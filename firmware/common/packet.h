#ifndef __PACKET_H__
#define __PACKET_H__

/* IMPORTANT!! 

This file defines the constants and packet structure for the communication
between the router and the dispensers. These values are duplicated in
the python code in ui/bartendro/router/driver.py. This should be improved
at some point.

*/

#define RAW_PACKET_SIZE        10
#define PACKET_SIZE            8

#define PACKET_PING                   3
#define PACKET_SET_MOTOR_SPEED        4
#define PACKET_TICK_DISPENSE          5
#define PACKET_TIME_DISPENSE          6
#define PACKET_LED_OFF                7
#define PACKET_LED_IDLE               8
#define PACKET_LED_DISPENSE           9
#define PACKET_LED_DRINK_DONE         10
#define PACKET_IS_DISPENSING          11  // requires response
#define PACKET_LIQUID_LEVEL           12  // requires response
#define PACKET_UPDATE_LIQUID_LEVEL    13 // requires a few ms of quiet time while measurements are taken
#define PACKET_ID_CONFLICT            14
#define PACKET_LED_CLEAN              15
#define PACKET_SET_CS_THRESHOLD       16
#define PACKET_SAVED_TICK_COUNT       17 // requires response
#define PACKET_RESET_SAVED_TICK_COUNT 18 
#define PACKET_GET_LIQUID_THRESHOLDS  19 // requires response
#define PACKET_SET_LIQUID_THRESHOLDS  20
#define PACKET_FLUSH_SAVED_TICK_COUNT 21
#define PACKET_TICK_SPEED_DISPENSE    22
#define PACKET_PATTERN_DEFINE         23
#define PACKET_PATTERN_ADD_SEGMENT    24
#define PACKET_PATTERN_FINISH         25
#define PACKET_COMM_TEST              0xFE

#define DEST_BROADCAST         0xFF

#define PACKET_ACK_OK          0
#define PACKET_ACK_CRC_FAIL    1
#define PACKET_ACK_INVALID     3
#define PACKET_ACK_INVALID_HEADER 4
#define PACKET_ACK_HEADER_IN_PACKET 5

#define ROUTER_CMD_SYNC_ON     251
#define ROUTER_CMD_SYNC_OFF    252
#define ROUTER_CMD_PING        253
#define ROUTER_CMD_COUNT       254
#define ROUTER_CMD_RESET       255

#define NUM_PACKET_SEND_TRIES  3

#define COMM_OK           0 
#define COMM_CRC_FAIL     1 
#define COMM_RESET        2
#define COMM_SEND_FAIL    3
#define COMM_PANIC        4

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
