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

#define SOFTWARE_VERSION                  4

#define USER_BUTTON_DURATION             10 // in clock ticks
#define RESET_DURATION                    1
#define SYNC_COUNT                       10 // Every SYNC_INIT ms we will change the color animation
#define NUM_ADC_SAMPLES                   5
#define TICKS_SAVE_THRESHOLD           1000
#define DEFAULT_LIQUID_LOW_THRESHOLD    140
#define DEFAULT_LIQUID_OUT_THRESHOLD     90
#define DEFAULT_CURRENT_SENSE_THRESHOLD 610
#define MOTOR_DIRECTION_FORWARD           1
#define MOTOR_DIRECTION_BACKWARD          0

// this (non volatile) variable keeps the current liquid level
static uint16_t g_liquid_level = 0;

volatile uint32_t g_time = 0;
static volatile uint32_t g_reset_fe_time = 0;
static volatile uint32_t g_reset = 0;
static volatile uint32_t g_ticks = 0;
static volatile uint32_t g_dispense_target_ticks = 0;
static volatile uint8_t g_is_dispensing = 0;
static volatile uint8_t g_is_motor_on = 0;
static volatile uint8_t g_motor_direction = MOTOR_DIRECTION_FORWARD;
static volatile uint32_t g_button_time = 0;
static volatile uint8_t g_button_state = 0;

static volatile uint8_t g_hall0 = 0;
static volatile uint8_t g_hall1 = 0;
static volatile uint8_t g_hall2 = 0;
static volatile uint8_t g_hall3 = 0;
static volatile uint8_t g_sync = 0;
static volatile uint32_t g_sync_count = 0, g_pattern_t = 0;
static volatile uint8_t g_sync_divisor = 10;

static volatile uint8_t g_current_sense_detected = 0;
static volatile uint8_t g_current_sense_state = 0;
static volatile uint8_t g_current_sense_enabled = 1;

void check_dispense_complete_isr(void);
void set_motor_speed(uint8_t speed, uint8_t use_current_sense);
void set_motor_direction(uint8_t direction);
void stop_motor(void);
void pulse_motor_driver_retry(void);
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
   5  - PD5 - motor control B (OC0B)
   6  - PD6 - motor control A (OC0A)
   7  - PD7 - Hall 0 (pcint 23)
   8  - PB0 - Hall 1 (pcint 0)
   9  - PB1 - Hall 2 (pcint 1) 
  10  - PB2 - Hall 3 (pcint 2)
  14  - PB6 - /RTRY for motor driver
  15  - PB7 - BUTTON (pcint7)
  A0  - PC0 - Current Sense (since v3 a digital function) (pcint 8)
  A1  - PC1 - liquid level
  A2  - PC2 - REV0
  A3  - PC3 - REV1
  A4  - PC4 - REV2
  A5  - PC5 - SYNC (pcint13)

*/
void setup(void)
{
    serial_init();

    // Set up LEDs & motor control outputs
    DDRD |= (1<<PD3)|(1<<PD4)|(1<<PD5)|(1<<PD6);
    DDRB |= (1<<PB6);

    // pull ups for hall sensors & for current sense
    sbi(PORTD, 7);
    sbi(PORTB, 0);
    sbi(PORTB, 1);
    sbi(PORTB, 2);
    sbi(PORTC, 0);

    // Timer setup for reset pulse width measuring
    TCCR1B |= TIMER1_FLAGS;
    TCNT1 = TIMER1_INIT;
    TIMSK1 |= (1<<TOIE1);

    // Set to Phase correct PWM, compare output mode
    TCCR0A |= _BV(WGM00) | _BV(COM0A1) | _BV(COM0B1);

    // Set the clock source
    TCCR0B |= (0 << CS00) | (1 << CS01);

    // Reset timers and comparators
    OCR0A = 0;
    OCR0B = 0;
    TCNT0 = 0;

    // INT0 for router reset
    EICRA |= (1 << ISC00);
    EIMSK |= (1 << INT0);

    // PCINT setup
    PCMSK0 |= (1 << PCINT0) | (1 << PCINT1) | (1 << PCINT2) | (1 << PCINT7);;
    PCMSK1 |= (1 << PCINT8) | (1 << PCINT13);
    PCMSK2 |= (1 << PCINT23);
    PCICR |=  (1 << PCIE2) | (1 << PCIE1) | (1 << PCIE0);

    // Set the motor driver RTRY line HIGH
    sbi(PORTB, 6);
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
    if (state != g_hall1)
    {
        g_hall1 = state;
        g_ticks++;
    }

    state = PINB & (1<<PINB1);
    if (state != g_hall2)
    {
        g_hall2 = state;
        g_ticks++;
    }
    state = PINB & (1<<PINB2);
    if (state != g_hall3)
    {
        g_hall3 = state;
        g_ticks++;
    }
    state = (PINB & (1<<PINB7)) ? 0 : 1;
    if (state != g_button_state)
    {
        if (!g_button_time)
        {
            g_button_time = g_time + USER_BUTTON_DURATION;
            g_button_state = state;
        }
    }
    check_dispense_complete_isr();
}

ISR(PCINT1_vect)
{
    uint8_t      state;

    state = PINC & (1<<PINC0);
    if (state != g_current_sense_state)
    {
        g_current_sense_state = state;

        if (!state && g_current_sense_enabled)
        {
            stop_motor();
            g_is_dispensing = 0;
            g_dispense_target_ticks = 0;
            set_led_pattern(LED_PATTERN_CURRENT_SENSE);
            g_current_sense_detected = 1;
        }
    }
    state = PINC & (1<<PINC5);
    if (state != g_sync)
    {
        g_sync_count++;
        g_sync = state;
    }
    check_dispense_complete_isr();
}

ISR(PCINT2_vect)
{
    uint8_t state;

    state = PIND & (1<<PIND7);
    if (state != g_hall0)
    {
        g_hall0 = state;
        g_ticks++;
    }

    check_dispense_complete_isr();
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
    uint8_t animate = 0, current_state = 0, button_state_changed = 0;
    uint32_t t = 0;

    cli();
    if (g_sync_count >= g_sync_divisor)
    {
        g_sync_count = 0;
        animate = 1;
    }

    // read button state & check time
    if (g_button_time > 0 && g_time >= g_button_time)
    {
        current_state = g_button_state;
        g_button_time = 0;
        button_state_changed = 1;
    }
    sei();

    // Set the leds and motor speed accordingly when button is pressed
    if (button_state_changed)
    {
        if (current_state)
            set_motor_speed(255, 1);
        else
            set_motor_speed(0, 1);
    }
      
    // run the animation if the current state 
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

void set_motor_direction(uint8_t direction)
{
    if (direction != MOTOR_DIRECTION_FORWARD && direction != MOTOR_DIRECTION_BACKWARD)
        return;

    cli();
    g_motor_direction = direction;
    sei();
}

void set_motor_speed(uint8_t speed, uint8_t use_current_sense)
{
    uint8_t direction;

    cli();
    g_current_sense_enabled = use_current_sense;
    direction = g_motor_direction;
    sei();

    if (direction == MOTOR_DIRECTION_FORWARD)
    {
        OCR0A = speed;
        OCR0B = 0;
    }
    else
    {
        OCR0A = 0;
        OCR0B = speed;
    }

    cli();
    g_is_motor_on = speed != 0;
    sei();
}

void pulse_motor_driver_retry(void)
{
    cbi(PORTB, 6);
    _delay_ms(2);
    sbi(PORTB, 6);
}

void stop_motor(void)
{
    adc_shutdown();
    OCR0A = 0;
    OCR0B = 0;
    cli();
    g_is_motor_on = 0;
    sei();
}

void run_motor_timed(uint16_t duration)
{
    uint16_t t;

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

#define MAX_CMD_LEN 64
// return true is a command was read, false if a reset was requested
uint8_t receive_cmd(char *cmd)
{
    uint8_t num = 0, ch;

    dprint(">");

    *cmd = 0;
    for(; !check_reset();)
    {
        for(;!check_reset() && !serial_rx_nb(&ch);)
            idle();

        if (check_reset())
            return 0;

        serial_tx(ch);
        if (ch == '\r')
        {
            serial_tx('\n');
            cmd[num] = 0;
            return 1;
        }
        cmd[num] = ch;
        num++;
    }
    return 0;
}

void text_interface(void)
{
    char cmd[MAX_CMD_LEN];
    uint8_t  speed, current_sense;
    uint16_t ticks;
    uint16_t t;
    uint8_t  i, cs;

    for(i = 0; i < 5; i++)
    {
        set_led_rgb(0, 0, 255);
        _delay_ms(150);
        set_led_rgb(0, 0, 0);
        _delay_ms(150);
    }
    set_led_pattern(LED_PATTERN_IDLE);
    for(;;)
    {
        cli();
        g_reset = 0;
        g_current_sense_detected = 0;
        setup();
        stop_motor();
        serial_init();
        cs = 0;
        sei();

        _delay_ms(10);
        dprint("\nParty Robotics Dispenser at your service!\n\n");

        for(;;)
        {
            cli();
            cs = g_current_sense_detected;
            sei();
            if (!receive_cmd(cmd))
                break;

            if (sscanf(cmd, "speed %hhu %hhu", &speed, &current_sense) == 2)
            {
                if (!cs)
                    set_motor_speed(speed, current_sense);

                if (current_sense == 0)
                    flush_saved_tick_count(0);
                continue;
            }
            if (sscanf(cmd, "tickdisp %hu %hhu", (short unsigned int *)&ticks, &speed) == 2)
            {
                if (!cs)
                {
                    dispense_ticks(ticks, speed);
                    flush_saved_tick_count(0);
                }
                continue;
            }
            if (sscanf(cmd, "timedisp %hu", (short unsigned int *)&t) == 1)
            {
                if (!cs)
                {
                    run_motor_timed(t);
                    flush_saved_tick_count(0);
                }
                continue;
            }
            if (strncmp(cmd, "forward", 7) == 0)
            {
                set_motor_direction(MOTOR_DIRECTION_FORWARD);
                continue;
            }
            if (strncmp(cmd, "backward", 8) == 0)
            {
                set_motor_direction(MOTOR_DIRECTION_BACKWARD);
                continue;
            }
            if (strncmp(cmd, "led_idle", 8) == 0)
            {
                set_led_pattern(LED_PATTERN_IDLE);
                continue;
            }
            if (strncmp(cmd, "led_dispense", 12) == 0)
            {
                set_led_pattern(LED_PATTERN_DISPENSE);
                continue;
            }
            if (strncmp(cmd, "led_done", 8) == 0)
            {
                set_led_pattern(LED_PATTERN_DRINK_DONE);
                continue;
            }
            if (strncmp(cmd, "led_clean", 8) == 0)
            {
                set_led_pattern(LED_PATTERN_CLEAN);
                continue;
            }
            if (strncmp(cmd, "help", 4) == 0)
            {
                dprint("You can use these commands:\n");
                dprint("  speed <speed> <cs>\n");
                dprint("  tickdisp <ticks> <speed>\n");
                dprint("  timedisp <ms>\n");
                dprint("  forward\n");
                dprint("  backward\n");
                dprint("  reset\n");
                dprint("  led_idle\n");
                dprint("  led_dispense\n");
                dprint("  led_done\n");
                dprint("  led_clean\n\n");
                dprint("speed is from 0 - 255. cs = current sense and is 0 or 1.\n");
                dprint("ticks == number of quarter turns. ms == milliseconds\n");
                continue;
            }
            if (strncmp(cmd, "reset", 5) == 0)
                break;

            dprint("Unknown command. Use help to get, eh help. Duh.\n");
        }
    }
}

uint8_t address_exchange(void)
{
    uint8_t  ch;
    uint8_t  id, text_cmd = 0;

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
        if (ch == '!')
            text_cmd++;
        if (ch == '!' && text_cmd == 3)
            text_interface();
    }

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

void check_software_revision(void)
{
    uint8_t bit0 = PINC & (1<<PINC2) ? 1 : 0;
    uint8_t bit1 = PINC & (1<<PINC3) ? 1 : 0;
    uint8_t bit2 = PINC & (1<<PINC4) ? 1 : 0;

    if ((bit0 | bit1 << 1 | bit2 << 2) == SOFTWARE_VERSION)
        return;

    // Wrong software! I refuse to do shit!
    set_led_rgb(255, 255, 255);
    for(;;)
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

    // Ensure we're running the right software for this board
    check_software_revision();

    // get the current liquid level 
    update_liquid_level();

    for(;;)
    {
        cli();
        g_reset = 0;
        g_current_sense_detected = 0;
        g_motor_direction = MOTOR_DIRECTION_FORWARD;
        setup();
        serial_init();
        stop_motor();
        pulse_motor_driver_retry();
        set_led_rgb(0, 0, 255);

        sei();
        id = address_exchange();

        for(; !check_reset();)
        {
            rec = receive_packet(id, &p);
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

                    case PACKET_GET_VERSION:
                        send_packet8(PACKET_GET_VERSION, SOFTWARE_VERSION);
                        break;

                    case PACKET_SET_MOTOR_SPEED:
                        if (!cs)
                            set_motor_speed(p.p.uint8[0], p.p.uint8[1]);

                        if (p.p.uint8[0] == 0)
                            flush_saved_tick_count(0);
                        break;

                    case PACKET_SET_MOTOR_DIRECTION:
                        if (!cs)
                            set_motor_direction(p.p.uint8[0]);

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
                            run_motor_timed((uint16_t)p.p.uint32);
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
                        // Only for v2 pumps
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
