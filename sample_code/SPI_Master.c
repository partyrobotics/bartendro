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

void SPI_MasterInit(void)
{
	// Set SS, MOSI and SCK as outputs [MISO is PB4]
	DDRB = (1<<PORTB2)|(1<<PORTB3)|(1<<PORTB5); 

	//SPCR = [SPIE][SPE][DORD][MSTR][CPOL][CPHA][SPR1][SPR0]
	//SPI Control Register = Interrupt Enable, Enable, Data Order, Master/Slave select, Clock Polarity, Clock Phase, Clock Rate
	SPCR = (1<<SPE)|(1<<MSTR)|(1<<SPR0);	// Enable SPI, Master, set clock rate fck/16 
}

void SPI_MasterTransmit(char cData)
{
	/* Start transmission */
	PORTB = ~(1<<PORTB2);
	SPDR = cData;
	/* Wait for transmission complete */
	while(!(SPSR & (1<<SPIF)))
	;
}

void setup(void)
{
	DDRD |= (1<<PORTD7); //LED pin
    serial_init();
	SPI_MasterInit();
}

int main (void)
{
	uint8_t num=0;
	setup();
	while(1){
		//PORTD |= (1<<PORTD7);
		SPI_MasterTransmit(num);
		dprintf("sent: %d\n",num);
		/*voltage = (adc_16b / 310.303);
		dprintf("Voltage: %f\n", voltage);*/
		_delay_ms(500);
		num++;
	}
}
