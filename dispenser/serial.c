#include <avr/io.h>
#include <util/crc16.h>
#include <avr/interrupt.h>
#include "defs.h"
#include "serial.h"

#define BAUD 38400
#define UBBR (F_CPU / 16 / BAUD - 1)
#define RECEIVE_TIMEOUT  100

extern uint8_t check_reset(void);
extern volatile uint32_t g_time;

void serial_init(void)
{
    /*Set baud rate */ 
    UBRR0H = (unsigned char)(UBBR>>8); 
    UBRR0L = (unsigned char)UBBR; 
    /* Enable transmitter */ 
    UCSR0B = (1<<TXEN0) | (1<<RXEN0); 
    /* Set frame format: 8data, 1stop bit */ 
    UCSR0C = (0<<USBS0)|(3<<UCSZ00); 
}

void serial_enable(uint8_t rx, uint8_t tx)
{
    if (rx)
        UCSR0B |= (1<<RXEN0); 
    else
        UCSR0B &= ~(1<<RXEN0); 

    if (tx)
        UCSR0B |= (1<<TXEN0); 
    else
        UCSR0B &= ~(1<<TXEN0); 
}

void serial_tx(uint8_t ch)
{
    while ( !( UCSR0A & (1<<UDRE0)) );
    UDR0 = ch;
}

uint8_t serial_rx(void)
{
    while ( !(UCSR0A & (1<<RXC0))) 
        ;

    return UDR0;
}

uint8_t serial_tx_nb(uint8_t ch)
{
    if (UCSR0A & (1<<UDRE0))
    {
        UDR0 = ch;
        return 1;
    }
    return 0;
}

uint8_t serial_rx_nb(uint8_t *ch)
{
    if (UCSR0A & (1<<RXC0)) 
    {
        *ch = UDR0;
        return 1;
    }
    return 0;
}

uint8_t receive_packet(packet_t *p)
{
    uint32_t timeout = 0, now;
    uint16_t crc = 0;
    uint8_t  i, *ch = (uint8_t *)p, timed_out, ret, ack;

    for(;!check_reset();)
    {
        timed_out = 0;
        i = UDR0; // read whatever might be leftover
        for(i = 0; i < sizeof(packet_t); i++, ch++)
        {
            for(;;)
            {
                ret = serial_rx_nb(ch);
                if (check_reset())
                    return REC_RESET;

                if (ret)
                {
                    if (i == 0)
                    {
                        cli();
                        timeout = g_time;
                        sei();
                        timeout += RECEIVE_TIMEOUT;
                    }
                    break;
                }

                cli();
                now = g_time;
                sei();
                if (timeout > 0 && now > timeout)
                {
                    sbi(PORTB, 5);
                    i = 0;
                    ch = (uint8_t *)p;
                    timed_out = 1;
                    timeout = 0;
                    for(;;)
                    {
                        ret = serial_tx_nb(PACKET_ACK_TIMEOUT);
                        if (check_reset())
                            return REC_RESET;
                        if (ret)
                            break;
                    }
                    break;
                }
            }
            if (timed_out)
                break;
        }
        if (timed_out)
            continue;

        crc = 0;
        crc = _crc16_update(crc, p->dest);
        crc = _crc16_update(crc, p->type);
        crc = _crc16_update(crc, p->p.uint8[0]);
        crc = _crc16_update(crc, p->p.uint8[1]);
        crc = _crc16_update(crc, p->p.uint8[2]);
        crc = _crc16_update(crc, p->p.uint8[3]);
        if (crc != p->crc)
            ack = PACKET_ACK_CRC_FAIL;
        else
            ack = PACKET_ACK_OK;

        for(;;)
        {
            ret = serial_tx_nb(ack);
            if (check_reset())
                return REC_RESET;
            if (ret)
                break;
        }
        return REC_OK;
    }
    return REC_RESET;
}

uint8_t send_packet(packet_t *p)
{
    uint16_t crc = 0;
    uint8_t i, *ch = (uint8_t *)p, ret, ack;

    crc = _crc16_update(crc, p->dest);
    crc = _crc16_update(crc, p->type);
    crc = _crc16_update(crc, p->p.uint8[0]);
    crc = _crc16_update(crc, p->p.uint8[1]);
    crc = _crc16_update(crc, p->p.uint8[2]);
    p->crc = _crc16_update(crc, p->p.uint8[3]);

    for(;;)
    {
        for(i = 0; i < sizeof(packet_t); i++, ch++)
        {
            for(;;)
            {
                ret = serial_tx_nb(*ch);
                if (check_reset())
                    return REC_RESET;

                if (ret)
                    break;
            }
        }
        sbi(PORTB, 5);
        for(;;)
        {
            ret = serial_rx_nb(&ack);
            if (check_reset())
                return REC_RESET;

            if (ret)
                break;
        }
        if (ack == PACKET_ACK_OK)
            return REC_OK;
    }

    // should never get here
    return PACKET_ACK_OK;
}

