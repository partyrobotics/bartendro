CC=avr-gcc
CFLAGS=-g -Os -Wall -I../include -I../mixer -mcall-prologues -mmcu=atmega328p -DF_CPU=8000000UL
OBJ2HEX=avr-objcopy 
TARGET=master

program: $(TARGET).hex 
	sudo avrdude -p m328p -P usb -c avrispmkII -Uflash:w:$(TARGET).hex -B 1.0

$(TARGET).hex: $(TARGET).obj
	$(OBJ2HEX) -R .eeprom -O ihex $< $@

$(TARGET).obj: $(TARGET).o serial.o
	$(CC) $(CFLAGS) -o $@ -Wl,-Map,$(TARGET).map $(TARGET).o serial.o

clean:
	rm -f *.hex *.obj *.o *.map
