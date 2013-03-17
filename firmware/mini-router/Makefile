CC=avr-gcc
CFLAGS=-g -Os -Wall -I../common -mcall-prologues -mmcu=atmega168 -DF_CPU=8000000UL -DROUTER
OBJ2HEX=avr-objcopy 
TARGET=mini-router

program: $(TARGET).hex 
	sudo avrdude -p m168 -P usb -c avrispmkII -Uflash:w:$(TARGET).hex -B 1.0

$(TARGET).hex: $(TARGET).obj
	$(OBJ2HEX) -R .eeprom -O ihex $< $@

$(TARGET).obj: $(TARGET).o
	make -C ../common
	$(CC) $(CFLAGS) -o $@ -Wl,-Map,$(TARGET).map $(TARGET).o ../common/common.ar

clean:
	rm -f *.hex *.obj *.o *.map
