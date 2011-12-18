#ifndef __PACKET_H__
#define __PACKET_H__

#define PACKET_TYPE_RESPONSE 0
#define PACKET_TYPE_START    1
#define PACKET_TYPE_STOP     2
#define PACKET_TYPE_READ_POS 3
#define PACKET_TYPE_CHECK    4

typedef struct
{
    uint8_t header[2];
    uint8_t type;
    uint8_t addr;
    uint8_t payload[2];
    uint8_t pad; // do not use. sometimes the last byte gets corrupted in the daisy chain!
} packet;

void make_packet(packet *p, uint8_t addr, uint8_t type);

#endif
