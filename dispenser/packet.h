#ifndef __PACKET_H__
#define __PACKET_H__

#define PACKET_FIND_ID         0
#define PACKET_ASSIGN_ID       1
#define PACKET_START           2
#define PACKET_PING            3
#define PACKET_SET_MOTOR_SPEED 4
#define PACKET_TICK_DISPENSE   5
#define PACKET_TIME_DISPENSE   6
#define PACKET_LED_OFF         7
#define PACKET_LED_IDLE        8
#define PACKET_LED_DISPENSE    9
#define PACKET_LED_DRINK_DONE  10
#define PACKET_COMM_TEST       0xFE
#define PACKET_BROADCAST       0xFF

#define PACKET_ACK_OK          0
#define PACKET_ACK_CRC_FAIL    1
#define PACKET_ACK_TIMEOUT     2

#define ROUTER_CMD_SYNC_ON     251
#define ROUTER_CMD_SYNC_OFF    252
#define ROUTER_CMD_PING        253
#define ROUTER_CMD_COUNT       254
#define ROUTER_CMD_RESET       255

#define REC_OK           0
#define REC_CRC_FAIL     1
#define REC_RESET        2

typedef struct
{
    uint8_t dest;
    uint8_t type;
    union
    {
        uint8_t  uint8[4];
        int8_t   int8[4];
        uint16_t uint16[2];
        int16_t  int16[2];
        uint32_t uint32;
        int32_t  int32;
    } p;
    uint16_t     crc;
} packet_t;

#endif
