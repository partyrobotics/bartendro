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
    uint8_t  duty_cycle;
    uint16_t duration;
} motor_cmd;

void pwm_setup(void)
{
	/* Set to Fast PWM */
	TCCR0A = _BV(WGM01) | _BV(WGM00);
	TCCR1A = _BV(WGM10) | _BV(WGM12);
    TCCR0B |= _BV(CS00);
    TCCR1B |= _BV(CS10);

	TCNT0 = 0;
	TCNT1 = 0;
}

void pwm_on(uint8_t motor, uint8_t dc)
{
    // OCR0B = Digital 5
    // OCR0A = Digital 6
    // OCR1A = Digital 9

    if (motor == 0)
    {
	    TCCR0A |= _BV(COM0B1);
	    OCR0B = dc;
    }
    if (motor == 1)
    {
	    TCCR0A |= _BV(COM0A1);
	    OCR0A = dc;
    }
    if (motor == 2)
    {
	    TCCR1A |= _BV(COM1A1);
	    OCR1A = dc;
    }
}

void pwm_off(uint8_t motor)
{
    if (motor == 0)
    {
	    OCR0B = 0;
    }
    if (motor == 1)
    {
	    OCR0A = 0;
    }
    if (motor == 2)
    {
	    OCR1A = 0;
    }
}

void pwm_shutdown(void)
{
    TCCR0A = TCCR1A = TCCR0B = TCCR1B = 0;
}

#define MAX_CMD_LEN 16

// Returns true if command was read, false if incomplete/invalid command received
int8_t read_cmd(char *cmd)
{
    int8_t len, ch;

    *cmd = 0;
    dprintf("#");
    for(len = 0; len < MAX_CMD_LEN - 1; len++)
    {
        ch = serial_rx();
        if (ch == 8)
        {
            if (len <= 0)
            {
                dprintf("[beep]\n#");
                len = -1;
                continue;
            }
            dprintf("\b \b");
            len--;
            cmd[len] = 0;
            len--;
            continue;
        }
        if (ch == '\r')
        {
            dprintf("\n");
            if (len == 0)
                return 0;

            cmd[len] = 0;
            return 1;
        }
        cmd[len] = ch;
        cmd[len+1] = 0;
        serial_tx(ch);
    }
    return 0;
}

int compare(void *a, void *b)
{
    return ((motor_cmd *)a)->duration > ((motor_cmd *)b)->duration;
}

void run(uint8_t count, motor_cmd *cmds)
{
    uint8_t  i;
    uint16_t t = 0;

    qsort(cmds, count, sizeof(motor_cmd), compare);

    for(i = 0; i < count; i++)
        dprintf("%05u: motor %d on, %d duty_cycle, %u ms\n", t, cmds[i].motor, cmds[i].duty_cycle, cmds[i].duration);
    
    pwm_setup();
    // turn motors on
    for(i = 0; i < count; i++)
    {
        if (cmds[i].motor == 0)
            pwm_on(0, cmds[i].duty_cycle);
        if (cmds[i].motor == 1)
            pwm_on(1, cmds[i].duty_cycle);
        if (cmds[i].motor == 2)
            pwm_on(2, cmds[i].duty_cycle);
    }
    for(i = 0; i < count; i++)
    {
        cmds[i].duration -= t;
        while(cmds[i].duration > 0)
        {
            uint8_t d = cmds[i].duration > 10 ? 10 : cmds[i].duration;
            _delay_ms(d);
            cmds[i].duration -= d;
            t += d;
        }
        if (cmds[i].motor == 0)
            pwm_off(0);
        if (cmds[i].motor == 1)
            pwm_off(0);
        if (cmds[i].motor == 2)
            pwm_off(0);
    }
    pwm_shutdown();
}

#define MAX_CMDS 3
int main(void)
{
    uint8_t   i, j, num_cmds = 0;
    char      cmd[MAX_CMD_LEN], *t;
    motor_cmd cmds[MAX_CMDS];

    serial_init();

    // Set PWM pins as outputs
    DDRD |= (1<<PD6)|(1<<PD5);
    DDRB |= (1<<PB1);

    dprintf("\nBartendro pre-prototype-prototype at your service!\n\n");

    for(;;)
    {
        if (!read_cmd(cmd))
        {
            dprintf("stored commands cleared\n");
            num_cmds = 0;
            continue;
        }
        if (strcmp(cmd, "l") == 0)
        {
            dprintf("%d commands\n", num_cmds);
            for(i = 0; i < num_cmds; i++)
                dprintf("  %d, %d, %d\n", cmds[i].motor, cmds[i].duty_cycle, cmds[i].duration);
            continue;
        }
        if (strcmp(cmd, "r") == 0)
        {
            dprintf("run\n");
            run(num_cmds, cmds);
            num_cmds = 0;
            dprintf("drink complete. bottoms up!\n");
            continue;
        }
        if (num_cmds == MAX_CMDS)
        {
            dprintf("Cannot accept more commands.\n");
            continue;
        }

        t = strtok(cmd, ",");
        if (t)
        {
            cmds[num_cmds].motor = atoi(t);
            t = strtok(NULL, ",");
            if (t)
            {
                cmds[num_cmds].duty_cycle = atoi(t);
                t = strtok(NULL, ",");
                if (t)
                {
                    cmds[num_cmds].duration = atol(t);
                    if (cmds[num_cmds].motor >= 0 && cmds[num_cmds].motor <= MAX_MOTORS &&
                        cmds[num_cmds].duty_cycle >= 0 && cmds[num_cmds].duty_cycle <= 255 &&
                        cmds[num_cmds].duration > 0)
                    {
                        dprintf("command stored: %d,%d,%u\n", cmds[num_cmds].motor, cmds[num_cmds].duty_cycle, cmds[num_cmds].duration);
                        num_cmds++;
                        continue;
                    }
                }
            }
        }
        dprintf("invalid command. not stored. fuck you.\n", cmd);
    }


//# m,dc,dur -> 0,100,01000
    
    for(i = 0;; i++)
    {
        OCR0B = 0;
        for(j = 0; j < 5; j++)
            _delay_ms(100);

        OCR0B = 64;
        for(j = 0; j < 5; j++)
            _delay_ms(100);

        OCR0B = 255;
        for(j = 0; j < 5; j++)
            _delay_ms(100);
        OCR0B = 0;


        OCR0A = 0;
        for(j = 0; j < 5; j++)
            _delay_ms(100);

        OCR0A = 64;
        for(j = 0; j < 5; j++)
            _delay_ms(100);

        OCR0A = 255;
        for(j = 0; j < 5; j++)
            _delay_ms(100);
        OCR0A = 0;


        OCR1A = 0;
        for(j = 0; j < 5; j++)
            _delay_ms(100);

        OCR1A = 64;
        for(j = 0; j < 5; j++)
            _delay_ms(100);

        OCR1A = 255;
        for(j = 0; j < 5; j++)
            _delay_ms(100);
        OCR1A = 0;

    }

	return 0;
}
