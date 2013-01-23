#!/usr/bin/env python

import sys
import time
import struct

if len(sys.argv) != 2:
    print "%s <output file>\n" % (sys.argv[0])
    sys.exit(-1)

try:
    f = open(sys.argv[1], "w")
    t = int(time.time())
    f.write(struct.pack("<I", t))
    f.close()
except IOError, e:
    print "Error: ", e
    sys.exit(-1)

print "Timestamp %d written to %s" % (t, sys.argv[1])
sys.exit(0)
