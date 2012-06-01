#!/usr/bin/env python

# Beagleboard user button
# Copyright 2009 mechomaniac.com
import struct
import sys
import os

def wait_for_button():
	inputDevice = "/dev/input/event0"
	# format of the event structure (int, int, short, short, int)
	inputEventFormat = 'iihhi'
	inputEventSize = 16
	 
	try:
	    file = open(inputDevice, "rb") # standard binary file input
	except IOError:
	    print "Cannot open %s. Are you root?" % inputDevice
	    sys.exit(1)

	event = file.read(inputEventSize)
	while event:
	    (time1, time2, type, code, value) = struct.unpack(inputEventFormat, event)
	    if type == 1 and code == 276 and value == 1:
		file.close()
		return True
	    event = file.read(inputEventSize)

while True:
	wait_for_button()
        os.system("kill -9 `ps x | grep bartendro_server | grep -v grep | cut -d ' ' -f 2`")
