#include <stdio.h>
#include <stdint.h>
#include <string.h>

void pack_7bit(uint8_t in_count, uint8_t *in, uint8_t *out_count, uint8_t *out)
{
    uint16_t buffer = 0;
    uint8_t  bitcount = 0;

    *out_count = 0;
    for(;;)
    {
        if (bitcount < 7)
        {
            buffer <<= 8;
            buffer |= *in++;
            in_count--;
            bitcount += 8;
        }
        *out = (buffer >> (bitcount - 7));
        out++;
        (*out_count)++;

        buffer &= (1 << (bitcount - 7)) - 1;
        bitcount -= 7;

        if (in_count == 0)
            break;
    }
    *out = buffer & 0xFF;
    out_count++;
}

void unpack_7bit(uint8_t in_count, uint8_t *in, uint8_t *out_count, uint8_t *out)
{
    uint16_t buffer = 0;
    uint8_t bitcount = 0;

    *out_count = 0;
    for(;;)
    {
        if (bitcount < 8)
        {
            buffer <<= 7;
            buffer |= *in++;
            in_count--;
            bitcount += 7;
        }

        if (bitcount >= 8)
        {
            *out = (buffer >> (bitcount - 8));
            out++;
            (*out_count)++;
            buffer &= (1 << (bitcount - 8)) - 1;
            bitcount -= 8;
        }

        if (in_count == 0)
            break;
    }

    out--;
    *out |= buffer;
}
