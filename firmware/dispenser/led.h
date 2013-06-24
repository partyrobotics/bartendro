#ifndef __LED_H__
#define __LED_H__

typedef struct
{
        uint8_t red, green, blue;
} color_t;

void set_led_rgb(uint8_t red, uint8_t green, uint8_t blue);
void led_pattern_init(uint8_t pattern);
void led_pattern_next(uint32_t t, color_t *c);

// LED animation patterns
#define LED_PATTERN_OFF           0
#define LED_PATTERN_IDLE          1
#define LED_PATTERN_DISPENSE      2
#define LED_PATTERN_DRINK_DONE    3
#define LED_PATTERN_CLEAN         4
#define LED_PATTERN_CURRENT_SENSE 5

#endif
