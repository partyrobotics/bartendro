#define F_CPU 16000000UL 
#include <avr/io.h>
#include <stdlib.h>
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

// Bit manipulation macros
#define sbi(a, b) ((a) |= 1 << (b))       //sets bit B in variable A
#define cbi(a, b) ((a) &= ~(1 << (b)))    //clears bit B in variable A
#define tbi(a, b) ((a) ^= 1 << (b))       //toggles bit B in variable A

#define max(a, b) ((a) > (b) ? (a) : (b))
#define min(a, b) ((a) < (b) ? (a) : (b))

#define RESET_DURATION   100
#define RECEIVE_TIMEOUT  100
#define TIMER1_INIT      0xFFE6

volatile uint32_t g_time = 0;
volatile uint32_t g_hall0_fe_time = 0;
volatile uint32_t g_hall1_fe_time = 0;
volatile uint32_t g_hall2_fe_time = 0;
volatile uint32_t g_hall3_fe_time = 0;

volatile uint8_t g_hall0 = 0;
volatile uint8_t g_hall1 = 0;
volatile uint8_t g_hall2 = 0;
volatile uint8_t g_hall3 = 0;

volatile uint8_t  pcint18 = 0;
volatile uint8_t  pcint19 = 0;
volatile uint8_t  pcint20 = 0;
volatile uint8_t  pcint21 = 0;

#define HALL_DURATION 100 //ms
#define BAUD 38400
#define UBBR (F_CPU / 16 / BAUD - 1)

ISR (TIMER1_OVF_vect)
{
    g_time++;
    TCNT1 = TIMER1_INIT;
}

ISR(PCINT2_vect)
{
    uint8_t      state;

    state = PIND & (1<<PIND2);
    if (state != pcint18)
    {
        if (state)
            g_hall0_fe_time = g_time + HALL_DURATION;
        else
        {
            if (g_hall0_fe_time > 0 && g_time >= g_hall0_fe_time)
            {
                tbi(PORTB, 5);
                g_hall0 = 1;
            }
            g_hall0_fe_time = 0;
        }
        pcint18 = state;
    }
    state = PIND & (1<<PIND3);
    if (state != pcint19)
    {
        if (state)
            g_hall1_fe_time = g_time + HALL_DURATION;
        else
        {
            if (g_hall1_fe_time > 0 && g_time >= g_hall1_fe_time)
                g_hall1 = 1;
            g_hall1_fe_time = 0;
        }
        pcint19 = state;
    }
    state = PIND & (1<<PIND4);
    if (state != pcint20)
    {
        if (state)
            g_hall2_fe_time = g_time + HALL_DURATION;
        else
        {
            if (g_hall2_fe_time > 0 && g_time >= g_hall2_fe_time)
                g_hall2 = 1;
            g_hall2_fe_time = 0;
        }
        pcint20 = state;
    }
    state = PIND & (1<<PIND5);
    if (state != pcint21)
    {
        if (state)
            g_hall3_fe_time = g_time + HALL_DURATION;
        else
        {
            if (g_hall3_fe_time > 0 && g_time >= g_hall3_fe_time)
                g_hall3 = 1;
            g_hall3_fe_time = 0;
        }
        pcint21 = state;
    }
}

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
    DDRB |= (1 << PORTB5);
    DDRD |= (1 << PORTD7);

    // Timer setup for reset pulse width measuring
    TCCR1B |= _BV(CS11)|(1<<CS10); // clock / 64 / 25 = .0001 per tick
    TCNT1 = TIMER1_INIT;
    TIMSK1 |= (1<<TOIE1);

    // PCINT setup
    PCMSK2 |= (1 << PCINT18) | (1 << PCINT19) | (1 << PCINT20) | (1 << PCINT21) ;
    PCICR |=  (1 << PCIE2);

    // pull ups
    sbi(PORTD, 2);
    sbi(PORTD, 3);
    sbi(PORTD, 4);
    sbi(PORTD, 5);
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

int main (void)
{
    uint8_t h0, h1, h2, h3;
    uint8_t last_h0 = 0, last_h1 = 0, last_h2 = 0, last_h3 = 0;
    uint32_t t, last_t = 0;

    setup();
    flash_led(1);
    serial_init();

    dprintf("encoder test!\n");
    sei();
    for(;;)
    {
        cli();
        h0 = g_hall0;
        h1 = g_hall1;
        h2 = g_hall2;
        h3 = g_hall3;
        t = g_time;
        g_hall0 = g_hall1 = g_hall2 = g_hall3 = 0; 
        sei();

        if (h0 != last_h0 || h1 != last_h1 || h2 != last_h2 || h3 != last_h3)
        {
            dprintf("%06ld, %05ld: %d %d %d %d\n", t, t - last_t, h0, h1, h2, h3);
            last_t = t;
        }

        last_h0 = h0;
        last_h1 = h1;
        last_h2 = h2;
        last_h3 = h3;
        _delay_ms(1);
    }
    return 0;
}
