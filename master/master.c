#include <avr/io.h>
#include <avr/interrupt.h>
#include <util/twi.h>
#include <util/delay.h>
#include <util/crc16.h>

#include <stddef.h>
#include <math.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <avr/pgmspace.h>
#include <stdarg.h>
#include <stdlib.h>

#include "../dispenser/defs.h"
#include "../dispenser/serial.h"
#include "../dispenser/packet.h"

#if F_CPU == 16000000UL
#define    TIMER1_INIT      0xFFEF
#define    TIMER1_FLAGS     _BV(CS12)|(1<<CS10); // 16Mhz / 1024 / 16 = .001024 per tick
#else
#define    TIMER1_INIT      0xFFF7
#define    TIMER1_FLAGS     _BV(CS12)|(1<<CS10); // 8Mhz / 1024 / 8 = .001024 per tick
#endif

#define MAX_DISPENSERS   15 
#define RESET_DURATION   1

void    set_pin(uint8_t port, uint8_t pin);
void    clear_pin(uint8_t port, uint8_t pin);
uint8_t get_pin_state(uint8_t port, uint8_t pin);

// TODO:
// check for COLLISIONS in name assignment

/*  For use with the production board
    { 'D', 3 }, // 0 - pcint19
    { 'D', 5 }, // 1 - pcint21
    { 'D', 7  }, // 2 - pcint23
    { 'B', 3  }, // 3 - pcint3
    { 'B', 5  }, // 4 - pcint5
    { 'B', 7  }, // 5 - pcint7
    { 'C', 1  }, // 6 - pcint9
    { 'D', 0  }, // 7 - pcint16
    { 'D', 4  }, // 8 - pcint20
    { 'D', 6  }, // 9 - pcint22
    { 'B', 2  }, // 10 - pcint2
    { 'B', 4  }, // 11 - pcint4
    { 'B', 6  }, // 12 - pcint6
    { 'C', 0  }, // 13 - pcint8
    { 'C', 2  }, // 14 - pcint10

 Sorted by pcints
    { 'B', 2  }, // 10 - pcint2
    { 'B', 3  }, // 3 - pcint3
    { 'B', 4  }, // 11 - pcint4
    { 'B', 5  }, // 4 - pcint5
    { 'B', 6  }, // 12 - pcint6
    { 'B', 7  }, // 5 - pcint7

    { 'C', 0  }, // 13 - pcint8
    { 'C', 1  }, // 6 - pcint9
    { 'C', 2  }, // 14 - pcint10

    { 'D', 0  }, // 7 - pcint16
    { 'D', 3 }, // 0 - pcint19
    { 'D', 4  }, // 8 - pcint20
    { 'D', 5 }, // 1 - pcint21
    { 'D', 6  }, // 9 - pcint22
    { 'D', 7  }, // 2 - pcint23
*/

// global variables that actually control states
volatile uint32_t        g_time = 0;
volatile uint8_t         g_sync = 0;

// reset related variables
static volatile uint32_t g_reset_fe_time = 0;
static volatile uint8_t  g_dispenser = 0;
static volatile uint8_t  g_reset = 0;

// dispenser select related stuff
static volatile uint8_t  g_dispenser_count = 0;
volatile uint8_t         g_in_id_assignment;
static volatile uint8_t  g_dispenser_id[MAX_DISPENSERS];

/*

   Test mappings:

   RPI:

       PD0 -> RESET input
       PB0 -> RX (pcint0)
       PB1 -> TX
       A4  -> SDA red wire
       A5  -> SCL green wire

   Dispenser 0:

       PD2 -> RESET
       PD1 -> TX
       PD3 -> RX (pcint19)
       PC3 -> SYNC

   Dispenser 1:

       PD2 -> RESET
       PD1 -> TX
       PD4 -> RX (pcint20)
       PC3 -> SYNC

*/

void setup(void)
{
    // on board LED
    DDRB |= (1<< PORTB5);

    // TX to RPI
    DDRB |= (1<< PORTB1);
    // TX to dispensers
    DDRD |= (1<< PORTD2);

    // SYNC to dispensers
    DDRC |= (1<< PORTC3);

    // PCINT setup
    PCMSK0 |= (1 << PCINT0);
    PCMSK2 |= (1 << PCINT19) | (1 << PCINT20) ;
    PCICR |=  (1 << PCIE0) | (1 << PCIE2);

    // Timer setup for reset pulse width measuring
    TCCR1B |= TIMER1_FLAGS;
    TCNT1 = TIMER1_INIT;
    TIMSK1 |= (1<<TOIE1);

    // I2C setup
    TWAR = (1 << 3); // address
    TWDR = 0x0;  
    TWCR = (1<<TWEN) | (1<<TWIE) | (1<<TWEA);  

    sei();
}

static volatile uint8_t g_pcint0 = 0;
ISR(PCINT0_vect)
{
    uint8_t      state;

    // Check for RX from the RPI
    state = PINB & (1<<PINB0);
    if (state != g_pcint0)
    {
        if (state)
            sbi(PORTD, 1);
        else
            cbi(PORTD, 1);
        g_pcint0 = state;
    }
}

// variables related to PCINT2
static volatile uint8_t  pcint19 = 0;
static volatile uint8_t  pcint20 = 0;
static volatile uint32_t g_rx_pcint_fe_time[MAX_DISPENSERS];

void id_assignment_fe(uint8_t state, uint8_t disp)
{
    if (state)
        g_rx_pcint_fe_time[disp] = g_time + RESET_DURATION;
    else
    {
        if (g_rx_pcint_fe_time[disp] > 0 && g_time >= g_rx_pcint_fe_time[disp])
            g_dispenser_id[disp] = 1;
        g_rx_pcint_fe_time[disp] = 0;
    }
}

void id_assignment_isr_pcint0(void)
{
    uint8_t state;

    state = PIND & (1<<PIND3);
    if (state != pcint19)
    {
        id_assignment_fe(state, 0);
        pcint19 = state;
    }
    state = PIND & (1<<PIND4);
    if (state != pcint20)
    {
        id_assignment_fe(state, 1);
        pcint20 = state;
    }
}

ISR(PCINT2_vect)
{
    uint8_t state;

    if (g_in_id_assignment)
    {
        id_assignment_isr_pcint0();
        return;
    }
    switch(g_dispenser)
    {
        case 0:
            // Check for RX for Dispenser 0
            state = PIND & (1<<PIND3);
            if (state != pcint19)
            {
                if (g_dispenser == 0)
                {
                    if (state)
                        sbi(PORTB, 1);
                    else
                        cbi(PORTB, 1);
                }
                pcint19 = state;
            }
            break;
        case 1:
            // Check for RX for Dispenser 1
            state = PIND & (1<<PIND4);
            if (state != pcint20)
            {
                if (g_dispenser == 1)
                {
                    if (state)
                        sbi(PORTB, 1);
                    else
                        cbi(PORTB, 1);
                }
                pcint20 = state;
            }
            break;
    }
}

ISR (TIMER1_OVF_vect)
{
    g_time++;
    if (g_sync)
        tbi(PORTC, 3);
    TCNT1 = TIMER1_INIT;
}

ISR(TWI_vect)
{
   uint8_t twi_status, data;

   // Get TWI Status Register, mask the prescaler bits (TWPS1,TWPS0)
   twi_status=TWSR & 0xF8;     
   switch(twi_status) 
   {
       case TW_SR_DATA_ACK:     // 0x80: data received, ACK returned
           data = TWDR;
           if (data == ROUTER_CMD_RESET)
           {
               g_reset = 1;
               break;
           }

           if (data < g_dispenser_count)
           {
               g_dispenser = data;
               break;
           }
           if (data == ROUTER_CMD_SYNC_OFF)
           {
               g_sync = 0;
               break;
           }
           if (data == ROUTER_CMD_SYNC_ON)
           {
               g_sync = 1;
               break;
           }
           break;
   }
   TWCR |= (1<<TWINT);    // Clear TWINT Flag
}

void reset_dispensers(void)
{
    // Reset the dispensers
    sbi(PORTD, 2);
    _delay_ms(RESET_DURATION + RESET_DURATION);
    cbi(PORTD, 2);

    // Wait for dispensers to start up
    _delay_ms(500);
    _delay_ms(500);
}

void flash_led(uint8_t fast)
{
    int i;

    for(i = 0; i < 5; i++)
    {
        sbi(PORTB, 5);
        if (fast)
            _delay_ms(50);
        else
            _delay_ms(250);
        cbi(PORTB, 5);
        if (fast)
            _delay_ms(50);
        else
            _delay_ms(250);
    }
}

// TODO: handle collisions and missing dispensers
uint8_t setup_ids(void)
{
    uint8_t  i, j, state, count = 0;
    uint8_t  dispensers_found[MAX_DISPENSERS];

    serial_init();
    serial_enable(0, 1);

    cli();
    g_in_id_assignment = 1;
    sei();

    memset(dispensers_found, 0xFF, sizeof(dispensers_found));
    for(;;)
    {
        count = 0;
        for(i = 0; i < 255; i++)
        {
            cli();
            memset((void *)g_dispenser_id, 0, sizeof(g_dispenser_id));
            sei();

            serial_tx(i);
            _delay_ms(3);
            for(j = 0; j < MAX_DISPENSERS; j++)
            {
                cli();
                state = g_dispenser_id[j];
                sei();
                if (state)
                {
                    dispensers_found[j] = i;
                    count++;
                }
            }
        }
#if 0
        flash_led(count == 2); //MAX_DISPENSERS);
        for(i = 0; i < min(count, 10); i++)
        {
            sbi(PORTB, 2);
            _delay_ms(200);
            cbi(PORTB, 2);
            _delay_ms(200);
        }
#endif
        if (count >= 0)
            break;

        // Found no dispensers!
        flash_led(0);
        flash_led(0);
        reset_dispensers();
    }
    _delay_ms(5);
    serial_tx(255);
    _delay_ms(5);

    for(i = 0; i < MAX_DISPENSERS; i++)
    {
        if (dispensers_found[i] != 255)
        {
            serial_tx(dispensers_found[i]);
            serial_tx(i);
        }
    }

    _delay_ms(5);
    serial_tx(255);
    _delay_ms(5);

    // Disable serial IO and put D2 back to output
    serial_enable(0, 0);
    DDRD |= (1<< PORTD2) | (1<< PORTD1);

    // start by pulling D1 & B1 high, since serial lines when idle are high
    sbi(PORTD, 1);
    sbi(PORTB, 1);

    cli();
    g_in_id_assignment = 0;
    sei();

    return count;
}

int main (void)
{
    uint8_t reset = 0, count;

    for(;;)
    {
        DDRB |= (1 << PORTB5) | (1 << PORTB2);
        DDRD |= (1 << PORTD2);
        flash_led(1);
        g_sync = 0;

        reset_dispensers();
        setup();
        count = setup_ids();
        cli();
        g_dispenser_count = count;
        g_sync = 0;
        sei();
        for(;;)
        {
            cli();
            reset = g_reset;
            sei();

            if (reset)
            {
                cli();
                g_reset = 0;
                sei();
                break; 
            }
            _delay_ms(1);
        }
    }
    return 0;
}

