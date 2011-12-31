#define PRO_MINI_5V
#ifdef PRO_MINI_5V
   #define F_CPU 16000000UL 
#else 
   #define F_CPU  8000000UL 
#endif

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

#include "../master/packet.h"

// Bit manipulation macros
#define sbi(a, b) ((a) |= 1 << (b))       //sets bit B in variable A
#define cbi(a, b) ((a) &= ~(1 << (b)))    //clears bit B in variable A
#define tbi(a, b) ((a) ^= 1 << (b))       //toggles bit B in variable A

#define BAUD 38400
#define UBBR (F_CPU / 16 / BAUD - 1)

#ifdef PRO_MINI_5V
#define TIMER1_INIT 0xFF06 // 16mhz / 64 cs / 250 = 1ms per 'tick'
#else 
#define TIMER1_INIT 0xFF06 // 8mhz / 8 cs / 1000 = 1ms per 'tick'
#endif

#define DEBUG 0

volatile uint8_t g_motor_state = 0;

ISR(PCINT1_vect)
{
    if (PINC & (1<<PINC3))
    {
        cbi(PORTB, 1);
        g_motor_state = 0;
    }
    else 
    {
        sbi(PORTB, 1);
        g_motor_state = 1;
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
    while ( !( UCSR0A & (1<<UDRE0)) );
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
    // Set LED PWM pins as outputs
    DDRD |= (1<<PD6)|(1<<PD5)|(1<<PD3)|(1<<PD4)|(1<<PD7);

    // Set Motor pin as output
    DDRB |= (1<<PB1) | (1<<PB0);

    // Enable the pull up on the input pin
    sbi(PORTC, 3);

    // Motor driver pins
    // pin 4 high = /STANDBY
    // pin 7 high = IN1
    // pin 8 low = IN2
    sbi(PORTD, 4);
    sbi(PORTD, 7);
    cbi(PORTB, 0);

    // External interrupts for motor line
    PCMSK1 |= (1<<PCINT11);
    PCICR |= (1<<PCIE1);

#if DEBUG
    serial_init();
#endif
}

void led_pwm_setup(void)
{
	/* Set to Phase correct PWM */
	TCCR0A |= _BV(WGM00);
	TCCR2A |= _BV(WGM20);

	// Set the compare output mode
	TCCR0A |= _BV(COM0A1);
	TCCR0A |= _BV(COM0B1);
	TCCR2A |= _BV(COM2B1);

	// Reset timers and comparators
	OCR0A = 0;
	OCR0B = 0;
	OCR2B = 0;
	TCNT0 = 0;
	TCNT2 = 0;

    // Set the clock source
	TCCR0B |= _BV(CS00) | _BV(CS01);
	TCCR2B |= _BV(CS22);
}

void set_led_color(uint8_t red, uint8_t green, uint8_t blue)
{
    OCR2B = 255 - red;
    OCR0A = 255 - blue;
    OCR0B = 255 - green;
}

void set_led_red(uint8_t v)
{
    OCR2B = 255 - v;
}

void set_led_green(uint8_t v)
{
    OCR0A = 255 - v;
}

void set_led_blue(uint8_t v)
{
    OCR0B = 255 - v;
}

int main(void)
{
    uint8_t state;

	setup();

    // turn the motor off, just in case
    cbi(PORTB, 1);

    led_pwm_setup();
    set_led_color(0, 0, 0);

#if DEBUG
    dprintf("slave starting\n");
#endif
    sei();

    for(;;)
    {
        cli();
        state = g_motor_state;
        sei();
#if DEBUG
        dprintf("%d\n", state);
#endif
        set_led_red(255);
        _delay_ms(250);
        set_led_red(0);
        _delay_ms(250);
    }
}

