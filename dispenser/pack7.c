#include <stdio.h>
#include <stdint.h>
#include <string.h>

const char *b2b(int x)
{
    static char b[9];
    b[0] = '\0';

    int z;
    for (z = 128; z > 0; z >>= 1)
    {
        strcat(b, ((x & z) == z) ? "1" : "0");
    }

    return b;
}

void pack_7bit(uint8_t in_count, uint8_t *in, uint8_t *out_count, uint8_t *out)
{
    uint16_t buffer = 0;
    uint8_t  bitcount = 0, i;

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
    *out = buffer << (7 - bitcount);
    (*out_count)++;
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
}
