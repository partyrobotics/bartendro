#!/usr/bin/env python

import sys
import struct
import subprocess
import random
import argparse

random.seed()
parser = argparse.ArgumentParser()
parser.add_argument("file", help="The filename to write the pump id to")
parser.add_argument("id", nargs='?', help="The pump id to write to the file.", type=int, default=random.randint(0, 254))
args = parser.parse_args()

try:
    f = open(args.file, "w")
    f.write(struct.pack("B", args.id))
    f.close()
except IOError, e:
    print "Error: ", e
    sys.exit(-1)

#cmd = "sudo avrdude -p m168 -P usb -c avrispmkII -U eeprom:w:%s:r -B 1.0" % sys.argv[1]
#subprocess.check_output(cmd)
print "Pump id %d written to %s" % (args.id, sys.argv[1])
sys.exit(0)
