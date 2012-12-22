#define F_CPU 8000000UL 
#include <avr/io.h>
#include <avr/interrupt.h>
#include <util/delay.h>
#include <util/crc16.h>

#include <stddef.h>
#include <math.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <avr/eeprom.h>
#include <stdarg.h>
#include <stdlib.h>
#include "defs.h"

#include "packet.h"
#include "serial.h"

static volatile uint32_t g_time = 0;
static volatile uint32_t g_reset_fe_time = 0;
static volatile uint32_t g_reset = 0;
#define RESET_DURATION   1
#define RECEIVE_TIMEOUT  100
#define TIMER1_INIT      0xFFE6

ISR (TIMER1_OVF_vect)
{
    g_time++;
    TCNT1 = TIMER1_INIT;
}

// reset pin change
ISR(INT0_vect)
{
    if (PIND & (1<<PIND2))
    {
        g_reset_fe_time = g_time + RESET_DURATION;
    }
    else
    {
        if (g_reset_fe_time > 0 && g_time >= g_reset_fe_time)
            g_reset = 1;
        g_reset_fe_time = 0;
    }
}

uint8_t check_reset(void)
{
    uint8_t reset;

    cli();
    reset = g_reset;
    sei();

    return reset;
}

uint8_t serial_rx_check_reset()
{
    while ( !(UCSR0A & (1<<RXC0)) && !check_reset()) 
         ;

    return UDR0;
}

void set_led(uint8_t red, uint8_t green, uint8_t blue)
{
    if (red)
        cbi(PORTB, 1);
    else
        sbi(PORTB, 1);
    if (green)
        cbi(PORTB, 2);
    else
        sbi(PORTB, 2);
    if (blue)
        cbi(PORTB, 3);
    else
        sbi(PORTB, 3);
}


uint32_t EEMEM _ee_random_number;
uint32_t EEMEM _ee_run_time;

void set_random_seed_from_eeprom(void)
{
    uint32_t r;

    eeprom_read_block((void *)&r, &_ee_random_number, sizeof(uint32_t));
    srandom(r);
}

uint8_t receive_packet(packet_t *p)
{
    uint32_t timeout, now;
    uint16_t crc = 0;
    uint8_t  i, *ch = (uint8_t *)p;

    i = UDR0; // read whatever might be leftover
    for(i = 0; i < sizeof(packet_t); i++, ch++)
    {
        *ch = serial_rx_check_reset();
        if (check_reset())
            return REC_RESET;

        if (i == 0)
        {
            cli();
            timeout = g_time;
            sei();
            timeout += RECEIVE_TIMEOUT;
        }
        else
        {
            cli();
            now = g_time;
            sei();
            if (now > timeout)
            {
                i = 0;
                ch = (uint8_t *)p;
                timeout = now + RECEIVE_TIMEOUT;
            }
        }
    }

    crc = _crc16_update(crc, p->dest);
    crc = _crc16_update(crc, p->type);
    crc = _crc16_update(crc, p->p.uint8[0]);
    crc = _crc16_update(crc, p->p.uint8[1]);
    crc = _crc16_update(crc, p->p.uint8[2]);
    crc = _crc16_update(crc, p->p.uint8[3]);
    if (crc != p->crc)
        return REC_CRC_FAIL;

    return REC_OK;
}

// TODO: Handle collisions
uint8_t get_address(void)
{
    uint8_t  id, rec;
    packet_t p;

    set_random_seed_from_eeprom();

    // turn off serial TX and set the TX line to output
    serial_enable(1, 0);
    DDRD |= (1 << PORTD1);

    // Pick a random 8-bit number
    id = random() % 255;

    set_led(1, 0, 0);
    for(;;)
    {
        rec = receive_packet(&p);
        if (rec == REC_CRC_FAIL)
        {
            set_led(1, 1, 0);
            continue;
        }
        if (rec == REC_RESET)
            return 0xFF;

        if (p.type == PACKET_ASSIGN_ID)
            break;

        if (p.p.uint8[0] == id)
        {
            set_led(1, 0, 1);
            sbi(PORTB, 5);
            sbi(PORTD, 1);
            _delay_ms(RESET_DURATION + RESET_DURATION);
            cbi(PORTB, 5);
            cbi(PORTD, 1);
        }
    }

    // We haven't processed the previous packet yet
    for(;;)
    {
        if (p.type == PACKET_ASSIGN_ID)
        {
            if (p.dest == id)
            {
                set_led(0, 1, 1);
                break;
            }
        }

        rec = receive_packet(&p);
        if (rec == REC_CRC_FAIL)
        {
            set_led(1, 1, 0);
            for(;!check_reset();)
                ;
            return 0xFF;
        }
        if (rec == REC_RESET)
            return 0xFF;
    }
    id = p.p.uint8[0];
    set_led(0, 0, 1);

    for(;;)
    {
        rec = receive_packet(&p);
        if (rec == REC_CRC_FAIL)
        {
            set_led(1, 1, 0);
            for(;!check_reset();)
                ;
            return 0xFF;
        }
        if (rec == REC_RESET)
            return 0xFF;

        if (p.type == PACKET_START)
            break;
    }
    set_led(0, 1, 0);

    serial_enable(1, 1);

    return id;
}

void setup(void)
{
    // Set up LEDs

    // Timer setup for reset pulse width measuring
    TCCR1B |= _BV(CS11)|(1<<CS10); // clock / 64 / 25 = .0001 per tick
    TCNT1 = TIMER1_INIT;
    TIMSK1 |= (1<<TOIE1);

    // INT0 for router reset
    EICRA |= (1 << ISC00);
    EIMSK |= (1 << INT0);
}

void flash_led(uint8_t fast)
{
    int i;

    for(i = 0; i < 5; i++)
    {
        sbi(PORTB, 5);
        if (fast)
            _delay_ms(50);
        else
            _delay_ms(250);
        cbi(PORTB, 5);
        if (fast)
            _delay_ms(50);
        else
            _delay_ms(250);
    }
}

void test(void)
{
    packet_t p;

    for(;;)
    {
        if (receive_packet(&p) == REC_OK)
            set_led(0, 1, 0);
        else
            set_led(1, 0, 0);
    }
}

int main (void)
{
    uint8_t id;

    for(;;)
    {
        cli();
        g_reset = 0;

        DDRB |= (1<< PORTB5) | (1 << PORTB1) | (1 << PORTB2) | (1 << PORTB3);
        set_led(0, 0, 0);

        setup();
        serial_init();
        flash_led(1);

        sei();

//        test();

        id = get_address();
        if (id == 0xFF)
            continue;

        for(; !check_reset();)
        {
        }
    }
    return 0;
}
