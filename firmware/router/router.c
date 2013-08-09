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
*/

// global variables that actually control states
volatile uint8_t         g_sync = 0;
static volatile uint8_t  g_dispenser = 0;
static volatile uint8_t  g_reset = 0;

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

    // By default, select the first dispenser
    g_dispenser = 0;

    // Check the state of the lines that we are routing and repeat that on 
    // our output lines.
    if (PINB & (1<<PINB1))
        sbi(PORTD, 1);
    else
        cbi(PORTD, 1);

    if (PIND & (1<<PIND3))
        sbi(PORTB, 0);
    else
        cbi(PORTB, 0);
    
    // TODO: Check to see if we really want this statement. This enables
    // the pull up on B1, which we should not need.
    //sbi(PORTB, 1);

    // Timer setup for SYNC signal
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

ISR (TIMER1_OVF_vect)
{
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

void port_b_process_change(uint8_t port_b, uint8_t changed_pins)
{
    // Check for RX from the RPI
    if (changed_pins & (1 << PB1))
    {
        if (port_b & (1 << PB1))
            sbi(PORTD, 1);
        else
            cbi(PORTD, 1);
    }

    switch(g_dispenser)
    {
        case 3:
            // Check for RX for Dispenser 3
            if (changed_pins & (1 << PB3))
            {
                if (port_b & (1 << PB3))
                    sbi(PORTB, 0);
                else
                    cbi(PORTB, 0);
            }
            break;
        case 4:
            // Check for RX for Dispenser 4
            if (changed_pins & (1 << PB5))
            {
                if (port_b & (1 << PB5))
                    sbi(PORTB, 0);
                else
                    cbi(PORTB, 0);
            }
            break;
        case 5:
            // Check for RX for Dispenser 5
            if (changed_pins & (1 << PB5))
            {
                if (port_b & (1 << PB5))
                    sbi(PORTB, 0);
                else
                    cbi(PORTB, 0);
            }
            break;
        case 10:
            // Check for RX for Dispenser 10
            if (changed_pins & (1 << PB2))
            {
                if (port_b & (1 << PB2))
                    sbi(PORTB, 0);
                else
                    cbi(PORTB, 0);
            }
            break;
        case 11:
            // Check for RX for Dispenser 11
            if (changed_pins & (1 << PB4))
            {
                if (port_b & (1 << PB4))
                    sbi(PORTB, 0);
                else
                    cbi(PORTB, 0);
            }
            break;
        case 12:
            // Check for RX for Dispenser 12
            if (changed_pins & (1 << PB6))
            {
                if (port_b & (1 << PB6))
                    sbi(PORTB, 0);
                else
                    cbi(PORTB, 0);
            }
            break;
    }
}

void port_c_process_change(uint8_t port_c, uint8_t changed_pins)
{
    switch(g_dispenser)
    {
        case 6:
            // Check for RX for Dispenser 6
            if (changed_pins & (1 << PC1))
            {
                if (port_c & (1 << PC1))
                    sbi(PORTB, 0);
                else
                    cbi(PORTB, 0);
            }
            break;
        case 13:
            // Check for RX for Dispenser 13
            if (changed_pins & (1 << PC0))
            {
                if (port_c & (1 << PC0))
                    sbi(PORTB, 0);
                else
                    cbi(PORTB, 0);
            }
            break;
        case 14:
            // Check for RX for Dispenser 14
            if (changed_pins & (1 << PC2))
            {
                if (port_c & (1 << PC2))
                    sbi(PORTB, 0);
                else
                    cbi(PORTB, 0);
            }
            break;
    }
}

void port_d_process_change(uint8_t port_d, uint8_t changed_pins)
{
    switch(g_dispenser)
    {
        case 0:
            // Check for RX for Dispenser 0
            if (changed_pins & (1 << PD3))
            {
                if (port_d & (1 << PD3))
                    sbi(PORTB, 0);
                else
                    cbi(PORTB, 0);
            }
            break;
        case 1:
            // Check for RX for Dispenser 1
            if (changed_pins & (1 << PD5))
            {
                if (port_d & (1 << PD5))
                    sbi(PORTB, 0);
                else
                    cbi(PORTB, 0);
                pcint21 = state;
            }
            break;
        case 2:
            // Check for RX for Dispenser 2
            if (changed_pins & (1 << PD7))
            {
                if (port_d & (1 << PD7))
                    sbi(PORTB, 0);
                else
                    cbi(PORTB, 0);
            }
            break;
        case 7:
            // Check for RX for Dispenser 7
            if (changed_pins & (1 << PD0))
            {
                if (port_d & (1 << PD0))
                    sbi(PORTB, 0);
                else
                    cbi(PORTB, 0);
            }
            break;
        case 8:
            // Check for RX for Dispenser 8
            if (changed_pins & (1 << PD4))
            {
                if (port_d & (1 << PD4))
                    sbi(PORTB, 0);
                else
                    cbi(PORTB, 0);
            }
            break;
        case 9:
            // Check for RX for Dispenser 9
            if (changed_pins & (1 << PD6))
            {
                if (port_d & (1 << PD6))
                    sbi(PORTB, 0);
                else
                    cbi(PORTB, 0);
            }
            break;
    }
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

int main (void)
{
    uint8_t reset = 0, i;
    uint8_t port_b, port_c, port_d;
    uint8_t port_b_last = 0xFF, port_c_last = 0xFF, port_d_last = 0xFF;

    for(;;)
    {
        setup();
        reset_dispensers();

        for(;;)
        {
            // Check for a reset signal
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

            // check for a change on PORT B
            port_b = PINB;
            if (port_b != port_b_last)
            {
                port_b_process_change(port_b, port_b ^ port_b_last);
                port_b_last = port_b;
            }

            // check for a change on PORT C
            port_c = PINC;
            if (port_c != port_c_last)
            {
                port_c_process_change(port_c, port_c ^ port_c_last);
                port_c_last = port_c;
            }

            // check for a change on PORT D
            port_d = PIND;
            if (port_d != port_d_last)
            {
                port_d_process_change(port_d, port_d ^ port_d_last);
                port_d_last = port_d;
            }
        }
    }
    return 0;
}

