// 
// Copyright (c) Party Robotics LLC 2010
// Written by Robert Kaye <rob@partyrobotics.com>
//
#include <avr/io.h>
#include <stdarg.h>
#include <stdio.h>
#include <avr/interrupt.h>

#define BAUD 38400
#define UBBR (F_CPU / 16 / BAUD - 1)

#define _UBRRH UBRR0H
#define _UBRRL UBRR0L
#define _UCSRB UCSR0B
#define _UCSRC UCSR0C
#define _TXEN  TXEN0
#define _RXEN  RXEN0
#define _RXC   RXC0
#define _USBS  USBS0
#define _UCSZ1 UCSZ01
#define _UCSZ0 UCSZ00
#define _UCSRA UCSR0A
#define _UDRE  UDRE0
#define _UDR   UDR0 

// TODO: This section needs to be customized for each AVR chip.
void serial_init(void)
{
    // UART 0
    /*Set baud rate */ 
    _UBRRH = (unsigned char)(UBBR>>8); 
    _UBRRL = (unsigned char)UBBR; 

    /* Enable transmitter */ 
    _UCSRB = (1<<_TXEN)|(1<<_RXEN); 
    /* Set frame format: 8data, 1stop bit */ 
    _UCSRC = (0<<_USBS)|(3<<_UCSZ0); 
}

void serial_tx(unsigned char ch)
{
    while ( !( _UCSRA & (1<<_UDRE)) )
        ;

    _UDR = ch;
}

unsigned char serial_rx(void)
{
    while ( !(_UCSRA & (1<<_RXC))) 
        ;

    return _UDR;
}

#define MAX 80 
void dprintf(const char *fmt, ...)
{
    va_list va;
    va_start (va, fmt);

    char buffer[MAX];
    char *ptr = buffer;
    vsnprintf(buffer, MAX, fmt, va);
    va_end (va);

    for(ptr = buffer; *ptr; ptr++)
		{
		   if (*ptr == '\n') serial_tx('\r');
       serial_tx(*ptr);
    }
}
