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
#include "led.h"

#if F_CPU == 16000000UL
#define    TIMER1_INIT      0xFFE6
#define    TIMER1_FLAGS     _BV(CS11)|(1<<CS10); // 16Mhz / 64 / 25 = .0001 per tick
#else
#define    TIMER1_INIT      0xFFFC
#define    TIMER1_FLAGS     _BV(CS11)|(1<<CS10); // 8Mhz / 256 / 3 = .000096 per tick
#endif

static volatile uint32_t g_time = 0;
static volatile uint32_t g_reset_fe_time = 0;
static volatile uint32_t g_reset = 0;
static volatile uint32_t g_ticks = 0;
static volatile uint8_t g_hall0 = 0;
static volatile uint8_t g_hall1 = 0;
static volatile uint8_t g_hall2 = 0;
static volatile uint8_t g_hall3 = 0;

// EEprom data 
uint32_t EEMEM _ee_random_number;
uint32_t EEMEM _ee_run_time;

#define RESET_DURATION   1
#define RECEIVE_TIMEOUT  100
#define NUM_ADC_SAMPLES 5

/*
   0  - PD0 - RX
   1  - PD1 - TX
   2  - PD2 - RESET
   3  - PD3 - LED clock
   4  - PD4 - LED data
   5  - PD5 - motor PWM out
   6  - PD6 - Hall 0 (pcint 22)
   7  - PD7 - Hall 1 (pcint 23)
   8  - PB0 - Hall 2 (pcint 1)
   9  - PB1 - Hall 3 (pcint 0) 
  10  - PB2 - SYNC 
  A0  - PA0 - CS
  A1  - PA1 - liquid level

*/
void setup(void)
{
    // Set up LEDs & motor out
    DDRD |= (1<<PD3)|(1<<PD4)|(1<<PD5);

    // Set up on board LED output
    DDRB |= (1<<PB5);

    // pull ups
    sbi(PORTD, 6);
    sbi(PORTD, 7);
    sbi(PORTB, 0);
    sbi(PORTB, 1);

    // Timer setup for reset pulse width measuring
    TCCR1B |= TIMER1_FLAGS;
    TCNT1 = TIMER1_INIT;
    TIMSK1 |= (1<<TOIE1);

    // Set to Phase correct PWM, compare output mode
    TCCR0A |= _BV(WGM00) | _BV(COM0B1);

    // Set the clock source
    TCCR0B |= _BV(CS00) | _BV(CS01);

    // Reset timers and comparators
    OCR0B = 0;
    TCNT0 = 0;

    // INT0 for router reset
    EICRA |= (1 << ISC00);
    EIMSK |= (1 << INT0);

    // PCINT setup
    PCMSK0 |= (1 << PCINT0) | (1 << PCINT1);
    PCMSK2 |= (1 << PCINT22) | (1 << PCINT23);
    PCICR |=  (1 << PCIE2) | (1 << PCIE0);
}

// update g_time
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

ISR(PCINT0_vect)
{
    uint8_t      state;

    state = PINB & (1<<PINB0);
    if (state != g_hall2)
    {
        g_hall2 = state;
        g_ticks++;
    }

    state = PINB & (1<<PINB1);
    if (state != g_hall3)
    {
        g_hall3 = state;
        g_ticks++;
    }
}

ISR(PCINT2_vect)
{
    uint8_t state;

    state = PIND & (1<<PIND6);
    if (state != g_hall0)
    {
        g_hall0 = state;
        g_ticks++;
    }

    state = PIND & (1<<PIND7);
    if (state != g_hall1)
    {
        g_hall1 = state;
        g_ticks++;
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

void serial_tx_check_reset(uint8_t ch)
{
    while ((!( UCSR0A & (1<<UDRE0))) && !check_reset());
    UDR0 = ch;
}

void adc_setup(void)
{
    ADCSRA = (1 << ADPS1);
    ADMUX = (1<<REFS0);
    ADCSRA |= (1<<ADEN);
}

void adc_shutdown(void)
{
    ADCSRA &= ~(1<<ADEN);
}

uint8_t adc_read(uint8_t mux)
{
    uint8_t val, dummy;

    ADMUX = mux;
    ADCSRA |= (1<<ADSC);
    while(ADCSRA & 0b01000000);
    val = ADCL;
    dummy = ADCH;
    ADCSRA &= ~(1<<ADSC);
    return val;
}

uint8_t read_current_sense(void)
{
    uint8_t  i;
    uint16_t v = 0;

    adc_setup();
    for(i = 0; i < NUM_ADC_SAMPLES; i++)
        v += adc_read(MUX0);
    adc_shutdown();

    return (uint8_t)(v / NUM_ADC_SAMPLES);
}

uint8_t read_liquid_level_sensor(void)
{
    uint8_t  i;
    uint16_t v = 0;

    adc_setup();
    for(i = 0; i < NUM_ADC_SAMPLES; i++)
        v += adc_read(MUX1);
    adc_shutdown();

    return (uint8_t)(v / NUM_ADC_SAMPLES);
}

void set_motor_speed(uint8_t speed)
{
    OCR0B = speed;
}

void run_motor_timed(uint32_t duration)
{
    uint32_t t;

    set_led_rgb(255, 0, 255);
    set_motor_speed(128);
    for(t = 0; t < duration && !check_reset(); t++)
        _delay_ms(1);
    set_motor_speed(0);
    set_led_rgb(0, 255, 0);
}

void run_motor_ticks(uint32_t ticks)
{
    uint32_t ticks_dest, ticks_now;

    cli();
    ticks_dest = g_ticks + ticks;
    sei();

    set_led_rgb(255, 0, 255);
    set_motor_speed(255);
    for(; !check_reset();)
    {
        cli();
        ticks_now = g_ticks;
        sei();
        if (ticks_now >= ticks_dest)
            break;
    }
    set_motor_speed(0);
    set_led_rgb(0, 255, 0);
}

void set_random_seed_from_eeprom(void)
{
    uint32_t r;

    eeprom_read_block((void *)&r, &_ee_random_number, sizeof(uint32_t));
    srandom(r);
}

uint8_t send_packet(packet_t *p)
{
    uint16_t crc = 0;
    uint8_t i, *ch = (uint8_t *)p;

    crc = _crc16_update(crc, p->dest);
    crc = _crc16_update(crc, p->type);
    crc = _crc16_update(crc, p->p.uint8[0]);
    crc = _crc16_update(crc, p->p.uint8[1]);
    crc = _crc16_update(crc, p->p.uint8[2]);
    p->crc = _crc16_update(crc, p->p.uint8[3]);
    for(i = 0; i < sizeof(packet_t) && !check_reset(); i++, ch++)
        serial_tx_check_reset(*ch);

    if (check_reset())
        return 0;

    return 1;
}

uint8_t receive_packet(packet_t *p)
{
    uint32_t timeout = 0, now;
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

    set_led_rgb(0, 0, 255);
    receive_packet(&p);

    for(;;)
    {
        rec = receive_packet(&p);
        if (rec == REC_CRC_FAIL)
        {
            set_led_rgb(255, 255, 0);
            continue;
        }
        if (rec == REC_RESET)
            return 0xFF;

        if (p.type == PACKET_ASSIGN_ID)
            break;

        if (p.p.uint8[0] == id)
        {
            sbi(PORTD, 1);
            _delay_ms(RESET_DURATION + RESET_DURATION);
            cbi(PORTD, 1);
        }
    }

    // We haven't processed the previous packet yet
    for(;;)
    {
        if (p.type == PACKET_ASSIGN_ID && p.dest == id)
                break;

        rec = receive_packet(&p);
        if (rec == REC_CRC_FAIL)
        {
            set_led_rgb(255, 255, 0);
            for(;!check_reset();)
                ;
            return 0xFF;
        }
        if (rec == REC_RESET)
            return 0xFF;
    }
    id = p.p.uint8[0];
    set_led_rgb(0, 0, 255);

    for(;;)
    {
        rec = receive_packet(&p);
        if (rec == REC_CRC_FAIL)
        {
            set_led_rgb(255, 255, 0);
            for(;!check_reset();)
                ;
            return 0xFF;
        }
        if (rec == REC_RESET)
        {
            return 0xFF;
        }

        if (p.type == PACKET_START)
            break;
    }
    set_led_rgb(0, 255, 0);

    serial_enable(1, 1);

    return id;
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
    uint8_t id, rec;
    packet_t p;

    for(;;)
    {
        cli();
        g_reset = 0;

        setup();
        flash_led(1);
        serial_init();
        set_led_rgb(0, 0, 0);

        sei();

        id = get_address();
        if (id == 0xFF)
            continue;


        for(; !check_reset();)
        {
            rec = receive_packet(&p);
            if (rec == REC_CRC_FAIL)
            {
                set_led_rgb(255, 255, 0);
                continue;
            }

            if (rec == REC_RESET)
                break;

            if (rec == REC_OK && p.dest == id)
            {
                switch(p.type)
                {
                    case PACKET_SET_MOTOR_SPEED:
                        set_motor_speed(p.p.uint8[0]);
                        break;
                    case PACKET_TICK_DISPENSE:
                        run_motor_ticks(p.p.uint32);
                        break;
                    case PACKET_TIME_DISPENSE:
                        run_motor_timed(p.p.uint32);
                        break;
                }
            }
        }
    }
    return 0;
}
