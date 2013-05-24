// 
// Copyright (c) Party Robotics LLC 2010
// Written by Robert Kaye <rob@partyrobotics.com>
//
#ifndef DEBUG_H
#define DEBUG_H

void          serial_init(void);
void          serial_tx(unsigned char ch);
unsigned char serial_rx(void);

void          dprintf(const char *fmt, ...);

#endif
