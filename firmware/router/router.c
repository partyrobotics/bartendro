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

// reset related variables
static volatile uint8_t  g_dispenser = 0;
static volatile uint8_t  g_reset = 0;

// dispenser select related stuff
volatile uint8_t         g_in_id_assignment;
static volatile uint8_t  g_dispenser_id[MAX_DISPENSERS];

static const struct {
    volatile unsigned char *group;
    unsigned pin;
} dispenser[MAX_DISPENSERS] = {
    { &PIND, PIND3 }, // dispenser 0
    { &PIND, PIND5 }, // dispenser 1
    { &PIND, PIND7 }, // dispenser 2
    { &PINB, PINB3 }, // dispenser 3
    { &PINB, PINB5 }, // dispenser 4
    { &PINB, PINB7 }, // dispenser 5
    { &PINC, PINC1 }, // dispenser 6
    { &PIND, PIND0 }, // dispenser 7
    { &PIND, PIND4 }, // dispenser 8
    { &PIND, PIND6 }, // dispenser 9
    { &PINB, PINB2 }, // dispenser 10
    { &PINB, PINB4 }, // dispenser 11
    { &PINB, PINB6 }, // dispenser 12
    { &PINC, PINC0 }, // dispenser 13
    { &PINC, PINC2 }, // dispenser 14
};

void echo_dispenser(void)
{
    volatile unsigned char *group;
    uint8_t pin, state;

    // capture a local copy of g_dispenser to guarantee the next two lines use the same value
    // (interrupt could come between the two and change g_dispenser, I think? Depends on interrupt
    // rules. I don't *think* this is an issue, but it would be a rare enough failure case that
    // it would be near impossible to debug.)
    uint8_t disp = g_dispenser;

    group = dispenser[disp].group;
    pin = dispenser[disp].pin;

    state = *group & (1 << pin);

    if (state)
        sbi(PORTB, 0);
    else
        cbi(PORTB, 0);
}

void echo_rpi(void)
{
    uint8_t      state;

    // Check for RX from the RPI
    state = PINB & (1<<PINB1);

    if (state)
        sbi(PORTD, 1);
    else
        cbi(PORTD, 1);
}

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
    echo_rpi();
    echo_dispenser();
    
    // TODO: Check to see if we really want this statement. This enables
    // the pull up on B1, which we should not need.
    //sbi(PORTB, 1);

    // PCINT setup
    PCMSK0 |= (1 << PCINT1) | (1 << PCINT2) | (1 << PCINT3) | (1 << PCINT4) | 
              (1 << PCINT5) | (1 << PCINT6) | (1 << PCINT7);
    PCMSK1 |= (1 << PCINT8) | (1 << PCINT9) | (1 << PCINT10);
    PCMSK2 |= (1 << PCINT16) | (1 << PCINT19) | (1 << PCINT20) | (1 << PCINT21) | 
              (1 << PCINT22) | (1 << PCINT23);
    PCICR |=  (1 << PCIE0) | (1 << PCIE1) | (1 << PCIE2);

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

ISR(PCINT0_vect)
{
    echo_rpi();
    echo_dispenser();
}

ISR(PCINT1_vect)
{
    echo_dispenser();
}

ISR(PCINT2_vect)
{
    echo_dispenser();
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
   if (twi_status == TW_SR_DATA_ACK)     // 0x80: data received, ACK returned
   {
       data = TWDR;
       if (data == ROUTER_CMD_RESET)
           g_reset = 1;
       else
       if (data < MAX_DISPENSERS)
           g_dispenser = data;
       else
       if (data == ROUTER_CMD_SYNC_OFF)
           g_sync = 0;
       else
       if (data == ROUTER_CMD_SYNC_ON)
           g_sync = 1;
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
