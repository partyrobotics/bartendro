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

// TODO: test collision support 

/*  For use with the production board
    { 'D', 3 }, // 0 - pcint19 -- works
    { 'D', 5 }, // 1 - pcint21 -- works
    { 'D', 7  }, // 2 - pcint23 -- works
    { 'B', 3  }, // 3 - pcint3 -- works
    { 'B', 5  }, // 4 - pcint5 -- works
    { 'B', 7  }, // 5 - pcint7 -- works
    { 'C', 1  }, // 6 - pcint9 -- works
    { 'D', 0  }, // 7 - pcint16 -- works
    { 'D', 4  }, // 8 - pcint20 -- works
    { 'D', 6  }, // 9 - pcint22 -- works
    { 'B', 2  }, // 10 - pcint2 -- works
    { 'B', 4  }, // 11 - pcint4 -- works
    { 'B', 6  }, // 12 - pcint6 -- works
    { 'C', 0  }, // 13 - pcint8 -- works
    { 'C', 2  }, // 14 - pcint10 -- works

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

void setup(void)
{
    // TX to RPI
    DDRB |= (1<< PORTB0);
    // TX to dispensers
    DDRD |= (1<< PORTD2);

    // SYNC to dispensers
    DDRC |= (1<< PORTC3);

    // PCINT setup
    PCMSK0 |= (1 << PCINT1) | (1 << PCINT2) | (1 << PCINT3) | (1 << PCINT4) | 
              (1 << PCINT5) | (1 << PCINT6) | (1 << PCINT7);
    PCMSK1 |= (1 << PCINT8) | (1 << PCINT9) | (1 << PCINT10);
    PCMSK2 |= (1 << PCINT16) | (1 << PCINT19) | (1 << PCINT20) | (1 << PCINT21) | 
              (1 << PCINT22) | (1 << PCINT23);
    PCICR |=  (1 << PCIE0) | (1 << PCIE1) | (1 << PCIE2);

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

static volatile uint8_t g_pcint1 = 0;
static volatile uint8_t g_pcint2 = 0;
static volatile uint8_t g_pcint3 = 0;
static volatile uint8_t g_pcint4 = 0;
static volatile uint8_t g_pcint5 = 0;
static volatile uint8_t g_pcint6 = 0;
static volatile uint8_t g_pcint7 = 0;
void id_assignment_isr_pcint0(void)
{
    uint8_t state;

    state = PINB & (1<<PINB2);
    if (state != g_pcint2)
    {
        id_assignment_fe(state, 10);
        g_pcint2 = state;
    }
    state = PINB & (1<<PINB3);
    if (state != g_pcint3)
    {
        id_assignment_fe(state, 3);
        g_pcint3 = state;
    }
    state = PINB & (1<<PINB4);
    if (state != g_pcint4)
    {
        id_assignment_fe(state, 11);
        g_pcint4 = state;
    }

    state = PINB & (1<<PINB5);
    if (state != g_pcint5)
    {
        id_assignment_fe(state, 4);
        g_pcint5 = state;
    }
    state = PINB & (1<<PINB6);
    if (state != g_pcint6)
    {
        id_assignment_fe(state, 12);
        g_pcint6 = state;
    }
    state = PINB & (1<<PINB7);
    if (state != g_pcint7)
    {
        id_assignment_fe(state, 5);
        g_pcint7 = state;
    }
}

ISR(PCINT0_vect)
{
    uint8_t      state;

    // Check for RX from the RPI
    state = PINB & (1<<PINB1);
    if (state != g_pcint1)
    {
        if (state)
            sbi(PORTD, 1);
        else
            cbi(PORTD, 1);
        g_pcint1 = state;
    }

    if (g_in_id_assignment)
    {
        id_assignment_isr_pcint0();
        return;
    }
    switch(g_dispenser)
    {
        case 3:
            // Check for RX for Dispenser 3
            state = PINB & (1<<PINB3);
            if (state != g_pcint3)
            {
                if (state)
                    sbi(PORTB, 0);
                else
                    cbi(PORTB, 0);
                g_pcint3 = state;
            }
            break;
        case 4:
            // Check for RX for Dispenser 4
            state = PINB & (1<<PINB5);
            if (state != g_pcint5)
            {
                if (state)
                    sbi(PORTB, 0);
                else
                    cbi(PORTB, 0);
                g_pcint5 = state;
            }
            break;
        case 5:
            // Check for RX for Dispenser 5
            state = PINB & (1<<PINB7);
            if (state != g_pcint5)
            {
                if (state)
                    sbi(PORTB, 0);
                else
                    cbi(PORTB, 0);
                g_pcint5 = state;
            }
            break;
        case 10:
            // Check for RX for Dispenser 10
            state = PINB & (1<<PINB2);
            if (state != g_pcint2)
            {
                if (state)
                    sbi(PORTB, 0);
                else
                    cbi(PORTB, 0);
                g_pcint2 = state;
            }
            break;
        case 11:
            // Check for RX for Dispenser 11
            state = PINB & (1<<PINB4);
            if (state != g_pcint4)
            {
                if (state)
                    sbi(PORTB, 0);
                else
                    cbi(PORTB, 0);
                g_pcint4 = state;
            }
            break;
        case 12:
            // Check for RX for Dispenser 12
            state = PINB & (1<<PINB6);
            if (state != g_pcint6)
            {
                if (state)
                    sbi(PORTB, 0);
                else
                    cbi(PORTB, 0);
                g_pcint6 = state;
            }
            break;
    }
}

static volatile uint8_t  g_pcint8 = 0;
static volatile uint8_t  g_pcint9 = 0;
static volatile uint8_t  g_pcint10 = 0;
void id_assignment_isr_pcint1(void)
{
    uint8_t state;

    state = PINC & (1<<PINC0);
    if (state != g_pcint8)
    {
        id_assignment_fe(state, 13);
        g_pcint8 = state;
    }
    state = PINC & (1<<PINC1);
    if (state != g_pcint9)
    {
        id_assignment_fe(state, 6);
        g_pcint9 = state;
    }
    state = PINC & (1<<PINC2);
    if (state != g_pcint10)
    {
        id_assignment_fe(state, 14);
        g_pcint10 = state;
    }
}

ISR(PCINT1_vect)
{
    uint8_t state;

    if (g_in_id_assignment)
    {
        id_assignment_isr_pcint1();
        return;
    }
    switch(g_dispenser)
    {
        case 6:
            // Check for RX for Dispenser 6
            state = PINC & (1<<PINC1);
            if (state != g_pcint9)
            {
                if (state)
                    sbi(PORTB, 0);
                else
                    cbi(PORTB, 0);
                g_pcint9 = state;
            }
            break;
        case 13:
            // Check for RX for Dispenser 13
            state = PINC & (1<<PINC0);
            if (state != g_pcint8)
            {
                if (state)
                    sbi(PORTB, 0);
                else
                    cbi(PORTB, 0);
                g_pcint8 = state;
            }
            break;
    }
}

// variables related to PCINT2
static volatile uint8_t  pcint16 = 0;
static volatile uint8_t  pcint19 = 0;
static volatile uint8_t  pcint20 = 0;
static volatile uint8_t  pcint21 = 0;
static volatile uint8_t  pcint22 = 0;
static volatile uint8_t  pcint23 = 0;

void id_assignment_isr_pcint2(void)
{
    uint8_t state;

    state = PIND & (1<<PIND0);
    if (state != pcint16)
    {
        id_assignment_fe(state, 7);
        pcint16 = state;
    }
    state = PIND & (1<<PIND3);
    if (state != pcint19)
    {
        id_assignment_fe(state, 0);
        pcint19 = state;
    }
    state = PIND & (1<<PIND5);
    if (state != pcint21)
    {
        id_assignment_fe(state, 1);
        pcint21 = state;
    }
    state = PIND & (1<<PIND7);
    if (state != pcint23)
    {
        id_assignment_fe(state, 2);
        pcint23 = state;
    }
    state = PIND & (1<<PIND4);
    if (state != pcint20)
    {
        id_assignment_fe(state, 8);
        pcint20 = state;
    }
    state = PIND & (1<<PIND6);
    if (state != pcint22)
    {
        id_assignment_fe(state, 9);
        pcint22 = state;
    }
}

ISR(PCINT2_vect)
{
    uint8_t state;

    if (g_in_id_assignment)
    {
        id_assignment_isr_pcint2();
        return;
    }
    switch(g_dispenser)
    {
        case 0:
            // Check for RX for Dispenser 0
            state = PIND & (1<<PIND3);
            if (state != pcint19)
            {
                if (state)
                    sbi(PORTB, 0);
                else
                    cbi(PORTB, 0);
                pcint19 = state;
            }
            break;
        case 1:
            // Check for RX for Dispenser 1
            state = PIND & (1<<PIND5);
            if (state != pcint21)
            {
                if (state)
                    sbi(PORTB, 0);
                else
                    cbi(PORTB, 0);
                pcint21 = state;
            }
            break;
        case 2:
            // Check for RX for Dispenser 2
            state = PIND & (1<<PIND7);
            if (state != pcint23)
            {
                if (state)
                    sbi(PORTB, 0);
                else
                    cbi(PORTB, 0);
                pcint23 = state;
            }
            break;
        case 7:
            // Check for RX for Dispenser 7
            state = PIND & (1<<PIND0);
            if (state != pcint16)
            {
                if (state)
                    sbi(PORTB, 0);
                else
                    cbi(PORTB, 0);
                pcint16 = state;
            }
            break;
        case 8:
            // Check for RX for Dispenser 8
            state = PIND & (1<<PIND4);
            if (state != pcint20)
            {
                if (state)
                    sbi(PORTB, 0);
                else
                    cbi(PORTB, 0);
                pcint20 = state;
            }
            break;
        case 9:
            // Check for RX for Dispenser 9
            state = PIND & (1<<PIND6);
            if (state != pcint22)
            {
                if (state)
                    sbi(PORTB, 0);
                else
                    cbi(PORTB, 0);
                pcint22 = state;
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

           if (data < MAX_DISPENSERS)
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

uint8_t setup_ids(void)
{
    uint8_t  i, j, state, count = 0, single_pass_count = 0;
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
            for(j = 0, single_pass_count = 0; j < MAX_DISPENSERS; j++)
            {
                cli();
                state = g_dispenser_id[j];
                sei();
                if (state)
                {
                    dispensers_found[j] = i;
                    count++;
                    single_pass_count++;
                }
            }
            // Did we get a collision??
            if (single_pass_count > 1)
                break;
        }
        // If we did get a collision, reset the dispensers and try the process again
        if (single_pass_count > 1)
        {
            reset_dispensers();
            continue;
        }
        if (count >= 0)
            break;

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

