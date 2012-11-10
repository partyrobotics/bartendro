#include <avr/io.h>
#include <avr/interrupt.h>
#include <util/delay.h>
#include <math.h>

#include <stddef.h>
#include <math.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <avr/pgmspace.h>
#include <stdarg.h>
#include <stdlib.h>

#include "hue.h"

// Bit manipulation macros
#define sbi(a, b) ((a) |= 1 << (b))       //sets bit B in variable A
#define cbi(a, b) ((a) &= ~(1 << (b)))    //clears bit B in variable A
#define tbi(a, b) ((a) ^= 1 << (b))       //toggles bit B in variable A

#define BAUD 38400
#define UBBR (F_CPU / 16 / BAUD - 1)
#define DEBUG 0

#define NUM_LED 4
#define NUM_DATA (NUM_LED * 3)

#define COLOR_LATCH_DURATION 501
#define CLOCK_PERIOD 10
#define CLOCK_PIN 0
#define DATA_PIN 1
#define CLOCK_PORT PORTC
#define DATA_PORT PORTC

// Time keeping
static volatile uint32_t g_time = 0;

// what light pattern should we show now?
static volatile uint8_t g_received = 0;

// some prototypes
uint8_t should_break(void);

void serial_init(void)
{
    /*Set baud rate */ 
    UBRR0H = (unsigned char)(UBBR>>8); 
    UBRR0L = (unsigned char)UBBR; 
    /* Enable transmitter */ 
    UCSR0B = (1<<TXEN0) | (1<<RXEN0) | (1<<RXCIE0);
    /* Set frame format: 8data, 1stop bit */ 
    UCSR0C = (0<<USBS0)|(3<<UCSZ00); 
}

ISR(USART_RX_vect) 
{ 
    g_received = UDR0;
}

void serial_tx(uint8_t ch)
{
    while ( !( UCSR0A & (1<<UDRE0)) )
        ;
    UDR0 = ch;
}

#define MAX 80 

// debugging printf function. Max MAX characters per line!!
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

void delay_ms(int ms) 
{ 
    int i;
    for (i = 0; i < ms; i++) 
        _delay_ms(1); 
}

void delay_us(int us) 
{ 
    int i;
    for (i = 0; i < us; i++) 
        _delay_us(1); 
}

void ledstick_setup(void)
{
    // setting clock and data ports
    DDRC |= (1<<PC0)|(1<<PC1);

    // Set PWM pins as outputs
    DDRD |= (1<<PD6)|(1<<PD5)|(1<<PD3);

    // on board LED
    DDRB |= (1<<PB5);

    // diagnostic LED on pins 7, 8, 9
    DDRD |= (1<<PD7); // red
    DDRB |= (1<<PB0); // green
    DDRB |= (1<<PB1); // blue

    serial_init();

    /* Set to Fast PWM */
    TCCR0A |= _BV(WGM01) | _BV(WGM00);
    TCCR2A |= _BV(WGM21) | _BV(WGM20);

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
    TCCR0B |= _BV(CS00);
    TCCR2B |= _BV(CS20);
}

void set_dia_led(uint8_t red, uint8_t green, uint8_t blue)
{
    if (red)
        sbi(PORTD, 7);
    else
        cbi(PORTD, 7);

    if (green)
        sbi(PORTB, 0);
    else
        cbi(PORTB, 0);

    if (blue)
        sbi(PORTB, 1);
    else
        cbi(PORTB, 1);
}

void set_pwm_colors(uint8_t *c)
{
    OCR2B = c[0];
    OCR0A = c[1];
    OCR0B = c[2];
}

void set_led_colors(uint8_t *leds)
{
    uint8_t i, l, c, byte;

    for(l = 0; l < NUM_LED; l++)
        for(c = 0; c < 3; c++)
            {
                byte = leds[(l * 3) + c];
                for(i = 0; i < 8; i++)
                {
                    if (byte & (1 << (8 - i)))
                        sbi(DATA_PORT, DATA_PIN);
                    else
                        cbi(DATA_PORT, DATA_PIN);
                    delay_us(CLOCK_PERIOD);

                    sbi(CLOCK_PORT, CLOCK_PIN);
                    delay_us(CLOCK_PERIOD);

                    cbi(CLOCK_PORT, CLOCK_PIN);
                }
            }
     delay_us(COLOR_LATCH_DURATION);
     set_pwm_colors((uint8_t *)leds);
}

void startup(void)
{
    int i;

    unsigned char leds[NUM_LED * 3] = { 0xff, 0xff, 0x00, 
                                        0xff, 0x00, 0xff,
                                        0xff, 0xff, 0x00,
                                        0xff, 0x00, 0xff };
    unsigned char leds2[NUM_LED * 3] = { 0xff, 0x00, 0xff, 
                                         0xff, 0xff, 0x00,
                                         0xff, 0x00, 0xff,
                                         0xff, 0xff, 0x00 };

    for(i = 0; i < 3; i++)
    {
        set_led_colors(leds);
        delay_ms(100);

        set_led_colors(leds2);
        delay_ms(100);
    }
}

void rainbow(void)
{
    uint8_t i, j;
    color_t led;
    uint8_t leds[NUM_LED * 3];
 
    for(; !should_break();)
        for(i = 0; i < HUE_MAX && !should_break(); i++)
        {
            for(j = 0; j < NUM_LED; j++)
            {
                color_hue((i + j) % HUE_MAX, &led);
                leds[(j * 3)] = led.red;
                leds[(j * 3) + 1] = led.green;
                leds[(j * 3) + 2] = led.blue;
            }
            set_led_colors(leds);
            delay_ms(30);
        }
}

void panic(uint8_t t, color_t *c)
{
    c->red =  (int)((sin((float)t / M_PI_2) + 1.0) * 127);
    c->blue = c->green = 0;
}

void drink_done(uint8_t t, color_t *c)
{
    c->green =  (int)((sin((float)t / M_PI_2) + 1.0) * 127);
    c->blue = c->red = 0;
}

void drink_pouring(uint8_t t, color_t *c)
{
    c->red =  (int)((sin((float)t / M_PI_2) + 1.0) * 127);
    c->green = 0;
    c->blue =  (int)((cos((float)t / M_PI_2) + 1.0) * 127);
}

void plot_function(uint8_t delay, void (*func)(uint8_t, color_t *))
{
    uint8_t i, j;
    uint8_t leds[NUM_LED * 3];
    color_t c;
 
    for(i = 0; !should_break(); i++)
    {
        func(i, &c);
        for(j = 0; j < NUM_LED; j++)
        {
            leds[(j * 3)] = c.red;
            leds[(j * 3) + 1] = c.green;
            leds[(j * 3) + 2] = c.blue;
        }
        set_led_colors(leds);
        delay_ms(delay);
    }
}

uint8_t should_break(void)
{
    uint8_t r;

    cli();
    r = g_received;
    sei();

    return r;
}

int main(void)
{
    uint8_t ch, last_ch = 'i', next;

    ledstick_setup();
    dprintf("bartendro led driver starting\n");
    sei();
    startup();
    for(;;)
    {
        ch = should_break();
        if (ch)
        {
            cli();
            g_received = 0;
            sei();
        }
        switch(ch)
        {
            // diagnostic LED control
            case 'w':
                dprintf("warning, some booze is low!");
                set_dia_led(0, 0, 1);
                next = last_ch;
                break;

            case 'o':
                dprintf("trouble, some booze is OUT!");
                set_dia_led(1, 0, 0);
                next = last_ch;
                break;

            case 'g':
                dprintf("all good!");
                set_dia_led(0, 1, 0);
                next = last_ch;
                break;

            default:
                next = ch;
                break;
        }

        switch(next)
        {
            // main LED control
            case 'd':
                dprintf("Drink done\n");
                plot_function(20, &drink_done);
                break;

            case 'p':
                dprintf("Pour drink\n");
                plot_function(25, &drink_pouring);
                break;

            case 'e':
                dprintf("Panic!\n");
                plot_function(20, &panic);
                break;

            case 'i':
            default:
                dprintf("idle\n");
                rainbow();
                break;
        }
    }
}
