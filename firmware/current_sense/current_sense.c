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
#include "debug.h"

#define NUM_ADC_SAMPLES 5
#define NUM_CURRENT_SENSE_SAMPLES 10

void set_motor_speed(uint8_t speed);

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

    // Set to Phase correct PWM, compare output mode
    TCCR0A |= _BV(WGM00) | _BV(COM0B1);

    // Set the clock source
    TCCR0B |= (0 << CS00) | (1 << CS01);

    // Reset timers and comparators
    OCR0B = 0;
    TCNT0 = 0;

}

void set_motor_speed(uint8_t speed)
{
    OCR0B = 255 - speed;
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

int main(void)
{
    uint16_t l;

    setup();
    set_motor_speed(0);
    sei();

    dprintf("Starting current sense test\n");
    set_motor_speed(255);
    for(;;)
    {
        l = read_current_sense();
        dprintf("%d\n", l);
        if (l > 500)
        {
            dprintf("Under threshold. stopping\n");
            set_motor_speed(0);
            break;
        }
        _delay_ms(50);
    }
}
