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
#include "led.h"

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
    color_t color;
    uint8_t steps;
} color_segment_t;

typedef struct
{
    color_segment_t *segments;
    uint8_t          num;
} pattern_t;

#define LED_IDLE_NUM_SEGMENTS 3
static color_segment_t idle_segments[LED_IDLE_NUM_SEGMENTS] =
{
    { { 255,  0, 0},  100 },
    { { 0,  255, 0},  100 },
    { { 0,  0, 255},  100 }
};

#define LED_DISPENSE_NUM_SEGMENTS 2
static color_segment_t dispense_segments[LED_DISPENSE_NUM_SEGMENTS] =
{
    { { 255,  0, 0},  50 },
    { { 0,  0, 255},  50 }
};

#define LED_DRINK_DONE_NUM_SEGMENTS 2
static color_segment_t drink_done_segments[LED_DRINK_DONE_NUM_SEGMENTS] =
{
    { { 0,  255, 0},  75 },
    { { 0,  90, 0},  75 }
};

#define LED_CLEAN_NUM_SEGMENTS 4
static color_segment_t clean_segments[LED_CLEAN_NUM_SEGMENTS] =
{
    { { 150,   14, 235},  40 },
    { {  85,    8, 133},  40 },
    { {  85,   64,  64},  40 },
    { { 255,  128,   0},  40 }
};

#define LED_CURRENT_SENSE_NUM_SEGMENTS 4
static color_segment_t current_sense_segments[LED_CURRENT_SENSE_NUM_SEGMENTS] =
{
    { { 255, 0, 0},  15 },
    { { 255, 0, 0},  0 },
    { { 0,   0, 0},  15 },
    { { 0,   0, 0},  0 }
};

#define MAX_PATTERNS 5
pattern_t g_pattern_table[MAX_PATTERNS] =
{ 
    { idle_segments,          LED_IDLE_NUM_SEGMENTS          },
    { dispense_segments,      LED_DISPENSE_NUM_SEGMENTS      },
    { drink_done_segments,    LED_DRINK_DONE_NUM_SEGMENTS    },
    { clean_segments,         LED_CLEAN_NUM_SEGMENTS         },
    { current_sense_segments, LED_CURRENT_SENSE_NUM_SEGMENTS }
};

#define MAX_NUM_CUSTOM_SEGMENTS 32
color_segment_t  g_custom_segments[MAX_NUM_CUSTOM_SEGMENTS];
uint8_t          g_num_custom_segments = 0;

color_segment_t *g_custom_index            = NULL;
int8_t           g_custom_pattern          = -1;
uint8_t          g_custom_pattern_segments = 0;

static color_segment_t *g_cur_segment = NULL;
static uint8_t          g_num_segments = 0;
static uint8_t          g_segment_index = 0;
static uint8_t          g_segment_step = 255;

uint8_t pattern_define(uint8_t pattern)
{
    if (g_custom_pattern != -1)
        return CUSTOM_PATTERN_NOT_FINISHED;

    if (g_custom_pattern >= LED_PATTERN_LAST)
        return CUSTOM_PATTERN_INVALID;

    g_custom_pattern = pattern;
    g_custom_index = &g_custom_segments[g_num_custom_segments];
    g_custom_pattern_segments = 0;

    return CUSTOM_PATTERN_OK;
}

uint8_t pattern_add_segment(color_t *color, uint8_t steps)
{
    if (g_num_custom_segments == MAX_NUM_CUSTOM_SEGMENTS)
        return CUSTOM_PATTERN_FULL;

    g_custom_segments[g_num_custom_segments].color = *color;
    g_custom_segments[g_num_custom_segments].steps = steps;

    g_num_custom_segments++;
    g_custom_pattern_segments++;

    return CUSTOM_PATTERN_OK;
}

uint8_t pattern_finish(void)
{
    if (g_custom_pattern == -1)
        return CUSTOM_PATTERN_INVALID;

    g_pattern_table[g_custom_pattern].segments = g_custom_index;      
    g_pattern_table[g_custom_pattern].num = g_custom_pattern_segments;
    g_custom_pattern = -1;
    g_custom_index = NULL;

    return CUSTOM_PATTERN_OK;
}

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
void set_led_rgb(uint8_t red, uint8_t green, uint8_t blue)
{
    uint8_t led[3];
    led[0] = blue;
    led[1] = red;
    led[2] = green;
    set_led_bytes(led);
    delay_us(COLOR_LATCH_DURATION);
}

void led_pattern_init(int8_t pattern)
{
    switch(pattern)
    {
        case LED_PATTERN_OFF:
            g_cur_segment = NULL;
            g_num_segments = 0;
            break;

        case LED_PATTERN_IDLE:
        case LED_PATTERN_DISPENSE:
        case LED_PATTERN_DRINK_DONE:
        case LED_PATTERN_CLEAN:
        case LED_PATTERN_CURRENT_SENSE:
            g_cur_segment = g_pattern_table[pattern].segments;
            g_num_segments = g_pattern_table[pattern].num;
            break;
    }
    g_segment_step = 255;
    g_segment_index = 0;
}

void led_pattern_next(uint32_t t, color_t *c)
{
    static color_t  *from;
    static float     rstep, gstep, bstep;
    color_t         *to;

    if (!g_cur_segment)
    {
        c->red = 0;
        c->blue = 0;
        c->green = 0;
        return;
    }

    if (g_segment_step == 255)
    {
        from = &g_cur_segment[g_segment_index].color;
        to = &g_cur_segment[(g_segment_index + 1) % g_num_segments].color;
        g_segment_step = 0;

        if (g_cur_segment[g_segment_index].steps == 0)
        {
            rstep = 0;
            gstep = 0;
            bstep = 0;
        }
        else
        {
            rstep = ((float)to->red - (float)from->red) / g_cur_segment[g_segment_index].steps;
            gstep = ((float)to->green - (float)from->green) / g_cur_segment[g_segment_index].steps;
            bstep = ((float)to->blue - (float)from->blue) / g_cur_segment[g_segment_index].steps;
        }
    }
    c->red = from->red + (int16_t)(g_segment_step * rstep);
    c->green = from->green + (int16_t)(g_segment_step * gstep);
    c->blue = from->blue + (int16_t)(g_segment_step * bstep);

    g_segment_step++;
    if (g_cur_segment[g_segment_index].steps == g_segment_step ||
        g_cur_segment[g_segment_index].steps == 0)
    {
        g_segment_step = 255;
        g_segment_index = (g_segment_index + 1) % g_num_segments;
    }
}
