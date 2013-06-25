#ifndef __LED_H__
#define __LED_H__

typedef struct
{
        uint8_t red, green, blue;
} color_t;

void set_led_rgb(uint8_t red, uint8_t green, uint8_t blue);
void led_pattern_init(int8_t pattern);
void led_pattern_next(uint32_t t, color_t *c);

// LED animation patterns
#define LED_PATTERN_OFF           -1 
#define LED_PATTERN_IDLE          0
#define LED_PATTERN_DISPENSE      1
#define LED_PATTERN_DRINK_DONE    2
#define LED_PATTERN_CLEAN         3
#define LED_PATTERN_CURRENT_SENSE 4
#define LED_PATTERN_LAST          5

// Define custom animations
#define CUSTOM_PATTERN_OK           0
#define CUSTOM_PATTERN_NOT_FINISHED 1
#define CUSTOM_PATTERN_INVALID      2
#define CUSTOM_PATTERN_FULL         3

uint8_t pattern_define(uint8_t pattern);
uint8_t pattern_add_segment(color_t *color, uint8_t steps);
uint8_t pattern_finish(void);

#endif
