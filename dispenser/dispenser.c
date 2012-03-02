#define PRO_MINI_5V
#ifdef PRO_MINI_5V
   #define F_CPU 16000000UL 
#else 
   #define F_CPU  8000000UL 
#endif

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

#include "../master/packet.h"

// Bit manipulation macros
#define sbi(a, b) ((a) |= 1 << (b))       //sets bit B in variable A
#define cbi(a, b) ((a) &= ~(1 << (b)))    //clears bit B in variable A
#define tbi(a, b) ((a) ^= 1 << (b))       //toggles bit B in variable A

#define BAUD 38400
#define UBBR (F_CPU / 16 / BAUD - 1)
#define DEBUG 0

static uint8_t g_address = 0xFF;

static volatile uint8_t g_is_dispensing = 0;
static volatile uint8_t g_rx = 0;
static volatile uint8_t g_reset = 0;
static volatile uint32_t g_hall_sensor_1 = 0;
static volatile uint32_t g_hall_sensor_2 = 0;
static volatile uint32_t g_dispense_target = 0;

uint8_t set_motor_state(uint8_t state);
#if DEBUG
void dprintf(const char *fmt, ...);
#endif

ISR (USART_RX_vect)
{
    g_rx = 1;
}

ISR(PCINT0_vect)
{
    if (PINB & (1<<PINB2))
        g_reset = 1;
    else
        g_reset = 0;
}

// encoder ISR
ISR(PCINT1_vect)
{
    if (PINC & (1<<PINC0))
        g_hall_sensor_1++;
    if (PINC & (1<<PINC1))
        g_hall_sensor_2++;

    if (g_dispense_target > 0 && g_hall_sensor_1 >= g_dispense_target)
    {
        g_dispense_target = 0;
        set_motor_state(0);
    }
}

uint8_t is_dispensing()
{
    uint8_t cur;

    cli();
    cur = g_is_dispensing;
    sei();

    return cur;
}

uint8_t set_motor_state(uint8_t state)
{
    uint8_t cur;

    cur = is_dispensing();
    if (cur == state)
        return 0;

    if (state)
    {
        cli();
        g_is_dispensing = 1;
        sei();
        sbi(PORTB, 1);
    }
    else
    {
        cli();
        g_is_dispensing = 0;
        sei();
        cbi(PORTB, 1);
    }
    return 1;
}
void dispense(uint32_t ticks)
{
    // Check to make sure we're not already dispensing
    if (is_dispensing())
        return;

    cli();
    g_dispense_target = g_hall_sensor_1 + ticks;
    sei();
#if DEBUG
    dprintf("dispense target: %d\n", g_dispense_target);
#endif

    // Turn the motor on and get moving!
    set_motor_state(1);
} 

#if DEBUG
void test()
{
    uint8_t disp;
    uint32_t cur;

    dispense(30000);
    for(;;)
    {
        cli();
        cur = g_hall_sensor_1;
        disp = g_is_dispensing;
        sei();

        dprintf("ticks: %ld is_disp: %d\n", cur, disp);

        if (!g_is_dispensing)
            break;
    }
    dprintf("Done dispensing\n");
}
#endif

void serial_init(void)
{
    /*Set baud rate */ 
    UBRR0H = (unsigned char)(UBBR>>8); 
    UBRR0L = (unsigned char)UBBR; 
    /* Enable transmitter */ 
    UCSR0B = (1<<TXEN0) | (1<<RXEN0) | (1<<RXCIE0);
    /* Set frame format: 8data, 1stop bit */ 
    UCSR0C = (0<<USBS0)|(3<<UCSZ00); 
}
uint8_t serial_tx(uint8_t ch)
{
    uint8_t reset;

    while ( !( UCSR0A & (1<<UDRE0)) )
    {
        cli();
        reset = g_reset;
        sei();
        if (reset)
            return 0;
    }
    UDR0 = ch;
    return 1;
}

#if DEBUG
#define MAX 80 

// debugging printf function. Max MAX characters per line!!
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
#endif

uint8_t serial_rx_block(void)
{
    while ( !(UCSR0A & (1<<RXC0))) 
          ;
        
    return UDR0;
}
uint8_t serial_rx(uint8_t *ch)
{
    uint8_t rx;

    cli();
    rx = g_rx;
    sei();

    if (!rx)
        return 0;

    *ch = UDR0;

    cli();
    g_rx = 0;
    sei();

    return 1;
}

void setup(void)
{
    // Set LED PWM pins as outputs
    DDRD |= (1<<PD6)|(1<<PD5)|(1<<PD3)|(1<<PD4)|(1<<PD7);

    // Set Motor pin as output
    DDRB |= (1<<PB1) | (1<<PB0);

    // Motor driver pins
    // pin 4 high = /STANDBY
    // pin 7 high = IN1
    // pin 8 low = IN2
    sbi(PORTD, 4);
    sbi(PORTD, 7);
    cbi(PORTB, 0);

    // External interrupts for the reset line
    PCMSK0 |= (1<<PCINT2);
    PCICR |= (1<<PCIE0);

    // External interrupts for the hall sensors on the motor`
    PCMSK1 |= (1<<PCINT8)|(1<<PCINT9);
    PCICR |= (1<<PCIE1);

    serial_init();
}

void led_pwm_setup(void)
{
	/* Set to Phase correct PWM */
	TCCR0A |= _BV(WGM00);
	TCCR2A |= _BV(WGM20);

	// Set the compare output mode
	TCCR0A |= _BV(COM0A1);
	TCCR0A |= _BV(COM0B1);
	TCCR2A |= _BV(COM2B1);

	// Reset timers and comparators
	OCR0A = 0;
	OCR0B = 0;
	OCR2B = 0;
	TCNT0 = 0;
	TCNT2 = 0;

    // Set the clock source
	TCCR0B |= _BV(CS00) | _BV(CS01);
	TCCR2B |= _BV(CS22);
}

void set_led_color(uint8_t red, uint8_t green, uint8_t blue)
{
    OCR2B = 255 - red;
    OCR0A = 255 - green;
    OCR0B = 255 - blue;
}

void set_led_red(uint8_t v)
{
    OCR2B = 255 - v;
}

void set_led_green(uint8_t v)
{
    OCR0A = 255 - v;
}

void set_led_blue(uint8_t v)
{
    OCR0B = 255 - v;
}


void wait_for_reset()
{
    uint8_t count = 0, reset, t = 1;

    for(;;)
    {
        cli();
        reset = g_reset;
        sei();
        if (!reset)
        {
            _delay_ms(1);
            count++;
        }
        else
            break;
        if (count == 100)
        {
           set_led_color(t * 255, 0, 0);
           t = !t;
           count = 0;
        }
    }
    set_led_color(0, 0, 0);
}

#define MAX_ADDR_CMD_LEN 40
void address_assignment(void)
{
    char    cmd[MAX_ADDR_CMD_LEN], *p;
    uint8_t ch, i;
   
    cmd[0] = 0;
    for(i = 0; i < MAX_ADDR_CMD_LEN - 1; i++)
    {
        while(!serial_rx(&ch));
        if (ch == '\n')
            break;
        cmd[i] = (char)ch;
        cmd[i + 1] = 0;
    }
    g_address = atoi(cmd);

    sprintf(cmd, "%d\n", g_address + 1);
    for(p = cmd; *p; p++)
        while(!serial_tx((uint8_t)*p));
}

#define BROADCAST_ADDR 255

void handle_cmd(char *line)
{
    uint8_t ret;
    int     addr;
    uint32_t arg1, arg2, arg3;
    char cmd[32];
    char resp[32], *r;

    resp[0] = 0;

    // ignore responses from other dispensers
    if (line[0] == '!')
       return;

    ret = sscanf(line, "%d %s %ld %ld %ld", &addr, cmd, &arg1, &arg2, &arg3);
    if (ret < 2)
        return;
  
    // We allow LED commands to be broadcast. Everything else needs to be done per address
    if ((addr == g_address || addr == BROADCAST_ADDR) && strcmp(cmd, "led") == 0 && ret == 5)
    {
        set_led_color((uint8_t)arg1, (uint8_t)arg2, (uint8_t)arg3);
        return;
    }

    // If this cmd isn't for us, skip it!
    if (addr != g_address)
        return;

    if (strcmp(cmd, "on") == 0)
    {
        set_motor_state(1);
    }
    else
    if (strcmp(cmd, "off") == 0)
    {
        set_motor_state(0);
    }
    else
    if (strcmp(cmd, "disp") == 0 && ret == 3)
    {
        dispense(arg1);
    }
    else
    if (strcmp(cmd, "isdisp") == 0)
    {
        uint8_t state = is_dispensing();
        sprintf(resp, "!%d isdisp %d\n", addr, state);
    }
    else
    if (strcmp(cmd, "ping") == 0)
    {
        sprintf(resp, "!%d pong\n", addr);
    }
    for(r = resp; *r; r++)
        serial_tx(*r);
}

#define MAX_CMD_LEN 80
int main(void)
{
    uint8_t reset = 0, ch;
    char    cmd[MAX_CMD_LEN], *ptr;

    setup();
    // turn the motor off, just in case
    cbi(PORTB, 1);

    led_pwm_setup();
    sei();
//    test();

    wait_for_reset();
    for(;;)
    {
        reset = 0;
        set_led_color(0, 0, 255);
        address_assignment();
        set_led_color(0, 255, 0);
        _delay_ms(500);
        set_led_color(0, 0, 0);

        for(;!reset;)
        {
            ptr = cmd;
            *ptr = 0;
            for(;;)
            {
                cli();
                reset = g_reset;
                sei();
                if (reset)
                    break;
                if (!serial_rx(&ch))
                    continue;
                if (!serial_tx(ch))
                {
                    reset = 1;
                    break;
                }

                *ptr = ch;
                ptr++;
                *ptr = 0;
                if (ch == '\n')
                {
                    handle_cmd(cmd);
                    break;
                }
                // Are we about to overflow our buffer? Shouldn't happen, but if it does, ditch it.
                if (ptr - cmd == MAX_CMD_LEN - 1)
                {
                    ptr = cmd;
                    *ptr = 0;
                }
            }
            if (reset)
            {
                // If we get a reset, turn off timer, turn off motor
                TIMSK1 &= ~(1<<TOIE1);
                set_motor_state(0);
            }
        }
    }
}
