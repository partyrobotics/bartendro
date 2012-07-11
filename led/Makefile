CC=avr-gcc
CFLAGS=-g -Os -Wall -mcall-prologues -mmcu=atmega328p -D F_CPU=16000000UL
OBJ2HEX=avr-objcopy 
TARGET=main

program: $(TARGET).hex 
	sudo avrdude -p m328p -P usb -c avrispmkII -Uflash:w:$(TARGET).hex -B 1.0

$(TARGET).hex: $(TARGET).obj
	$(OBJ2HEX) -R .eeprom -O ihex $< $@

$(TARGET).obj: $(TARGET).o hue.o 
	$(CC) $(CFLAGS) -o $@ -Wl,-Map,$(TARGET).map $(TARGET).o hue.o -lm

clean:
	rm -f *.hex *.obj *.o *.map
