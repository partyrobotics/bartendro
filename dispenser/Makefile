CC=avr-gcc
CFLAGS=-g -Os -Wall -I../include -I../mixer -mcall-prologues -mmcu=atmega328 -DF_CPU=8000000UL
OBJ2HEX=avr-objcopy 
TARGET=dispenser

program: $(TARGET).hex 
	./timestamp.py timestamp.raw
	sudo avrdude -p m328p -P usb -c avrispmkII -Uflash:w:$(TARGET).hex -B 1.0
	sudo avrdude -p m328p -P usb -c avrispmkII -U eeprom:w:timestamp.raw:r -B 1.0
	rm -f timestamp.raw

$(TARGET).hex: $(TARGET).obj
	$(OBJ2HEX) -R .eeprom -O ihex $< $@

$(TARGET).obj: $(TARGET).o serial.o led.o pack7.o
	$(CC) $(CFLAGS) -o $@ -Wl,-Map,$(TARGET).map $(TARGET).o serial.o led.o pack7.o

clean:
	rm -f *.hex *.obj *.o *.map
