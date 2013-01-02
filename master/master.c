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
// THink about serial IO errors on this level.
// check for COLLISIONS in name assignment
// Ensure that I2C has error correction

typedef struct 
{
    uint8_t port, pin;
} dispenser_rx_defs_t;

typedef struct
{
    uint32_t fe_time;
    uint8_t  state;
} dispenser_state_t;

static dispenser_rx_defs_t g_dispenser_rx_defs[MAX_DISPENSERS] =
{
    // For use with the breadboard
    { 'D', 3 }, // 0
    { 'D', 4 }, // 1
    { 0, 0  }, // 2
    { 0, 0  }, // 3
    { 0, 0  }, // 4
    { 0, 0  }, // 5
    { 0, 0  }, // 6
    { 0, 0  }, // 7
    { 0, 0  }, // 8
    { 0, 0  }, // 9
    { 0, 0  }, // 10
    { 0, 0  }, // 11
    { 0, 0  }, // 12
    { 0, 0  }, // 13
    { 0, 0  }, // 14
/*  For use with the production board
    { 'D', 3 }, // 0
    { 'D', 5 }, // 1
    { 'D', 7  }, // 2
    { 'B', 3  }, // 3
    { 'B', 5  }, // 4
    { 'B', 7  }, // 5
    { 'C', 1  }, // 6
    { 'D', 0  }, // 7
    { 'D', 4  }, // 8
    { 'D', 6  }, // 9
    { 'B', 2  }, // 10
    { 'B', 4  }, // 11
    { 'B', 6  }, // 12
    { 'C', 0  }, // 13
    { 'C', 2  }, // 14
*/
};
static volatile uint8_t g_dispenser_id[MAX_DISPENSERS];
static volatile dispenser_state_t g_dispenser_state[MAX_DISPENSERS];

#define NUM_PCINT_2_DISPENSERS 2
static uint8_t g_pcint_2_dispenser_map[NUM_PCINT_2_DISPENSERS] = { 0, 1 };

volatile uint32_t g_time = 0;
static volatile uint32_t g_reset_fe_time = 0;
static volatile uint8_t  g_dispenser = 0;
static volatile uint8_t  g_reset = 0;
static volatile uint8_t  g_dispenser_count = 0;
volatile uint8_t         g_in_id_assignment;
volatile uint8_t         g_sync = 0;
volatile uint8_t         g_pcint0 = 0;

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

ISR(PCINT2_vect)
{
    uint8_t state, i, disp;

    for(i = 0; i < NUM_PCINT_2_DISPENSERS; i++)
    {
        disp = g_pcint_2_dispenser_map[i];
        state = get_pin_state(g_dispenser_rx_defs[disp].port, g_dispenser_rx_defs[disp].pin);
        if (state != g_dispenser_state[disp].state)
        {
            if (g_in_id_assignment)
            {
                if (state)
                    g_dispenser_state[disp].fe_time = g_time + RESET_DURATION;
                else
                {
                    if (g_dispenser_state[disp].fe_time > 0 && g_time >= g_dispenser_state[disp].fe_time)
                        g_dispenser_id[disp] = 1;
                    g_dispenser_state[disp].fe_time = 0;
                }
            }
            else
            if (g_dispenser == disp)
            {
                if (state)
                    sbi(PORTB, 1);
                else
                    cbi(PORTB, 1);
            }
            g_dispenser_state[disp].state = state;
        }
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

uint8_t get_pin_state(uint8_t port, uint8_t pin)
{
    switch(port)
    {
        case 'B':
            return PINB & (1 << pin) ? 1 : 0;
        case 'C':
            return PINC & (1 << pin) ? 1 : 0;
        case 'D': 
            return PIND & (1 << pin) ? 1 : 0;
    }
}

void set_pin(uint8_t port, uint8_t pin)
{
    switch(port)
    {
        case 'B':
            sbi(PORTB, pin);
            return;
        case 'C':
            sbi(PORTC, pin);
            return;
        case 'D': 
            sbi(PORTD, pin);
            return;
    }
}

void clear_pin(uint8_t port, uint8_t pin)
{
    switch(port)
    {
        case 'B':
            cbi(PORTB, pin);
            return;
        case 'C':
            cbi(PORTC, pin);
            return;
        case 'D': 
            cbi(PORTD, pin);
            return;
    }
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

