#ifndef __PACKET_H__
#define __PACKET_H__

#define PACKET_TYPE_RESPONSE 0
#define PACKET_TYPE_START    1
#define PACKET_TYPE_STOP     2
#define PACKET_TYPE_READ_POS 3
#define PACKET_TYPE_CHECK    4
#define PACKET_TYPE_DISPENSE 5
#define PACKET_TYPE_GETSTATE 6

typedef struct
{
    uint8_t  header[2];
    uint8_t  type;
    uint8_t  addr;
    union 
    {
        uint16_t word;
        uint8_t  ch[2];
    } payload;
} packet;

void make_packet(packet *p, uint8_t addr, uint8_t type);

#endif
