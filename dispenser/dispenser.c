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
#include "led.h"

#if F_CPU == 16000000UL
#define    TIMER1_INIT      0xFFEF
#define    TIMER1_FLAGS     _BV(CS12)|(1<<CS10); // 16Mhz / 1024 / 16 = .001024 per tick
#else
#define    TIMER1_INIT      0xFFF7
#define    TIMER1_FLAGS     _BV(CS12)|(1<<CS10); // 8Mhz / 1024 / 8 = .001024 per tick
#endif

// TODO
// Hook up more LED patterns.
// Start with no patterns, sync off. Let bot start animations.
// Add support for different animation speeds

// Production TODO:
// Hook up more RX pins
// Move Sync to different pin

// EEprom data 
uint32_t EEMEM _ee_random_number;
uint32_t EEMEM _ee_run_time;

#define RESET_DURATION  1
#define SYNC_COUNT      10 // Every SYNC_INIT ms we will change the color animation
#define NUM_ADC_SAMPLES 5
#define NUM_CURRENT_SENSE_SAMPLES 10

volatile uint32_t g_time = 0;
static volatile uint32_t g_reset_fe_time = 0;
static volatile uint32_t g_reset = 0;
static volatile uint32_t g_ticks = 0;
static volatile uint8_t g_hall0 = 0;
static volatile uint8_t g_hall1 = 0;
static volatile uint8_t g_hall2 = 0;
static volatile uint8_t g_hall3 = 0;
static volatile uint8_t g_sync = 0;
static volatile uint32_t g_sync_count = 0, g_pattern_t = 0;
static void (*g_led_function)(uint32_t, color_t *);

/*
   0  - PD0 - RX
   1  - PD1 - TX
   2  - PD2 - RESET
   3  - PD3 - LED clock
   4  - PD4 - LED data
   5  - PD5 - motor PWM out
   6  - PD6 - Hall 0 (pcint 22)
   7  - PD7 - Hall 1 (pcint 23)
   8  - PB0 - Hall 2 (pcint 0)
   9  - PB1 - Hall 3 (pcint 1) 
  10  - PB2 - SYNC (pcint 2)
  A0  - PC0 - CS
  A1  - PC1 - liquid level

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
    TCCR0B |= (0 << CS00) | (1 << CS01);

    // Reset timers and comparators
    OCR0B = 0;
    TCNT0 = 0;

    // INT0 for router reset
    EICRA |= (1 << ISC00);
    EIMSK |= (1 << INT0);

    // PCINT setup
    PCMSK0 |= (1 << PCINT0) | (1 << PCINT1) | (1 << PCINT2);
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

    state = PINB & (1<<PINB2);
    if (state != g_sync)
    {
        g_sync_count++;
        g_sync = state;
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

void idle(void)
{
    color_t c;
    uint8_t animate = 0;
    uint32_t t = 0;

    cli();
    if (g_sync_count >= SYNC_COUNT)
    {
        g_sync_count = 0;
        animate = 1;
    }
    sei();

    if (animate && g_led_function)
    {
        cli();
        t = g_pattern_t++;
        sei();
        // do some animation!
        (*g_led_function)(t, &c);
        set_led_rgb_no_delay(c.red, c.green, c.blue);
    }
}

void set_led_pattern(void (*func)(uint32_t, color_t *))
{
    if (func == NULL)
        set_led_rgb(0, 0, 0);

    g_led_function = func;
}

void adc_liquid_level_setup(void)
{
    ADCSRA = (1 << ADPS1);
    ADMUX = (1<<REFS0) | (1 << MUX0);
    ADCSRA |= (1<<ADEN);
}

void adc_current_sense_setup(void)
{
    ADCSRA = (1 << ADPS0) | (1 << ADPS1) | (1 << ADPS2);
    ADMUX = (1<<REFS0) | (0 << REFS1);
    ADCSRA |= (1<<ADEN);
}

void adc_shutdown(void)
{
    ADCSRA &= ~(1<<ADEN);
}

uint16_t adc_read()
{
    uint8_t hi, low;

    ADCSRA |= (1<<ADSC);
    while(ADCSRA & 0b01000000);
    low = ADCL;
    hi = ADCH;
    return (hi << 8) | low;
}

uint16_t read_current_sense(void)
{
    uint8_t  i;
    uint16_t v = 0;

    adc_current_sense_setup();
    for(i = 0; i < NUM_CURRENT_SENSE_SAMPLES; i++)
        v += adc_read();
    adc_shutdown();

    return (uint16_t)(v / NUM_CURRENT_SENSE_SAMPLES);
}

uint16_t read_liquid_level_sensor(void)
{
    uint8_t  i;
    uint16_t v = 0;

    adc_liquid_level_setup();
    for(i = 0; i < NUM_ADC_SAMPLES; i++)
        v += adc_read();
    adc_shutdown();

    return (uint16_t)(v / NUM_ADC_SAMPLES);
}

void set_motor_speed(uint8_t speed)
{
    OCR0B = 255 - speed;
}

void run_motor_timed(uint32_t duration)
{
    uint32_t t;

    set_motor_speed(255);
    for(t = 0; t < duration && !check_reset(); t++)
        _delay_ms(1);
    set_motor_speed(0);
}

void run_motor_ticks(uint32_t ticks)
{
    uint32_t ticks_dest, ticks_now;

    cli();
    ticks_dest = g_ticks + ticks;
    sei();

    set_motor_speed(255);
    for(; !check_reset();)
    {
        cli();
        ticks_now = g_ticks;
        sei();
        if (ticks_now >= ticks_dest)
            break;

        idle();
    }
    set_motor_speed(0);
}

void set_random_seed_from_eeprom(void)
{
    uint32_t r;

    eeprom_read_block((void *)&r, &_ee_random_number, sizeof(uint32_t));
    srandom(r);
}

uint8_t get_address(void)
{
    uint8_t  ch;
    uint8_t  id, old_id, new_id, my_new_id = 255;

    set_random_seed_from_eeprom();

    // turn off serial TX and set the TX line to output
    serial_enable(1, 0);
    DDRD |= (1 << PORTD1);

    // Pick a random 8-bit number
    id = random() % 255;

    set_led_rgb(0, 0, 255);
    for(;;)
    {
        for(;;)
        {
            if (serial_rx_nb(&ch))
                break;
            if (check_reset())
                return 0xFF;
        }

        if (ch == id)
        {
            sbi(PORTD, 1);
            _delay_ms(RESET_DURATION + RESET_DURATION);
            cbi(PORTD, 1);
        }
        if (ch == 255)
            break;
    }
    for(;;)
    {
        for(;;)
        {
            if (serial_rx_nb(&old_id))
                break;
            if (check_reset())
                return 0xFF;
        }
        if (old_id == 0xFF)
            break;

        for(;;)
        {
            if (serial_rx_nb(&new_id))
                break;
            if (check_reset())
                return 0xFF;
        }
        if (id == old_id)
            my_new_id = new_id;
    }
    if (my_new_id == 0xFF || my_new_id > 14 || my_new_id == id)
        set_led_rgb(255, 0, 0);
    else
        set_led_rgb(0, 255, 0);

    // Switch to using sending serial data
    serial_enable(1, 1);

    return my_new_id;
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

void comm_test(void)
{
    uint8_t ch;

    // disable all interrupts and just echo every character received.
    cli();
    set_led_rgb(0, 255, 255);
    for(; !check_reset();)
        if (serial_rx_nb(&ch))
            for(; !serial_tx_nb(ch) && !check_reset();)
                ;
    sei();
}

int main(void)
{
    uint8_t id, rec;
    packet_t p;

    for(;;)
    {
        cli();
        g_reset = 0;

        setup();
        set_motor_speed(0);
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
                continue;

            if (rec == REC_RESET)
                break;

            if (rec == REC_OK && p.dest == id)
            {
                tbi(PORTB, 5);
                switch(p.type)
                {
                    case PACKET_PING:
                        set_led_rgb(0, 0, 255);
                        _delay_ms(200);
                        set_led_rgb(0, 255, 0);
                        break;
                    case PACKET_SET_MOTOR_SPEED:
                        set_motor_speed(p.p.uint8[0]);
                        break;

                    case PACKET_TICK_DISPENSE:
                        run_motor_ticks(p.p.uint32);
                        break;

                    case PACKET_TIME_DISPENSE:
                        run_motor_timed(p.p.uint32);
                        break;

                    case PACKET_LED_OFF:
                        set_led_pattern(NULL);
                        break;

                    case PACKET_LED_IDLE:
                        set_led_pattern(led_pattern_idle);
                        break;

                    case PACKET_LED_DISPENSE:
                        set_led_pattern(led_pattern_dispense);
                        break;

                    case PACKET_LED_DRINK_DONE:
                        set_led_pattern(led_pattern_drink_done);
                        break;

                    case PACKET_COMM_TEST:
                        comm_test();
                        break;
                }
            }
        }
    }
    return 0;
}
