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

static volatile uint32_t g_time = 0;
static volatile uint32_t g_falling_edge_time = 0;

ISR(INT0_vect)
{
    if (PIND & (1<<PIND2))
    {
        sbi(PORTB, 5);
        g_falling_edge_time = g_time + RESET_DURATION;
    }
    else
    {
        cbi(PORTB, 5);
        if (g_falling_edge_time > 0 && g_time >= g_falling_edge_time)
        {
             cbi(PORTD, 6);
             _delay_us(10);
             sbi(PORTD, 6);
        }

        g_falling_edge_time = 0;
    }
}

ISR (TIMER1_OVF_vect)
{
    g_time++;
    TCNT1 = TIMER1_INIT;
}

void serial_init(void)
{
    /*Set baud rate */ 
    UBRR0H = (unsigned char)(UBBR>>8); 
    UBRR0L = (unsigned char)UBBR; 
    /* Enable transmitter */ 
    UCSR0B = (1<<TXEN0)|(1<<RXEN0); 
    /* Set frame format: 8data, 1stop bit */ 
    UCSR0C = (0<<USBS0)|(3<<UCSZ00); 
}

void serial_tx(uint8_t ch)
{
    while ( !( UCSR0A & (1<<UDRE0)) );
    UDR0 = ch;
}

uint8_t serial_rx(void)
{
    while ( !(UCSR0A & (1<<RXC0))) 
        ;

    return UDR0;
}

#define MAX 80 
void dprintf(const char *fmt, ...)
{
    va_list va;
    va_start (va, fmt);
    char buffer[MAX];
    char *ptr = buffer;
    vsnprintf(buffer, MAX, fmt, va);
    va_end (va);
    for(ptr = buffer; *ptr; ptr++)
    {
        if (*ptr == '\n') serial_tx('\r');
        serial_tx(*ptr);
    }
}

/*
   Master pin mappings:

   15 RX pins from dispenser
   1  RESET from RPI
   1  TX    from RPI
   =================
   17 total

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

       PD2 -> RESET input 
       PD3 -> MUX select
       PD4 -> RX 
       PD5 -> TX

   Dispenser 0:

       PD6 -> RESET
       PB1 -> RX (PCINT1)
       PB2 -> TX

   Dispenser 1:

       PD6 -> RESET
       PB3 -> RX (PCINT3)
       PB4 -> TX

*/

typedef struct 
{
    uint8_t reset_port, reset_pin;
    uint8_t rx_port, rx_pin, rx_pcicr, rx_pcint;
    uint8_t tx_port, tx_pin;
} dispenser_t;

#define NUM_DISPENSERS 2
static dispenser_t dispensers[NUM_DISPENSERS] =
{  // reset_port, reset_pin, rx_port, rx_pin, rx_pcirc, rx_pcint, tx_port, tx_pin
    { 3,          6,         1,       1,      PCIE0,    PCINT1,   1,       2      },
    { 3,          6,         1,       3,      PCIE0,    PCINT3,   1,       4      },
};

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

void setup_ports(void)
{
    uint8_t i, ddr, port;

    for(i = 0; i < NUM_DISPENSERS; i++)
    {
        port = get_port(dispensers[i].reset_port);
        ddr = get_port_ddr(dispensers[i].reset_port);
        dispensers[i].reset_port = port;
        ddr |= (1 << dispensers[i].reset_pin);

        dispensers[i].rx_port = get_port(dispensers[i].rx_port);
        dispensers[i].rx_pcicr |= (1 << dispensers[1].rx_pcint);

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

    // TX to rpi
    DDRD |= (1<< PORTD5);

    // INT0 for RPI RX
    EICRA |= (1 << ISC00);
    EIMSK |= (1<< INT0);

    // Timer setup for reset pulse width measuring
    TCCR1B |= _BV(CS11)|(1<<CS10); // clock / 64 / 25 = .0001 per tick
    TCNT1 = TIMER1_INIT;
    TIMSK1 |= (1<<TOIE1);

    serial_init();
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


    sbi(PORTB, 6);
    flash_led(1);

    sei();
    for(;;)
        ;

    return 0;
}
