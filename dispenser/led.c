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

#include "defs.h"

#define NUM_LED 1
#define NUM_DATA (NUM_LED * 3)

#define COLOR_LATCH_DURATION 501 
#define CLOCK_PERIOD         1
#define CLOCK_PIN            3
#define DATA_PIN             4
#define CLOCK_PORT           PORTD
#define DATA_PORT            PORTD

typedef struct
{
        uint8_t red, green, blue;
} color_t;

// some delay helper functions
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

// Set the leds to a given color, using 3 uint8_t characters
void set_led_bytes(uint8_t *leds)
{
    uint8_t i, c, byte;

    for(c = 0; c < 3; c++)
    {
        byte = leds[c];
        for(i = 0; i < 8; i++)
        {
            if (byte & (1 << (8 - i)))
                sbi(DATA_PORT, DATA_PIN);
            else
                cbi(DATA_PORT, DATA_PIN);
            _delay_us(1);

            sbi(CLOCK_PORT, CLOCK_PIN);
            _delay_us(1);

            cbi(CLOCK_PORT, CLOCK_PIN);
        }
    }
}

// helper function to set the led color by passing in a color_t struct
void set_led_color(color_t *color)
{
    set_led_bytes((uint8_t*)color);
}

// This function is for setting the LED to one solid color. 
// This function should not be used for color animations since it
// includes the 500us rest period for the WS2801 to latch the results.
void set_led_rgb(uint8_t red, uint8_t green, uint8_t blue)
{
    uint8_t led[3];
    led[0] = red;
    led[1] = green;
    led[2] = blue;
    set_led_bytes(led);
    delay_us(COLOR_LATCH_DURATION);
}

// Same as the above, but without the delay
// to be used by color animation functions which must heed the 500us reset period
void set_led_rgb_no_delay(uint8_t red, uint8_t green, uint8_t blue)
{
    uint8_t led[3];
    led[0] = red;
    led[1] = green;
    led[2] = blue;
    set_led_bytes(led);
    delay_us(COLOR_LATCH_DURATION);
}

void led_pattern_idle(uint32_t t, color_t *c)
{
    c->red =  (int)((sin((float)t / 50) + 1.0) * 127);
    c->blue = 0; 
    c->green = (int)((sin((float)t / 50) + 1.0) * 127);
}

void led_pattern_dispense(uint32_t t, color_t *c)
{
    c->red =  (int)((sin((float)t / 30) + 1.0) * 127);
    c->blue =  (int)((cos((float)t / 30) + 1.0) * 127);
    c->green = 0;
}

void led_pattern_drink_done(uint32_t t, color_t *c)
{
    c->red = 0;
    c->blue = 0;
    c->green = (int)((sin((float)t / 30) + 1.0) * 127);
}

// fade from one color to another colors in steps with a delay of delay
void fade(uint16_t steps, uint16_t delay, color_t *from, color_t *to)
{
    float    rstep, gstep, bstep;
    uint16_t i;
    color_t  c;

    rstep = ((float)to->red - (float)from->red) / steps;
    gstep = ((float)to->green - (float)from->green) / steps;
    bstep = ((float)to->blue - (float)from->blue) / steps;

    for(i = 0; i < steps; i++)
    {
        c.red = from->red + (int16_t)(i * rstep);
        c.green = from->green + (int16_t)(i * gstep);
        c.blue = from->blue + (int16_t)(i * bstep);
        set_led_rgb_no_delay(c.red, c.green, c.blue);
        delay_ms(delay);
    }
}
