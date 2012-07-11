#ifndef __HUE_H__
#define __HUE_H__

#include <stdint.h>

#define HUE_MAX           252 

typedef struct
{
    uint8_t red, green, blue;
} color_t;

void color_hue(uint8_t h, color_t *c);

#endif
