CC=avr-gcc
CFLAGS=-g -Os -Wall -I../include -I../mixer -mcall-prologues -mmcu=atmega168 -D F_CPU=16000000UL
OBJ2HEX=avr-objcopy 
TARGET=motor-driver

program: $(TARGET).hex 
	sudo avrdude -p m168 -P usb -c avrispmkII -Uflash:w:$(TARGET).hex -B 1.0

$(TARGET).hex: $(TARGET).obj
	$(OBJ2HEX) -R .eeprom -O ihex $< $@

$(TARGET).obj: $(TARGET).o debug.o
	$(CC) $(CFLAGS) -o $@ -Wl,-Map,$(TARGET).map $(TARGET).o debug.o

clean:
	rm -f *.hex *.obj *.o *.map
