#!/usr/bin/env python

import sys
import struct
import subprocess

if len(sys.argv) != 3:
    print "%s <output file> <id>\n" % (sys.argv[0])
    sys.exit(-1)

id = int(sys.argv[2])
try:
    f = open(sys.argv[1], "w")
    f.write(struct.pack("b", id))
    f.close()
except IOError, e:
    print "Error: ", e
    sys.exit(-1)

#cmd = "sudo avrdude -p m168 -P usb -c avrispmkII -U eeprom:w:%s:r -B 1.0" % sys.argv[1]
#subprocess.check_output(cmd)
print "Pump id %d written to %s" % (id, sys.argv[1])
sys.exit(0)
