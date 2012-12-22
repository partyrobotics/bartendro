#ifndef __LED_H__
#define __LED_H__

typedef struct
{
        uint8_t red, green, blue;
} color_t;

void led_startup(void);
void set_led_bytes(uint8_t *leds);
void set_led_color(color_t *color);
void set_led_rgb(uint8_t red, uint8_t green, uint8_t blue);
void panic(uint16_t t, color_t *c);
void orange(uint16_t t, color_t *c);

#endif
