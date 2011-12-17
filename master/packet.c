#include <stddef.h>
#include <math.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <avr/pgmspace.h>
#include <stdarg.h>
#include <stdlib.h>

#include "packet.h"

void make_packet(packet *p, uint8_t addr, uint8_t type)
{
    p->header[0] = 0xFF;
    p->header[1] = 0xFF;
    p->addr = addr;
    p->type = type;
}
