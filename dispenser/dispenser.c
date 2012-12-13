#define F_CPU 8000000UL 
#include <avr/io.h>
#include <avr/interrupt.h>
#include <util/delay.h>

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
    uint8_t i, *ch = (uint8_t *)p;

    for(i = 0; i < sizeof(packet_t); i++)
        *ch = serial_rx();

    return 1;
}

// TODO: Handle collisions
uint8_t get_address(void)
{
    uint8_t  id;
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
        receive_packet(&p);
        if (p.type != PACKET_FIND_ID)
            break;

        if (p.p.uint8[0] == id)
        {
            set_led(0, 1, 0);
            sbi(PORTD, 1);
        }
        else
            cbi(PORTD, 1);
    }

    for(;;)
    {
        receive_packet(&p);
        if (p.type != PACKET_ASSIGN_ID && p.dest == id)
            break;
    }
    id = p.p.uint8[0];
    set_led(0, 0, 1);

    for(;;)
    {
        receive_packet(&p);
        if (p.type == PACKET_START)
            break;
    }
    set_led(0, 0, 0);

    serial_enable(1, 1);

    return id;
}

int main (void)
{
    uint8_t id;

    serial_init();
    DDRB |= (1<< PORTB5) | (1 << PORTB1) | (1 << PORTB2) | (1 << PORTB3);
    set_led(0, 0, 0);

    flash_led(1);

    id = get_address();
    for(;;)
        ;

    return 0;
}
