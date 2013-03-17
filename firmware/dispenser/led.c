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

#include "defs.h"

#define NUM_LED 1
#define NUM_DATA (NUM_LED * 3)

#define HUE_MAX           252 
#define STEPS_PER_HEXTET   42

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
    led[0] = green;
    led[1] = red;
    led[2] = blue;
    set_led_bytes(led);
    delay_us(COLOR_LATCH_DURATION);
}

// Same as the above, but without the delay
// to be used by color animation functions which must heed the 500us reset period
void set_led_rgb_no_delay(uint8_t red, uint8_t green, uint8_t blue)
{
    uint8_t led[3];
    led[0] = green;
    led[1] = red;
    led[2] = blue;
    set_led_bytes(led);
    delay_us(COLOR_LATCH_DURATION);
}

void led_pattern_hue(uint32_t t, color_t *c) 
{
    uint8_t s, h;

    h = (uint8_t)(t & 0xFF);
    if (h >= HUE_MAX)
    {
        c->red = HUE_MAX;
        c->green = 0;
        c->blue = 0;

        return;
    }
    s = h % (252 / 6);
    switch(h / STEPS_PER_HEXTET) 
    {
        case 0:  // from 255, 0, 0 to 255, 255, 0
            c->red = HUE_MAX;
            c->green = s * 6;
            c->blue = 0;
            break;
        case 1: 
            c->red = HUE_MAX - (s * 6);
            c->green = HUE_MAX;
            c->blue = 0;
            break;
        case 2: 
            c->red = 0;
            c->green = HUE_MAX;
            c->blue = s * 6;
            break;
        case 3: 
            c->red = 0;
            c->green = HUE_MAX - (s * 6);
            c->blue = HUE_MAX;
            break;
        case 4: 
            c->red = (s * 6);
            c->green = 0;
            c->blue = HUE_MAX;
            break;
        case 5: 
            c->red = HUE_MAX;
            c->green = 0;
            c->blue = HUE_MAX - (s * 6);
            break;
    }
    c->red += 3;
    c->green += 3;
    c->blue += 3;
}

#if 0
int main(int argc, char *argv[])
{
    uint8_t i;
    color_t c;

    for(i = 0; i < HUE_MAX; i++)
    {
        color_hue(i, &c);
        printf("%d: %d, %d, %d\n", i, c.red, c.green, c.blue);
    }
}
#endif
void led_pattern_idle(uint32_t t, color_t *c)
{
    uint8_t t8 = t & 0xFF;

    if (t8 < 128)
        c->blue = t * 2;
    else
        c->blue = 255 - (2 * (t - 128));
    c->red = 0;
    c->green = 0;
}

void led_pattern_dispense(uint32_t t, color_t *c)
{
    uint8_t t8 = t & 0xFF;

    if (t8 < 128)
        c->blue = t * 2;
    else
        c->blue = 255 - (2 * (t - 128));
    c->red = 255 - c->blue;
    c->green = 0;
}

void led_pattern_drink_done(uint32_t t, color_t *c)
{
    uint8_t t8 = t & 0xFF;

    if (t8 < 128)
        c->green = t * 2;
    else
        c->green = 255 - (2 * (t - 128));
    c->blue = 0;
    c->red = 0;
}

void led_pattern_clean(uint32_t t, color_t *c)
{
    uint8_t t8 = t & 0xFF;

    if (t8 < 128)
    {
        c->red = t * 2;
        c->green = t * 2;
    }
    else
    {
        c->red = 255 - (2 * (t - 128));
        c->green = 255 - (2 * (t - 128));
    }
    c->blue = 0;
}

#if 0
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
#endif
