#include <avr/io.h>
#include <avr/interrupt.h>
#define F_CPU 8000000UL
#include <util/delay.h>
#include <avr/pgmspace.h>
#include <stdio.h>
#include <stdarg.h>
#include <stdlib.h>

// Bit manipulation macros
#define sbi(a, b) ((a) |= 1 << (b))       //sets bit B in variable A
#define cbi(a, b) ((a) &= ~(1 << (b)))    //clears bit B in variable A
#define tbi(a, b) ((a) ^= 1 << (b))       //toggles bit B in variable A

#define BAUD 9600
#define UBBR (F_CPU / 16 / BAUD - 1)

void blink_led(void)
{
    for(;;)
    {
        _delay_ms(100); 
        cbi(PORTD, 7);
        _delay_ms(100); 
        sbi(PORTD, 7);
    }
}

void click_relay(void)
{
    for(;;)
    {
        _delay_ms(100); 
        cbi(PORTD, 3);
        _delay_ms(100); 
        sbi(PORTD, 3);
    }
}

void serial_init(void)
{
    /*Set baud rate */ 
    UBRR0H = (unsigned char)(UBBR>>8); 
    UBRR0L = (unsigned char)UBBR; 

    /* Enable transmitter */ 
    UCSR0B = (1<<TXEN0); 
    /* Set frame format: 8data, 1stop bit */ 
    UCSR0C = (0<<USBS0)|(3<<UCSZ00); 
}

void serial_tx(unsigned char ch)
{
    while ( !( UCSR0A & (1<<UDRE0)) )
        ;

    UDR0 = ch;
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

void setup(void)
{
    // Hall sensor pull up
//    PINB |= (1<<PB0);
    DDRB = 0;

    // Pins used for output
    // LED and Valve OUT
    DDRD |= (1<<PD3)|(1<<PD7);

    serial_init();
}

void polling_loop(void)
{
    for(;;)
    {
        if ((PINB & (1<<PINB0)) == 0)
        {
            sbi(PORTD, 7);
            _delay_ms(100); 
            cbi(PORTD, 7);
            _delay_ms(25); 
        }
    }
}

volatile unsigned long int count = 0;
volatile unsigned short win_count = 0;

void interrupt_loop(void)
{
    dprintf("total, since last\n");
    for(;;)
    {
        unsigned long int v = count;
        unsigned short int w = win_count;
        win_count = 0;
        dprintf("%d, %d\n", v, w);
        _delay_ms(250); 
        _delay_ms(250); 
    }
}

ISR(INT0_vect)
{
    cli();
    count++;
    win_count++;
    sei();
}

int main (void)
{
    setup();
    blink_led();
    dprintf("Welcome to Banana Jr. 2000\n");
    interrupt_loop();
    return 0;
}
