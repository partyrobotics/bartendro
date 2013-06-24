#ifndef __SERIAL_H__
#define __SERIAL_H__

#include "packet.h"

// Serial function
void serial_init(void);
void serial_enable(uint8_t rx, uint8_t tx);
void serial_tx(uint8_t ch);
uint8_t serial_rx(void);
uint8_t serial_rx_nb(uint8_t *ch);
uint8_t serial_tx_nb(uint8_t ch);

uint8_t receive_packet(packet_t *p);
uint8_t send_packet(packet_t *p);
uint8_t send_packet8(uint8_t type, uint8_t data);
uint8_t send_packet8_2(uint8_t type, uint8_t data0, uint8_t data1);
uint8_t send_packet16(uint8_t type, uint16_t data0, uint16_t data1);

void i2c_tx(uint8_t ch);
void iprintf(const char *fmt, ...);

#endif
