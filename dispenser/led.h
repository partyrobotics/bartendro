#ifndef __LED_H__
#define __LED_H__

typedef struct
{
        uint8_t red, green, blue;
} color_t;

void set_led_rgb(uint8_t red, uint8_t green, uint8_t blue);
void set_led_rgb_no_delay(uint8_t red, uint8_t green, uint8_t blue);

// LED animation patterns
void panic(uint32_t t, color_t *c);

#endif
