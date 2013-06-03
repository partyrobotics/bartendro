CC=avr-gcc
CFLAGS=-g -Os -Wall -I../common -mcall-prologues -mmcu=atmega168 -DF_CPU=8000000UL
OBJ2HEX=avr-objcopy 
TARGET=dispenser

program: $(TARGET).hex 
	sudo avrdude -p m168 -P usb -c avrispmkII -Uflash:w:$(TARGET).hex -B 1.0

fuses:
	sudo avrdude -p m168 -P usb -c avrispmkII -U lfuse:w:0xe2:m -U hfuse:w:0xd7:m -U efuse:w:0x03:m -B 8

dispenser: fuses program
	/bin/true

$(TARGET).hex: $(TARGET).obj
	$(OBJ2HEX) -R .eeprom -O ihex $< $@

$(TARGET).obj: $(TARGET).o led.o 
	make -C ../common
	$(CC) $(CFLAGS) -o $@ -Wl,-Map,$(TARGET).map $(TARGET).o led.o ../common/common.ar

clean:
	rm -f *.hex *.obj *.o *.map
