#define F_CPU 8000000UL 
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

#define BAUD 9600
#define UBBR (F_CPU / 16 / BAUD - 1)

uint16_t adc_16b;

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
void adc_init(void){

    //ADCSRA=[ADEN][ADSC][ADATE][ADIF][ADIE][ADPS2][ADPS1][ADPS0] 
	//ADC Enable, ADC Start Conversion, ADC Auto Trigger, ADC Interrupt Flag, ADC Interrupt Enable, ADC Prescaler bits (set sample rate)
    ADCSRA |= (1 << ADEN) | (1 << ADATE)| (1 << ADIE) | (1 << ADPS2) | (1 << ADPS1) | (1 << ADPS0); // Set ADC prescaler to 128 - 125KHz sample rate @ 16MHz 

 	//ADMUX=[REFS1][REFS0][ADLAR][---][MUX3][MUX2][MUX1][MUX0]
	//REF1:0 Set reference voltage, MUX3:0 Set Analog channel to read
    ADMUX &= (0 << ADLAR) & (0 << REFS1); // Right adjust ADC result 
    ADMUX |= (1 << REFS0); // Set ADC reference to AVCC 
 
 	//ADCSRB=[---][ACME][---][---][---][ADTS2][ADTS1][ADTS0]
	//ADC Comparater mode, ADTS2:0 sets auto trigger source 
    ADCSRB &= (0 << ADTS2) & (0 << ADTS1) & (0 << ADTS0);
    
    sei();   // Enable Global Interrupts 
    ADCSRA |= (1 << ADSC);  // Start A2D Conversions 
}

void setup(void)
{
	DDRD |= (1<<PORTD7); //LED pin
    serial_init();
	adc_init();
}
ISR(ADC_vect) 
{ 
	uint16_t adcl_var, adch_var;
	adcl_var = ADCL;
	adch_var = ADCH;
	adc_16b = adch_var  << 8;
	adc_16b |= adcl_var;
} 
int main (void)
{
	uint16_t voltage=0;
	setup();
	while(1){
		PORTD |= (1<<PORTD7);
		dprintf("Raw ADC: %d\n",adc_16b);
		voltage = (adc_16b / 310.303);
		dprintf("Voltage: %f\n", voltage);
		_delay_ms(500);
	}
}