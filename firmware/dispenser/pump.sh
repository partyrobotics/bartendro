#!/bin/sh

./pump_id.py id.raw $1
sudo avrdude -p m168 -P usb -c usbtiny -U eeprom:w:id.raw:r -B 1.0
rm -f id.raw
