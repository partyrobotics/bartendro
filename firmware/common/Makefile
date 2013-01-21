CC=avr-gcc
AR=avr-ar
CFLAGS=-g -Os -Wall -mcall-prologues -mmcu=atmega168 -DF_CPU=8000000UL
ARFLAGS=r
TARGET=common

$(TARGET).ar: $(TARGET).ar serial.o pack7.o
	avr-ar $(ARFLAGS) $(TARGET).ar serial.o pack7.o

clean:
	rm -f *.hex *.obj *.o *.map *.ar
