#include <stdio.h>
#include "hue.h"

#define HUE_MAX           252 
#define STEPS_PER_HEXTET   42

void color_hue(uint8_t h, color_t *c) 
{
    uint8_t s = h % (252 / 6);
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
