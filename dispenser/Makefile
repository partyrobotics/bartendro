CC=avr-gcc
CFLAGS=-g -Os -Wall -I../include -I../mixer -mcall-prologues -mmcu=atmega48
OBJ2HEX=avr-objcopy 
TARGET=dispenser

program: $(TARGET).hex 
	sudo avrdude -p m48 -P usb -c avrispmkII -Uflash:w:$(TARGET).hex 

$(TARGET).hex: $(TARGET).obj
	$(OBJ2HEX) -R .eeprom -O ihex $< $@

$(TARGET).obj: $(TARGET).o 
	$(CC) $(CFLAGS) -o $@ -Wl,-Map,$(TARGET).map $(TARGET).o 

clean:
	rm -f *.hex *.obj *.o *.map
