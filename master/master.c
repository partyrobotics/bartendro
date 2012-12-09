#define F_CPU 16000000UL 
#include <avr/io.h>
#include <avr/interrupt.h>
#include <util/delay.h>

#include <stddef.h>
#include <math.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <avr/pgmspace.h>
#include <stdarg.h>
#include <stdlib.h>

// Bit manipulation macros
#define sbi(a, b) ((a) |= 1 << (b))       //sets bit B in variable A
#define cbi(a, b) ((a) &= ~(1 << (b)))    //clears bit B in variable A
#define tbi(a, b) ((a) ^= 1 << (b))       //toggles bit B in variable A

#define BAUD 38400
#define UBBR (F_CPU / 16 / BAUD - 1)
#define TIMER1_INIT 0xFFE6 // 16mhz / 64 cs / 25 = 100us per 'tick'
#define RESET_DURATION 1

void    set_pin(uint8_t port, uint8_t pin);
void    clear_pin(uint8_t port, uint8_t pin);
uint8_t get_port(uint8_t port);
uint8_t get_port_ddr(uint8_t port);
uint8_t get_pcmsk(uint8_t msk);

/*
   Master pin mappings:

   Inputs:

       PD0        -> rpi RESET
       PD1 (INT0) -> rpi TX
       PD2        -> rpi RX

       PE0        -> disp 0, TX
       PD3        -> disp 0, RX
       PD4        -> disp 0, RESET

       PE1        -> disp 1, TX
       PD5        -> disp 1, RX
       PD6        -> disp 1, RESET

       PE2        -> disp 2, TX
       PD7        -> disp 2, RX
       PG0        -> disp 2, RESET
       
       PE3        -> disp 3, TX
       PG1        -> disp 3, RX
       PC0        -> disp 3, RESET

       PE4        -> disp 4, TX
       PC1        -> disp 4, RX
       PC2        -> disp 4, RESET

       PE5        -> disp 5, TX
       PC3        -> disp 5, RX
       PC4        -> disp 5, RESET

       PE6        -> disp 6, TX
       PC5        -> disp 6, RX
       PC6        -> disp 6, RESET

       PE7        -> disp 7, TX
       PC7        -> disp 7, RX
       PG2        -> disp 7, RESET
       
       PB0        -> disp 8, TX
       PA7        -> disp 8, RX
       PA6        -> disp 8, RESET

       PB1        -> disp 9, TX
       PA5        -> disp 9, RX
       PA4        -> disp 9, RESET

       PB2        -> disp 10, TX
       PA3        -> disp 10, RX
       PA2        -> disp 10, RESET

       PB3        -> disp 11, TX
       PA1        -> disp 11, RX
       PA0        -> disp 11, RESET

       PB4        -> disp 12, TX
       PF7        -> disp 12, RX
       PF6        -> disp 12, RESET

       PB5        -> disp 13, TX
       PF5        -> disp 13, RX
       PF4        -> disp 13, RESET
       
       PB6        -> disp 14, TX
       PF3        -> disp 14, RX
       PF2        -> disp 14, RESET

       PB7        -> disp 15, TX
       PF1        -> disp 15, RX
       PF0        -> disp 15, RESET


       --------------------

   Test mappings:

   RPI:

       PD2 -> RESET input (INT0)
       PD3 -> MUX select (PCINT19)
       PD0 -> RX (PCINT16)
       PD1 -> TX

   Dispenser 0:

       PD6 -> RESET
       PD5 -> RX (PCINT21)
       PD4 -> TX

   Dispenser 1:

       PD6 -> RESET
       PB0 -> RX (PCINT0)
       PD7 -> TX

*/

typedef struct 
{
    uint8_t reset_port, reset_pin;
    uint8_t rx_port, rx_pin, rx_pcicr, rx_pcint, rx_pcmsk;
    uint8_t tx_port, tx_pin;
} dispenser_t;

#define NUM_DISPENSERS 2
static volatile dispenser_t dispensers[NUM_DISPENSERS] =
{  // reset_port, reset_pin, rx_port, rx_pin, rx_pcicr, rx_pcint, rx_pcmsk, tx_port, tx_pin
    { 'D',        6,         'D',     5,      PCIE1,    PCINT13,  1,        'D',     4      },
    { 'D',        6,         'B',     0,      PCIE0,    PCINT0,   0,        'D',     7      },
};

static volatile uint32_t g_time = 0;
static volatile uint32_t g_reset_fe_time = 0;
static volatile uint8_t  g_dispenser = 0;
static volatile uint8_t  g_mux_pin_0 = 0;

// reset pin change
ISR(INT0_vect)
{
    if (PIND & (1<<PIND2))
    {
        g_reset_fe_time = g_time + RESET_DURATION;
    }
    else
    {
        if (g_reset_fe_time > 0 && g_time >= g_reset_fe_time)
        { // TODO: move this over to be table driven
             cbi(PORTD, 6);
             _delay_us(10);
             sbi(PORTD, 6);
        }

        g_reset_fe_time = 0;
    }
}

volatile uint8_t pcint0 = 0;

ISR(PCINT0_vect)
{
    uint8_t      state;

    // Check for RX for Dispenser 1
    state = PINB & (1<<PINB0);
    if (state != pcint0)
    {
        if (g_dispenser == 1)
        {
            if (state)
                sbi(PORTD, 1);
            else
                cbi(PORTD, 1);
        }
        pcint0 = state;
    }
}

// unused right now
ISR(PCINT1_vect)
{
}

volatile uint8_t pcint16 = 0;
volatile uint8_t pcint19 = 0;
volatile uint8_t pcint21 = 0;
ISR(PCINT2_vect)
{
    uint8_t      state;

    // Check for RX from the RPI
    state = PIND & (1<<PIND0);
    if (state != pcint16)
    {
        // TODO: Fix this!
        if (state)
        {
            if (g_dispenser == 0)
                sbi(PORTD, 4);
            else
                sbi(PORTD, 7);
        }
        else
        {
            if (g_dispenser == 0)
                cbi(PORTD, 4);
            else
                cbi(PORTD, 7);
        }

        pcint16 = state;
    }

    // Check for RX for Dispenser 0
    state = PIND & (1<<PIND5);
    if (state != pcint21)
    {
        if (g_dispenser == 0)
        {
            if (state)
                sbi(PORTD, 1);
            else
                cbi(PORTD, 1);
        }
        pcint21 = state;
    }

    // Check for MUX select from the RPI
    state = PIND & (1<<PIND3);
    if (state != pcint19)
    {
        if (state)
            sbi(PORTB, 5);
        else
            cbi(PORTB, 5);
        g_dispenser = state;
        pcint19 = state;
    }
}

ISR (TIMER1_OVF_vect)
{
    g_time++;
    TCNT1 = TIMER1_INIT;
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

uint8_t get_port(uint8_t port)
{
    switch(port)
    {
        case 1:
            return PORTB;
        case 2:
            return PORTC;
        case 3: 
            return PORTD;
        default:
            return 0xFF;
    }
}

uint8_t get_port_ddr(uint8_t port)
{
    switch(port)
    {
        case 1:
            return DDRB;
        case 2:
            return DDRC;
        case 3: 
            return DDRD;
        default:
            return 0xFF;
    }
}

uint8_t get_pcmsk(uint8_t msk)
{
    switch(msk)
    {
        case 0:
            return PCMSK0;
        case 1:
            return PCMSK1;
        case 2: 
            return PCMSK2;
        default:
            return 0xFF;
    }
}

void setup_ports(void)
{
    uint8_t i, ddr, port, msk;

    for(i = 0; i < NUM_DISPENSERS; i++)
    {
        port = get_port(dispensers[i].reset_port);
        ddr = get_port_ddr(dispensers[i].reset_port);
        dispensers[i].reset_port = port;
        ddr |= (1 << dispensers[i].reset_pin);

        dispensers[i].rx_port = get_port(dispensers[i].rx_port);
        PCICR |= (1 << dispensers[i].rx_pcicr);
        msk = get_pcmsk(dispensers[i].rx_pcmsk);
        msk |= (1 << dispensers[1].rx_pcint);

        port = get_port(dispensers[i].tx_port);
        ddr = get_port_ddr(dispensers[i].tx_port);
        dispensers[i].tx_port = port;
        ddr |= (1 << dispensers[i].tx_pin);
    }
}

void setup(void)
{
    setup_ports();

    // on board LED
    DDRB |= (1<< PORTB5);

    // TX to RPI
    DDRD |= (1<< PORTD1);
    // TX to dispenser 0
    DDRD |= (1<< PORTD4);
    // TX to dispenser 1
    DDRD |= (1<< PORTD7);
    // RESET
    DDRD |= (1<< PORTD6);

    // INT0 for RPI reset
    EICRA |= (1 << ISC00);
    EIMSK |= (1 << INT0);

    // PCINT setup
    PCMSK0 |= (1 << PCINT0);
//    PCMSK1 |= (1 << PCINT13);
    PCMSK2 |= (1 << PCINT19) | (1 << PCINT16) | (1 << PCINT21);
    PCICR |= (1 << PCIE0) | (1 << PCIE1) | (1 << PCIE2);

    // Timer setup for reset pulse width measuring
    TCCR1B |= _BV(CS11)|(1<<CS10); // clock / 64 / 25 = .0001 per tick
    TCNT1 = TIMER1_INIT;
    TIMSK1 |= (1<<TOIE1);
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

int main (void)
{
    setup();

    // Set RESET to high, to enable the dispensers to run
    sbi(PORTD, 6);
    flash_led(1);

    sei();
    for(;;)
        ;

    return 0;
}
