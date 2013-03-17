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

#include "defs.h"
#include "serial.h"
#include "packet.h"

#define MAX_DISPENSERS   15 
#define RESET_DURATION   10
#define PULSE_WIDTH      1

void    set_pin(uint8_t port, uint8_t pin);
void    clear_pin(uint8_t port, uint8_t pin);
uint8_t get_pin_state(uint8_t port, uint8_t pin);
void    flash_led(uint8_t fast);

/*  For use with the production board
    { 'D', 0 }, // 0 - pcint16
    { 'D', 3 }, // 1 - pcint19
    { 'D', 4 }, // 2 - pcint20
*/

// global variables that actually control states
volatile uint32_t        g_time = 0;
volatile uint8_t         g_sync = 0;

// reset related variables
static volatile uint32_t g_reset_fe_time = 0;
static volatile uint8_t  g_dispenser = 0;
static volatile uint8_t  g_reset = 0;

// dispenser select related stuff
volatile uint8_t         g_in_id_assignment;
static volatile uint8_t  g_dispenser_id[MAX_DISPENSERS];

void setup(void)
{
    // TX to RPI
    DDRB |= (1<< PORTB0);
    // RST is output
    DDRD |= (1<< PORTD2);
    // SYNC to dispensers
    DDRC |= (1<< PORTC3);
    // TX to dispensers
    DDRD |= (1<< PORTD1);

    // start by pulling D1 & B1 high, since serial lines when idle are high
    sbi(PORTD, 1);
    sbi(PORTB, 1);

    // PCINT setup
    PCMSK0 |= (1 << PCINT1);
    PCMSK2 |= (1 << PCINT16) | (1 << PCINT19) | (1 << PCINT20);
    PCICR |=  (1 << PCIE0) | (1 << PCIE2);

    // Timer setup for reset pulse width measuring
    TCCR1B |= TIMER1_FLAGS;
    TCNT1 = TIMER1_INIT;
    TIMSK1 |= (1<<TOIE1);

    // I2C setup
    TWAR = (1 << 3); // address
    TWDR = 0x0;  
    TWCR = (1<<TWEN) | (1<<TWIE) | (1<<TWEA);  

    // Turn sync off to start with
    g_sync = 0;

    sei();
}

static volatile uint8_t g_pcint1 = 0;
static volatile uint8_t g_pcint2 = 0;
static volatile uint8_t g_pcint3 = 0;
static volatile uint8_t g_pcint4 = 0;
static volatile uint8_t g_pcint5 = 0;
static volatile uint8_t g_pcint6 = 0;
static volatile uint8_t g_pcint7 = 0;

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
}

// variables related to PCINT2
static volatile uint8_t  pcint16 = 0;
static volatile uint8_t  pcint19 = 0;
static volatile uint8_t  pcint20 = 0;

ISR(PCINT2_vect)
{
    uint8_t state;

    switch(g_dispenser)
    {
        case 0:
            // Check for RX for Dispenser 0
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
        case 1:
            // Check for RX for Dispenser 1
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
        case 2:
            // Check for RX for Dispenser 2
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
    _delay_ms(RESET_DURATION);
    cbi(PORTD, 2);

    // Wait for dispensers to start up
    _delay_ms(1000);
    _delay_ms(1000);
}

// These functions are needed in the dispenser, but not the router.
// So we just have empty functions here
void idle()
{

}
uint8_t check_reset(void)
{
    return 0;
}

int main (void)
{
    uint8_t reset = 0, i;

    for(;;)
    {
        setup();
        for(i = 0; i < 5; i++)
        {
            sbi(PORTC, 3);
            _delay_ms(10);
            cbi(PORTC, 3);
            _delay_ms(10);
        }
        reset_dispensers();

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

