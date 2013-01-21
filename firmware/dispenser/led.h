#ifndef __LED_H__
#define __LED_H__

typedef struct
{
        uint8_t red, green, blue;
} color_t;

void set_led_rgb(uint8_t red, uint8_t green, uint8_t blue);
void set_led_rgb_no_delay(uint8_t red, uint8_t green, uint8_t blue);

// LED animation patterns
void led_pattern_idle(uint32_t t, color_t *c);
void led_pattern_dispense(uint32_t t, color_t *c);
void led_pattern_drink_done(uint32_t t, color_t *c);

#endif
