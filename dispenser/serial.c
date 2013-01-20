#include <string.h>
#include <avr/io.h>
#include <util/crc16.h>
#include <util/delay.h>
#include <avr/interrupt.h>
#include <stdio.h>
#include <stdarg.h>
#include "defs.h"
#include "serial.h"
#include "pack7.h"
#include "led.h"
#ifndef ROUTER
#include "i2cmaster.h"
#endif

#define BAUD             9600
#define UBBR             (F_CPU / 16 / BAUD - 1)
#define RECEIVE_TIMEOUT  100

extern uint8_t check_reset(void);
extern volatile uint32_t g_time;
extern void idle(void);

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

#ifdef ROUTER
void idle()
{
}
uint8_t check_reset(void)
{
    return 0;
}

#else

uint8_t receive_packet(packet_t *p)
{
    uint16_t crc = 0;
    uint8_t  i, j, ret, ack, header, ch, *ptr;
    uint8_t  unpacked_size;
    uint8_t  data[RAW_PACKET_SIZE];
    uint8_t  err = 0;
    uint8_t  rec_count = 0;

    memset(data, 0, sizeof(data));
    for(;!check_reset();)
    {
#if 1        
        if (err)
        {
            set_led_rgb(255,255,255);
            _delay_ms(500);
            for(ch = 0; ch < err; ch++)
            {
                set_led_rgb(255,0,0);
                _delay_ms(500);
                set_led_rgb(0,0,0);
                _delay_ms(500);
            }
            _delay_ms(500);
            for(ch = 0; ch < rec_count; ch++)
            {
                set_led_rgb(255,0,255);
                _delay_ms(500);
                set_led_rgb(0,0,0);
                _delay_ms(500);
            }
            _delay_ms(500);
        }
#endif

        header = 0;
        ack = PACKET_ACK_OK;
        for(;;)
        {
            ret = serial_rx_nb(&ch);
            if (check_reset())
                return COMM_RESET;

            if (ret)
            {
                if (ch == 0xFF)
                    header++;
                else 
                {
                    if (header > 0)
                    {
                        ack = PACKET_ACK_INVALID_HEADER;
                        break;
                    }
                }

                if (header == 2)
                    break;
            }
            idle();
        }

        if (ack == PACKET_ACK_OK)
        {
            for(i = 0; i < RAW_PACKET_SIZE; i++)
            {
                for(;;)
                {
                    ret = serial_rx_nb(&ch);
                    if (check_reset())
                        return COMM_RESET;

                    if (ret)
                    {
                        if (ch == 0xFF)
                        {
                            ack = PACKET_ACK_HEADER_IN_PACKET;
                            break;
                        }
                        if (err == 0)
                            rec_count++;

                        data[i] = ch;
                        break;
                    }
                    idle();
                }
                if (ack != PACKET_ACK_OK)
                    break;
            }
        }

        if (ack == PACKET_ACK_OK)
        {
            unpack_7bit(RAW_PACKET_SIZE, data, &unpacked_size, (uint8_t *)p);
            if (unpacked_size != PACKET_SIZE)
            {
                iprintf("Decoded packet size assert fail: %d vs %d\n", PACKET_SIZE, unpacked_size);
                set_led_rgb(255, 0, 0);
                ack = PACKET_ACK_INVALID;
                err = 3;
            }
        }

        if (ack == PACKET_ACK_OK)
        {
            crc = 0;
            for(i = 0, ptr = (uint8_t *)p; i < unpacked_size - 2; i++, ptr++)
                crc = _crc16_update(crc, *ptr);

            if (crc != p->crc)
                ack = PACKET_ACK_CRC_FAIL;
        }

        // send response, unless this is a broadcast packet
        if (p->dest != DEST_BROADCAST)
        {
            for(;;)
            {
                ret = serial_tx_nb(ack);
                if (check_reset())
                    return COMM_RESET;
                if (ret)
                {
                    set_led_rgb(255, 255, 0);
                    break;
                }
                idle();
            }
            for(;;)
            {
                ret = serial_tx_nb(ack);
                if (check_reset())
                    return COMM_RESET;
                if (ret)
                {
                    set_led_rgb(255, 255, 0);
                    break;
                }
                idle();
            }
        }
        if (ack != PACKET_ACK_OK)
        {
            iprintf("Bad packet received: %d\n", ack);
            continue; 
        }
#if 0
        else
        {
            iprintf("received:\n");
            for(i = 0, ptr = (uint8_t *)p; i < unpacked_size - 2; i++, ptr++)
                iprintf("  %02X\n", *ptr);
            iprintf("ack: %d\n\n", ack);
        }
#endif
        return COMM_OK;
    }
    iprintf("reach end of loop. bad!\n");
    return COMM_PANIC;
}

uint8_t send_packet8(uint8_t type, uint8_t data)
{
    packet_t p;
    
    memset(&p, 0, sizeof(packet_t));
    p.type = type;
    p.p.uint8[0] = data;

    return send_packet(&p);
}

uint8_t send_packet16(uint8_t type, uint16_t data)
{
    packet_t p;
    
    memset(&p, 0, sizeof(packet_t));
    p.type = type;
    p.p.uint16[0] = data;

    return send_packet(&p);
}

uint8_t send_packet(packet_t *p)
{
    uint16_t crc = 0;
    uint8_t i, *ch, ret, ack, tries, packed_size;
    uint8_t packed[RAW_PACKET_SIZE + 2]; // +2 for the header

    crc = _crc16_update(crc, p->dest);
    crc = _crc16_update(crc, p->type);
    crc = _crc16_update(crc, p->p.uint8[0]);
    crc = _crc16_update(crc, p->p.uint8[1]);
    crc = _crc16_update(crc, p->p.uint8[2]);
    p->crc = _crc16_update(crc, p->p.uint8[3]);

    pack_7bit(sizeof(packet_t), (uint8_t *)p, &packed_size, &packed[2]);
    if (packed_size != RAW_PACKET_SIZE)
    {
        iprintf("Encode packet size assert fail: %d vs %d\n", RAW_PACKET_SIZE, packed_size);
        set_led_rgb(255, 0, 0);
        ack = PACKET_ACK_INVALID;
    }

    packed[0] = 0xFF;
    packed[1] = 0xFF;
    for(tries = 0; tries < NUM_PACKET_SEND_TRIES; tries++)
    {
        // Send the packet data
        for(i = 0, ch = packed; i < RAW_PACKET_SIZE + 2; i++, ch++)
        {
            for(;;)
            {
                ret = serial_tx_nb(*ch);
                if (check_reset())
                    return COMM_RESET;

                if (ret)
                    break;

                idle();
            }
        }

        // Wait for the ACK
        for(;;)
        {
            ret = serial_rx_nb(&ack);
            if (check_reset())
                return COMM_RESET;

            if (ret)
                break;
            idle();
        }
        if (ack == PACKET_ACK_OK)
            return COMM_OK;
    }

    // whoops, we didn't succesfully send the packet. :-(
    return COMM_SEND_FAIL;
}


#define MAX 80
void iprintf(const char *fmt, ...)
{
    va_list va;
    va_start (va, fmt);

    char buffer[MAX];
    char *ptr = buffer;
    vsnprintf(buffer, MAX, fmt, va);
    va_end (va);

    i2c_init();
    i2c_start_wait(8+I2C_WRITE);     // set device address and write mode
    for(ptr = buffer; *ptr; ptr++)
    {
        if (*ptr == '\n') i2c_write('\r');
        i2c_write(*ptr);
    }
    i2c_stop(); 
}

#endif
