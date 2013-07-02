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

// EEprom data. 
#define ee_pump_id_offset                 0
#define ee_run_time_ticks_offset          1
#define ee_liquid_low_threshold_offset    5
#define ee_liquid_out_threshold_offset    7 

#define RESET_DURATION                    1
#define SYNC_COUNT                       10 // Every SYNC_INIT ms we will change the color animation
#define NUM_ADC_SAMPLES                   5
#define MAX_CURRENT_SENSE_CYCLES         10
#define TICKS_SAVE_THRESHOLD           1000
#define DEFAULT_LIQUID_LOW_THRESHOLD    140
#define DEFAULT_LIQUID_OUT_THRESHOLD     90
#define DEFAULT_CURRENT_SENSE_THRESHOLD 610

// this (non volatile) variable keeps the current liquid level
static uint16_t g_liquid_level = 0;

volatile uint32_t g_time = 0;
static volatile uint32_t g_reset_fe_time = 0;
static volatile uint32_t g_reset = 0;
static volatile uint32_t g_ticks = 0;
static volatile uint32_t g_dispense_target_ticks = 0;
static volatile uint8_t g_is_dispensing = 0;
static volatile uint8_t g_is_motor_on = 0;

static volatile uint8_t g_hall0 = 0;
static volatile uint8_t g_hall1 = 0;
static volatile uint8_t g_hall2 = 0;
static volatile uint8_t g_hall3 = 0;
static volatile uint8_t g_sync = 0;
static volatile uint32_t g_sync_count = 0, g_pattern_t = 0;
static volatile uint8_t g_sync_divisor = 10;

static uint8_t  g_current_sense_num_cycles = 0;
static uint16_t g_current_sense_threshold = DEFAULT_CURRENT_SENSE_THRESHOLD;
static volatile uint8_t g_current_sense_detected = 0;

void check_dispense_complete_isr(void);
void set_motor_speed(uint8_t speed, uint8_t use_current_sense);
void stop_motor(void);
void adc_shutdown(void);
uint8_t check_reset(void);
void is_dispensing(void);
void flush_saved_tick_count(uint8_t force);
void set_led_pattern(uint8_t pattern);

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
    serial_init();

    // Set up LEDs & motor out
    DDRD |= (1<<PD3)|(1<<PD4)|(1<<PD5);

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
    check_dispense_complete_isr();

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
    check_dispense_complete_isr();
}

ISR(ADC_vect)
{
    uint8_t low, hi;
    uint16_t data;

    low = ADCL;
    hi = ADCH;
    data = (hi << 8) | low;

    if (data >= g_current_sense_threshold)
        g_current_sense_num_cycles++;

    if (g_current_sense_num_cycles >= MAX_CURRENT_SENSE_CYCLES)
    {
        stop_motor();
        g_is_dispensing = 0;
        g_dispense_target_ticks = 0;
        set_led_pattern(LED_PATTERN_CURRENT_SENSE);
        g_current_sense_detected = 1;
    }

    // If we're still dispensing, then start another ADC conversion
    if (g_is_dispensing || g_is_motor_on)
        ADCSRA |= (1<<ADSC);
}

// this function is called from an ISR, so no need to turn off/on interrupts
void check_dispense_complete_isr(void)
{
    if (g_dispense_target_ticks > 0 && g_ticks >= g_dispense_target_ticks)
    {
         g_dispense_target_ticks = 0;
         g_is_dispensing = 0;
         stop_motor();
         adc_shutdown();
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
    if (g_sync_count >= g_sync_divisor)
    {
        g_sync_count = 0;
        animate = 1;
    }
    sei();

    if (animate)
    {
        cli();
        t = g_pattern_t++;
        sei();
        // do some animation!
        led_pattern_next(t, &c);
        set_led_rgb(c.red, c.green, c.blue);
    }

    flush_saved_tick_count(0);
}

void flush_saved_tick_count(uint8_t force)
{
    uint8_t is_dispensing;
    uint32_t ticks_to_save;

    cli();
    is_dispensing = g_is_dispensing;
    ticks_to_save = g_ticks;
    sei();

    if (is_dispensing && !force)
        return;

    if (ticks_to_save > TICKS_SAVE_THRESHOLD || (force && ticks_to_save > 0))
    {
        cli();
        g_ticks = 0;
        sei();

        ticks_to_save += eeprom_read_dword((uint32_t *)ee_run_time_ticks_offset);
        eeprom_update_dword((uint32_t *)ee_run_time_ticks_offset, ticks_to_save);
    }
}

void reset_saved_tick_count(void)
{
    uint32_t dispensing;

    // Don't reset the tick count while we're counting!
    cli();
    dispensing = g_is_dispensing;
    sei();
    if (dispensing)
        return;

    cli();
    g_ticks = 0;
    sei();

    eeprom_update_dword((uint32_t *)ee_run_time_ticks_offset, 0);
}

void get_saved_tick_count(void)
{
    uint32_t ticks;

    cli();
    ticks = g_ticks;
    sei();

    send_packet16(PACKET_SAVED_TICK_COUNT, ticks + eeprom_read_dword((uint32_t *)ee_run_time_ticks_offset), 0);
}

void get_liquid_thresholds(void)
{
    uint16_t low, out;

    low = eeprom_read_word((uint16_t *)ee_liquid_low_threshold_offset);
    out = eeprom_read_word((uint16_t *)ee_liquid_out_threshold_offset);

    if (low == 0 || low == 0xFFFF)
        low = DEFAULT_LIQUID_LOW_THRESHOLD; 

    if (out == 0 || out == 0xFFFF)
        out = DEFAULT_LIQUID_OUT_THRESHOLD;

    send_packet16(PACKET_GET_LIQUID_THRESHOLDS, low, out);
}

void set_liquid_thresholds(uint16_t low, uint16_t out)
{
    eeprom_update_word((uint16_t *)ee_liquid_low_threshold_offset, low);
    eeprom_update_word((uint16_t *)ee_liquid_out_threshold_offset, out);
}

void set_led_pattern(uint8_t pattern)
{
    led_pattern_init(pattern);
    cli();
    g_pattern_t = 0;
    sei();
}

void adc_current_sense_start(void)
{
    // Set up ADC conversion with interrupt enable
    ADCSRA = (1 << ADPS0) | (1 << ADPS1) | (1 << ADPS2) | (1 << ADIE);
    ADMUX = (1<<REFS0) | (0 << REFS1);
    ADCSRA |= (1<<ADEN);

    // Start a conversion
    ADCSRA |= (1<<ADSC);
}

void adc_liquid_level_setup(void)
{
    ADCSRA = (1 << ADPS1);
    ADMUX = (1<<REFS0) | (1 << MUX0);
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

void update_liquid_level(void)
{
    uint8_t  i;
    uint16_t v = 0;

    adc_liquid_level_setup();
    for(i = 0; i < NUM_ADC_SAMPLES; i++)
        v += adc_read();
    adc_shutdown();

    g_liquid_level = (uint16_t)(v / NUM_ADC_SAMPLES);
}

void get_liquid_level(void)
{
    send_packet16(PACKET_LIQUID_LEVEL, g_liquid_level, 0);
}

void set_motor_speed(uint8_t speed, uint8_t use_current_sense)
{
    if (use_current_sense)
        adc_current_sense_start();

    OCR0B = 255 - speed;

    cli();
    g_is_motor_on = speed != 0;
    sei();
}

void stop_motor(void)
{
    adc_shutdown();
    OCR0B = 255;
    cli();
    g_is_motor_on = 0;
    sei();
}

void run_motor_timed(uint32_t duration)
{
    uint32_t t;

    if (duration == 0)
        return;

    set_motor_speed(255, 1);
    for(t = 0; t < duration && !check_reset(); t++)
        _delay_ms(1);
    stop_motor();
}

void dispense_ticks(uint32_t ticks, uint16_t speed)
{
    uint8_t dispensing;

    cli();
    dispensing = g_is_dispensing;
    sei();

    if (dispensing || ticks == 0)
        return;

    cli();
    g_dispense_target_ticks = g_ticks + ticks;
    g_is_dispensing = 1;
    sei();

    set_motor_speed(speed, 1);
}

void is_dispensing(void)
{
    uint8_t dispensing;

    cli();
    dispensing = g_is_dispensing;
    sei();

    send_packet8_2(PACKET_IS_DISPENSING, dispensing, g_current_sense_detected);
}

uint8_t address_exchange(void)
{
    uint8_t  ch;
    uint8_t  id;

    set_led_rgb(0, 0, 255);
    id = eeprom_read_byte((uint8_t *)ee_pump_id_offset);
    if (id == 0 || id == 255)
    {
        // we failed to get a unique number for the pump. just stop.
        set_led_rgb(255, 0, 0);
        for(;;);
    }

    for(;;)
    {
        for(;;)
        {
            if (serial_rx_nb(&ch))
                break;

            if (check_reset())
                return 0xFF;
        }
        if (ch == 0xFF)
            break;
        if (ch == '?')
            serial_tx(id);
    }
    set_led_rgb(0, 255, 0);

    return id;
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

void id_conflict(void)
{
    // we failed to get an address. stop and wait for a reset
    set_led_rgb(255, 0, 0);
    for(; !check_reset();)
        ;
}

int main(void)
{
    uint8_t  id, rec, i, cs;
    color_t  c;
    packet_t p;

    setup();
    stop_motor();
    sei();
    for(i = 0; i < 5; i++)
    {
        set_led_rgb(255, 0, 255);
        _delay_ms(50);
        set_led_rgb(255, 255, 0);
        _delay_ms(50);
    }

    // get the current liquid level 
    update_liquid_level();

    for(;;)
    {
        cli();
        g_reset = 0;
        g_current_sense_detected = 0;
        g_current_sense_num_cycles = 0;
        setup();
        serial_init();
        stop_motor();
        set_led_rgb(0, 0, 255);

        sei();
        id = address_exchange();

        for(; !check_reset();)
        {
            rec = receive_packet(&p);
            if (rec == COMM_CRC_FAIL)
                continue;

            if (rec == COMM_RESET)
                break;

            if (rec == COMM_OK && (p.dest == DEST_BROADCAST || p.dest == id))
            {
                // If we've detected a over current sitatuion, ignore all comamnds until reset
                cli();
                cs = g_current_sense_detected;
                sei();

                switch(p.type)
                {
                    case PACKET_PING:
                        break;

                    case PACKET_SET_MOTOR_SPEED:
                        if (!cs)
                            set_motor_speed(p.p.uint8[0], p.p.uint8[1]);

                        if (p.p.uint8[0] == 0)
                            flush_saved_tick_count(0);
                        break;

                    case PACKET_TICK_DISPENSE:
                        if (!cs)
                        {
                            dispense_ticks((uint16_t)p.p.uint32, 255);
                            flush_saved_tick_count(0);
                        }
                        break;

                    case PACKET_TIME_DISPENSE:
                        if (!cs)
                        {
                            run_motor_timed(p.p.uint32);
                            flush_saved_tick_count(0);
                        }
                        break;

                    case PACKET_IS_DISPENSING:
                        is_dispensing();
                        break;

                    case PACKET_LIQUID_LEVEL:
                        get_liquid_level();
                        break;

                    case PACKET_UPDATE_LIQUID_LEVEL:
                        update_liquid_level();
                        break;

                    case PACKET_LED_OFF:
                        set_led_pattern(LED_PATTERN_OFF);
                        break;

                    case PACKET_LED_IDLE:
                        if (!cs)
                            set_led_pattern(LED_PATTERN_IDLE);
                        break;

                    case PACKET_LED_DISPENSE:
                        if (!cs)
                            set_led_pattern(LED_PATTERN_DISPENSE);
                        break;

                    case PACKET_LED_DRINK_DONE:
                        if (!cs)
                            set_led_pattern(LED_PATTERN_DRINK_DONE);
                        break;

                    case PACKET_LED_CLEAN:
                        if (!cs)
                            set_led_pattern(LED_PATTERN_CLEAN);
                        break;

                    case PACKET_COMM_TEST:
                        comm_test();
                        break;

                    case PACKET_ID_CONFLICT:
                        id_conflict();
                        break;

                    case PACKET_SET_CS_THRESHOLD:
                        g_current_sense_threshold = p.p.uint16[0];
                        break;

                    case PACKET_SAVED_TICK_COUNT:
                        get_saved_tick_count();
                        break;

                    case PACKET_RESET_SAVED_TICK_COUNT:
                        reset_saved_tick_count();
                        break;

                    case PACKET_FLUSH_SAVED_TICK_COUNT:
                        flush_saved_tick_count(1);
                        break;

                    case PACKET_GET_LIQUID_THRESHOLDS:
                        get_liquid_thresholds();
                        break;

                    case PACKET_SET_LIQUID_THRESHOLDS:
                        set_liquid_thresholds(p.p.uint16[0], p.p.uint16[1]);
                        break;

                    case PACKET_TICK_SPEED_DISPENSE:
                        if (!cs)
                        {
                            dispense_ticks(p.p.uint16[0], (uint8_t)p.p.uint16[1]);
                            flush_saved_tick_count(0);
                        }
                        break;
                    case PACKET_PATTERN_DEFINE:
                        pattern_define(p.p.uint8[0]);
                        break;

                    case PACKET_PATTERN_ADD_SEGMENT:
                        c.red = p.p.uint8[0];
                        c.green = p.p.uint8[1];
                        c.blue = p.p.uint8[2];
                        pattern_add_segment(&c, p.p.uint8[3]);
                        break;

                    case PACKET_PATTERN_FINISH:
                        pattern_finish();
                        break;
                }
            }
        }
    }
    return 0;
}
