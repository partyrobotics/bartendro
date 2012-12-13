#ifndef __SERIAL_H__
#define __SERIAL_H__

void serial_init(void);
void serial_enable(uint8_t rx, uint8_t tx);
void serial_tx(uint8_t ch);
uint8_t serial_rx(void);

#endif
