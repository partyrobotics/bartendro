CC=avr-gcc
CFLAGS=-g -Os -Wall -I../include -I../mixer -mcall-prologues -mmcu=atmega168 -DF_CPU=8000000UL
OBJ2HEX=avr-objcopy 
TARGET=dispenser

program: $(TARGET).hex 
	sudo avrdude -p m168 -P usb -c avrispmkII -Uflash:w:$(TARGET).hex -B 1.0

$(TARGET).hex: $(TARGET).obj
	$(OBJ2HEX) -R .eeprom -O ihex $< $@

$(TARGET).obj: $(TARGET).o serial.o led.o pack7.o twimaster.o
	$(CC) $(CFLAGS) -o $@ -Wl,-Map,$(TARGET).map $(TARGET).o serial.o led.o pack7.o twimaster.o

clean:
	rm -f *.hex *.obj *.o *.map
