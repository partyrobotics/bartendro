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

#ifdef PRO_MINI_5V
#define TIMER1_INIT 0xFF06 // 16mhz / 64 cs / 250 = 1ms per 'tick'
#else 
#define TIMER1_INIT 0xFF06 // 8mhz / 8 cs / 1000 = 1ms per 'tick'
#endif

static uint8_t g_address = 0xFF;
static uint8_t g_response_payload[2] = { 0, 0};
static uint8_t g_motor_state = 0;

static volatile uint8_t g_spi_ch_in = 0;
static volatile uint8_t g_spi_ch_out = 0;
static volatile uint8_t g_spi_char_received = 0;
static volatile uint8_t g_ss_reset = 0;
static volatile uint8_t g_hall_sensor_1 = 0;
static volatile uint8_t g_hall_sensor_2 = 0;

uint8_t set_motor_state(uint8_t state);

#define DEBUG 1

ISR(SPI_STC_vect)
{
    g_spi_ch_in = SPDR;
    SPDR = g_spi_ch_out;
    g_spi_char_received = 1;
}

ISR(PCINT0_vect)
{
    if (PINB & (1<<PINB2))
        g_ss_reset = 1;
    else
        g_ss_reset = 0;
}

ISR(PCINT1_vect)
{
    if (PINC & (1<<PINC0))
        g_hall_sensor_1++;
    if (PINC & (1<<PINC1))
        g_hall_sensor_2++;
}

// clock globals
volatile uint32_t ticks = 0;
volatile uint8_t  motor_state = 0;
volatile uint16_t dispense_ticks = 0;
volatile uint8_t  dispense_chunks = 0;

#define DISPENSE_TICKS  700
#define DISPENSE_DELAY 1000

ISR (TIMER1_OVF_vect)
{
    if (ticks == 0)
    {
        if (motor_state)
            set_motor_state(0);

        if (dispense_chunks == 0)
        {
            TIMSK1 &= ~(1<<TOIE1);
            return;
        }

        if (motor_state)
        {
            ticks = DISPENSE_DELAY;
            motor_state = 0;
        }
        else
        {
            ticks = dispense_ticks;
            dispense_chunks--;
            
            set_motor_state(1);
            motor_state = 1;
        }
        TCNT1 = TIMER1_INIT;
        return;
    }

    ticks--;
    TCNT1 = TIMER1_INIT;
}

void set_timer(uint16_t dur)
{
    dispense_chunks = (dur + DISPENSE_TICKS - 1) / DISPENSE_TICKS;
    dispense_ticks = (dur + dispense_chunks - 1) / dispense_chunks;

    dispense_chunks--;

    ticks = dispense_ticks;
    TCNT1 = TIMER1_INIT;
    set_motor_state(1);
    motor_state = 1;
    TIMSK1 |= (1<<TOIE1);
}

void stop_timer(void)
{
    cli();
    TIMSK1 &= ~(1<<TOIE1);
    ticks = 0;
    dispense_chunks = 0;
    sei();
}

void serial_init(void)
{
    /*Set baud rate */ 
    UBRR0H = (unsigned char)(UBBR>>8); 
    UBRR0L = (unsigned char)UBBR; 
    /* Enable transmitter */ 
    UCSR0B = (1<<TXEN0); 
    /* Set frame format: 8data, 1stop bit */ 
    UCSR0C = (0<<USBS0)|(3<<UCSZ00); 
}
void serial_tx(unsigned char ch)
{
    while ( !( UCSR0A & (1<<UDRE0)) );
    UDR0 = ch;
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

void spi_slave_init(void)
{
	// Set MISO as output 
	DDRB |= (1<<PB4);
	SPCR = (1<<SPE);//|(1<<SPIE);	// Enable SPI
}

void spi_slave_stop(void)
{
	SPCR &= ~((1<<SPE)|(1<<SPIE));	// Disable SPI
}

uint8_t spi_transfer_int(uint8_t tx)
{
    uint8_t rec, reset, ch;

    cli();
    g_spi_ch_out = tx;
    sei();

    for(;;)
    {
        cli();
        reset = g_ss_reset;
        rec = g_spi_char_received;
        sei();

        if (reset)
            return 0;

        if (rec)
            break;
    }

    cli();
    g_spi_char_received = 0;
    ch = g_spi_ch_in;
    sei();
    return ch;
}

uint8_t spi_transfer(uint8_t tx)
{
    uint8_t reset = 0;

    SPDR = tx;
	/* Wait for reception complete */
	while(!(SPSR & (1<<SPIF)) && !reset)
    {
        cli();
        reset = g_ss_reset;
        sei();
    }
	/* Return Data Register */
	return SPDR;
}

uint8_t receive_packet(packet *rx)
{
    static uint8_t ch = 0;
    uint8_t *prx = (uint8_t*)rx;
    uint8_t received = 0, old, reset = 0;

    for(; received < sizeof(packet);)
    {
        cli();
        reset = g_ss_reset;
        sei();
        if (reset)
            return 0;

        old = ch;
        ch = spi_transfer(ch);

        // Look for the packet header
        if (prx == (uint8_t*)rx && ch != 0xFF)
            continue;


        *prx = ch;
        prx++;
        received++;

        if (received == 5 && rx->type == PACKET_TYPE_RESPONSE)
            ch = g_response_payload[0];
        if (received == 6 && rx->type == PACKET_TYPE_RESPONSE)
            ch = g_response_payload[1];
    }
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

    // Timer setup for dispense timing
    TCCR1B |= _BV(CS11)|(1<<CS10); // clock / 64 / 256 = 244Hz = .001024 per tick

#if DEBUG
    serial_init();
#endif
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
    OCR0A = 255 - blue;
    OCR0B = 255 - green;
}

void set_led_red(uint8_t v)
{
    OCR2B = 255 - v;
}

void set_led_green(uint8_t v)
{
    OCR0B = 255 - v;
}

void set_led_blue(uint8_t v)
{
    OCR0A = 255 - v;
}

uint8_t set_motor_state(uint8_t state)
{
    uint8_t cur;

    cli();
    cur = g_motor_state;
    sei();

    if (cur == state)
        return 0;

    if (state)
    {
        cli();
        g_motor_state = 1;
        sei();
        sbi(PORTB, 1);
    }
    else
    {
        cli();
        g_motor_state = 0;
        sei();
        cbi(PORTB, 1);
    }
    return 1;
}

void test(void)
{
    uint8_t ch = 0;

    for(;;)
    {
        ch = spi_transfer(ch);
        dprintf("%x\n", ch);
    }
}

void wait_for_reset()
{
    uint8_t count = 0, reset, t = 1;

#if DEBUG
    dprintf("waiting for reset\n");
#endif
    for(;;)
    {
        cli();
        reset = g_ss_reset;
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

void address_assignment(void)
{
    uint8_t ch = 0;

    for(;;)
    {
        ch = spi_transfer(ch);
        if (ch > 0 && ch < 0xff)
        {
            g_address = ch;
            ch++;
            spi_transfer(ch);
            break;
        }
    }

#if DEBUG
    dprintf("got address: %d\n", g_address);
#endif
}

void print_packet(packet *p)
{
    uint8_t *pp = (uint8_t *)p, i;

    for(i = 0; i < sizeof(packet); i++, pp++)
        dprintf("%02x ", *pp);
    dprintf("\n");
}

int main(void)
{
    packet  p;
    uint8_t i;

	setup();
    // turn the motor off, just in case
    cbi(PORTB, 1);

    led_pwm_setup();

#if DEBUG
    dprintf("slave starting\n");
#endif
    sei();

    wait_for_reset();
	spi_slave_init();
    address_assignment();

    set_led_color(0, 0, 0);

    for(;;)
    {
        if (!receive_packet(&p))
        {
#if DEBUG
            dprintf("got reset notice!\n");
#endif
            // If SS went high, reset and start over
            stop_timer();
            spi_slave_stop();
            set_motor_state(0);
            g_address = 0;
            wait_for_reset();
            spi_slave_init();
            address_assignment();
            continue;
        }
        print_packet(&p);

        // If we have no address yet, ignore all packets
        if (g_address == 0)
        {
#if DEBUG
            dprintf("ignore packet\n");
#endif
            continue;
        }

        if (p.addr != g_address)
            continue;
        if (p.type == PACKET_TYPE_START)
        {
            uint8_t r;

            r = set_motor_state(1);
#if DEBUG
            if (r)
                dprintf("turn on\n");
            else
                dprintf("already on!\n");
#endif
        }
        else
        if (p.type == PACKET_TYPE_CHECK)
        {
            g_response_payload[0] = 0;
            g_response_payload[1] = 0;
        }
        else
        if (p.type == PACKET_TYPE_GETSTATE)
        {
            cli();
            g_response_payload[0] = g_motor_state;
            sei();
            g_response_payload[1] = 0;
        }
        else
        if (p.type == PACKET_TYPE_SETLED)
        {
            if (p.payload.ch[0] == 0)
                set_led_red(p.payload.ch[1]);
            if (p.payload.ch[0] == 1)
                set_led_green(p.payload.ch[1]);
            if (p.payload.ch[0] == 2)
                set_led_blue(p.payload.ch[1]);
        }
        else
        if (p.type == PACKET_TYPE_RESPONSE)
        {
            ;
        }
        else
        if (p.type == PACKET_TYPE_STOP)
        {
            set_motor_state(0);
        }
        else
        if (p.type == PACKET_TYPE_DISPENSE)
        {
            uint16_t temp;
            cli();
            temp = p.payload.word;
            sei();
            set_timer(temp);
#if DEBUG
            dprintf("turn on for %d ms\n", p.payload.word);
#endif
        }
#if DEBUG
        else
        {
            uint8_t *pp = (uint8_t *)&p;

            dprintf("bad packet: ");
            for(i = 0; i < sizeof(packet); i++, pp++)
                dprintf("%02x ", *pp);
            dprintf("\n");
        }
#endif
    }
}
