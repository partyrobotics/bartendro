#!/usr/bin/env python

import sys
import struct
import subprocess
import random
import argparse
import errno

PUMP_ID_FILE = "last_pump_id.txt"

def get_random_pump_id():
    random.seed()
    return random.randint(0, 254)

def get_pump_id():

    # Get a random id, just in case.
    id = get_random_pump_id()
    id_file = None

    # now try and see if we've got a saved pump id. If so, increment by one and save it
    try:
        id_file = open(PUMP_ID_FILE, "r")
        id = int(id_file.readline().strip()) + 1
    except IOError:
        pass
    except ValueError:
        print "Warning: Cannot read saved pump id. Try removing file %s " % PUMP_ID_FILE

    if id_file:
        id_file.close()

    try:
        id_file = open(PUMP_ID_FILE, "w")
        id_file.write("%d\n" % id)
    except IOError:
        print "Failed to save pump id to %s" % PUMP_ID_FILE

    if id_file:
        id_file.close()

    return id

parser = argparse.ArgumentParser()
parser.add_argument("file", help="The filename to write the pump id to")
parser.add_argument("id", nargs='?', help="The pump id to write to the file.", type=int, default=-1)
args = parser.parse_args()

if args.id < 0:
    id = get_pump_id()
else:
    id = args.id

try:
    f = open(args.file, "a")
    f.write(struct.pack("B", id))
    f.close()
except IOError, e:
    print "Error: ", e
    sys.exit(-1)

#cmd = "sudo avrdude -p m168 -P usb -c avrispmkII -U eeprom:w:%s:r -B 1.0" % sys.argv[1]
#subprocess.check_output(cmd)
print "Pump id %x written to %s" % (id, sys.argv[1])
sys.exit(0)
