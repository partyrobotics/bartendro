#include <avr/io.h>
#include <stdint.h>
#include <stdlib.h>
#include <string.h>
#include <avr/interrupt.h>
#include <avr/pgmspace.h>
#include <util/delay.h>

#include "debug.h"

// Bit manipulation macros
#define sbi(a, b) ((a) |= 1 << (b))       //sets bit B in variable A
#define cbi(a, b) ((a) &= ~(1 << (b)))    //clears bit B in variable A
#define tbi(a, b) ((a) ^= 1 << (b))       //toggles bit B in variable A

#define MAX_MOTORS 3
typedef struct
{
    int8_t   motor;
    uint16_t duration;
} motor_cmd;

int compare(void *a, void *b)
{
    return ((motor_cmd *)a)->duration > ((motor_cmd *)b)->duration;
}

void run(uint8_t count, motor_cmd *cmds)
{
    uint8_t  i;
    uint16_t t = 0, duration;

    qsort(cmds, count, sizeof(motor_cmd), compare);

    for(i = 0; i < count; i++)
        dprintf("%05u: motor %d on, %u ms\n", t, cmds[i].motor, cmds[i].duration);
    
    // turn motors on
    for(i = 0; i < count; i++)
    {
        if (cmds[i].motor == 0)
            sbi(PORTB, 0);
        if (cmds[i].motor == 1)
            sbi(PORTB, 1);
        if (cmds[i].motor == 2)
            sbi(PORTB, 2);
    }
    for(i = 0; i < count; i++)
    {
        duration = cmds[i].duration - t;
        dprintf("delay: %d\n", duration);
        while(duration > 0)
        {
            uint8_t d = duration > 10 ? 10 : duration;
            _delay_ms(d);
            duration -= d;
            t += d;
        }
        if (cmds[i].motor == 0)
            cbi(PORTB, 0);
        if (cmds[i].motor == 1)
            cbi(PORTB, 1);
        if (cmds[i].motor == 2)
            cbi(PORTB, 2);
    }
}

static motor_cmd drinks[3][3] =
{
//    { // Test
//        { 0, 400 },
//        { 1, 2000 },
//        { 2, 1333 }
//    },
    { // Normal
        { 0, 3560 },
        { 1, 21360 },
        { 2, 10680 }
    },
    { // Strong
        { 0, 3830 },
        { 1, 19150 },
        { 2, 12770 }
    }
};

int main(void)
{
    uint8_t   i;

    serial_init();

    // Set PWM pins as outputs
    DDRB |= (1<<PB0)|(1<<PB1)|(1<<PB2);
    DDRB |= (1<<PB4)|(1<<PB3);

    /*
    for(i = 0; i < 3; i++)
    {
        sbi(PORTB, 0);
        sbi(PORTB, 1);
        sbi(PORTB, 2);
        _delay_ms(50);

        cbi(PORTB, 0);
        cbi(PORTB, 1);
        cbi(PORTB, 2);
        _delay_ms(50);
    }
    */

    dprintf("\nTequila Sunrise bot. What shall be your bidding?\n\n");
    for(;;)
    {
        if (!(PIND & (1<<PIND7)))
        {
            sbi(PORTB, 3);
            dprintf("making normal drink\n");
            run(3, drinks[0]);
            dprintf("drink complete. bottoms up!\n");
            cbi(PORTB, 3);
        }
        if (!(PIND & (1<<PIND6)))
        {
            sbi(PORTB, 4);
            dprintf("making strong drink\n");
            run(3, drinks[1]);
            dprintf("drink complete. bottoms up!\n");
            cbi(PORTB, 4);
        }
    }
	return 0;
}
