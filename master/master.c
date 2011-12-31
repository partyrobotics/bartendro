#define F_CPU 16000000UL 
#include <avr/io.h>
#include <avr/interrupt.h>
#include <util/delay.h>

#include <stddef.h>
#include <math.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <avr/pgmspace.h>
#include <stdarg.h>
#include <stdlib.h>

#include "packet.h"

// Bit manipulation macros
#define sbi(a, b) ((a) |= 1 << (b))       //sets bit B in variable A
#define cbi(a, b) ((a) &= ~(1 << (b)))    //clears bit B in variable A
#define tbi(a, b) ((a) ^= 1 << (b))       //toggles bit B in variable A

#define BAUD 38400
#define UBBR (F_CPU / 16 / BAUD - 1)

#define TIMER1_INIT 0xFF06 // 16mhz / 64 cs / 250 = 1ms per 'tick'

static uint8_t g_debug = 1;
static volatile uint32_t g_ticks = 0;

ISR (TIMER1_OVF_vect)
{
    g_ticks++;
    TCNT1 = TIMER1_INIT;
}

void serial_init(void)
{
    /*Set baud rate */ 
    UBRR0H = (unsigned char)(UBBR>>8); 
    UBRR0L = (unsigned char)UBBR; 
    /* Enable transmitter */ 
    UCSR0B = (1<<TXEN0)|(1<<RXEN0); 
    /* Set frame format: 8data, 1stop bit */ 
    UCSR0C = (0<<USBS0)|(3<<UCSZ00); 
}

void serial_tx(unsigned char ch)
{
    while ( !( UCSR0A & (1<<UDRE0)) );
    UDR0 = ch;
}

unsigned char serial_rx(void)
{
    while ( !(UCSR0A & (1<<RXC0))) 
        ;

    return UDR0;
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

void setup(void)
{
    DDRB |= (1<<PINB1)|(1<<PINB0)|(1<<PINB2);
    DDRD |= (1<<PIND2)|(1<<PIND3)|(1<<PIND4)|(1<<PIND5)|(1<<PIND6)|(1<<PIND7);
    TCCR1B |= _BV(CS11)|(1<<CS10);
    TIMSK1 |= (1<<TOIE1);
    serial_init();
}

#define MAX_CMD_LEN 16
void get_cmd(char cmd[MAX_CMD_LEN])
{
    uint8_t ch, count;

    cmd[0] = 0;
    for(count = 0; count < MAX_CMD_LEN - 1; count++)
    {
        ch = serial_rx();
        if (g_debug)
            serial_tx(ch);
        if (ch == '\r')
        {
            if (g_debug)
                serial_tx('\n');
            break;
        }

        cmd[count] = (char)ch;
    }
    cmd[count] = 0;
}

void motor_state(uint8_t m, uint8_t s)
{
    switch(m)
    {
        case 0:
            if (s)
                cbi(PORTD, 2);
            else
                sbi(PORTD, 2);
            break;
        case 1:
            if (s)
                cbi(PORTD, 3);
            else
                sbi(PORTD, 3);
            break;
        case 2:
            if (s)
                cbi(PORTD, 4);
            else
                sbi(PORTD, 4);
            break;
        case 3:
            if (s)
                cbi(PORTD, 5);
            else
                sbi(PORTD, 5);
            break;
        case 4:
            if (s)
                cbi(PORTD, 6);
            else
                sbi(PORTD, 6);
            break;
        case 5:
            if (s)
                cbi(PORTD, 7);
            else
                sbi(PORTD, 7);
            break;
        case 6:
            if (s)
                cbi(PORTB, 0);
            else
                sbi(PORTB, 0);
            break;
        case 7:
            if (s)
                cbi(PORTB, 1);
            else
                sbi(PORTB, 1);
            break;
    }
}

typedef struct
{
    uint8_t disp;
    uint8_t state;
    uint16_t ticks;
} timing_info;

#define DISPENSE_TICKS  700
#define DISPENSE_DELAY 1000

uint8_t convert_timing(timing_info *info, uint8_t info_index, uint8_t disp, uint16_t dur)
{
    uint8_t dispense_chunks, i;
    uint16_t dispense_ticks, ticks = 0;

    dispense_chunks = (dur + DISPENSE_TICKS - 1) / DISPENSE_TICKS;
    dispense_ticks = (dur + dispense_chunks - 1) / dispense_chunks;
    //dprintf("chunks: %d ticks: %d\n", dispense_chunks, dispense_ticks);

    for(i = 0; i < dispense_chunks; i++)
    {
        info[info_index].disp = disp;
        info[info_index].state = 1;
        info[info_index].ticks = ticks;
        info_index++;

        ticks += dispense_ticks;

        info[info_index].disp = disp;
        info[info_index].state = 0;
        info[info_index].ticks = ticks;
        info_index++;

        ticks += DISPENSE_DELAY;
    }
    return info_index;
}

int compare(const void *a, const void *b)
{
    timing_info *ta = (timing_info *)a;
    timing_info *tb = (timing_info *)b;

    return ta->ticks - tb->ticks;
}

#define MASTER_REBOOTED 1
#define BAD_DISPENSER_INDEX_ERROR 2
#define INVALID_COMMAND_ERROR 3
#define g_num_dispensers 8

int main (void)
{
    uint8_t i;
    char cmd[MAX_CMD_LEN];
    uint16_t durs[8];
    timing_info info[64];
    uint8_t info_count = 0;

	setup();
    for(i = 0; i < 8; i++)
        motor_state(i, 0);

    dprintf("%d master booted\n", MASTER_REBOOTED);
    // Flash the LED to let us know we rebooted
    for(i = 0; i< 3; i++)
    {
        sbi(PORTB, 2);
        _delay_ms(100);
        cbi(PORTB, 2);
        _delay_ms(100);
    }

    for(;0;)
    {
        uint32_t t;

        cli();
        t = g_ticks;
        sei();

        if ((t % 1000) == 0)
            dprintf("%ld\n", t);
    }

    for(;0;)
    {
        for(i = 0; i < 8; i++)
        {
            dprintf("turn on %d\n", i);
            motor_state(i, 1);
            _delay_ms(1000);
            dprintf("turn off %d\n", i);
            motor_state(i, 0);
            _delay_ms(1000);
        }
    }

    memset(durs, 0, sizeof(durs));
    for(;;)
    {
        if (g_debug)
            dprintf(">");

        get_cmd(cmd);
        if (strlen(cmd) == 0)
            continue;

        if (strncasecmp(cmd, "go", 2) == 0)
        {
            uint32_t t0, t;
            qsort(info, info_count, sizeof(timing_info), compare);
//            for(i = 0; i < 8; i++)
//            {
//                if (durs[i] > 0)
//                    dprintf("durs %d: %d\n", i, durs[i]);
//            }

            cli();
            t0 = g_ticks;
            sei();
            for(i = 0; i < info_count;)
            {
                cli();
                t = g_ticks;
                sei();
                t -= t0;

                //dprintf("%ld\n", t);
                for(;i < info_count; i++)
                {
                    if (t >= info[i].ticks)
                    {
//                        dprintf("[%ld] info %d: %d %d\n", t, info[i].disp, info[i].ticks, info[i].state);
                        motor_state(info[i].disp, info[i].state);
                    }
                    else 
                        break;
                }
            }
            info_count = 0;
            memset(durs, 0, sizeof(durs));
        }

        if (strncasecmp(cmd, "disp", 4) == 0)
        {
            uint16_t dur, disp;
            uint8_t  ret;

            ret = sscanf(cmd, "disp %d %d", &disp, &dur);
            if (ret != 2)
            {
                dprintf("%d invalid command\n", INVALID_COMMAND_ERROR);
                continue;
            }
            if (disp < 0 || disp > g_num_dispensers)
            {
                dprintf("%d invalid dispenser\n", BAD_DISPENSER_INDEX_ERROR);
                continue;
            }
            durs[(uint8_t)disp] = dur;
            info_count = convert_timing(info, info_count, disp, dur);
            dprintf("0 ok\n");
            continue;
        }
    }

    return 0;
}
