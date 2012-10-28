#!/usr/bin/env python

import os
import time
from optparse import OptionParser
from bartendro.master import driver

MAX_NUM_PUMPS = 15

parser = OptionParser()
parser.add_option("-p", "--pumps", action="store", type="string", dest="pumps", default="1,2,3,4,5,6,7,8,9,10,11,12,13,14,15",
                  help="Command separated list of pumps to run. NO SPACES ARE ALLOWED IN THIS LIST!", metavar="FILE")
parser.add_option("-r", "--run", action="store", type="int", dest="run", default="60",
                  help="run the pumps for this many seconds")
parser.add_option("-w", "--wait", action="store", type="int", dest="wait", default="60",
                  help="pause the pumps for for at least this many seconds")
parser.add_option("-c", "--count", action="store", type="int", dest="count", default="3",
                  help="the number of pumps to run simulteanously")
parser.add_option("-t", "--times", action="store", type="int", dest="times", default="1",
                  help="how many times to repeat this cleaning cycle")

(options, args) = parser.parse_args()

options = vars(options)
times = options['times']
run_time = int(options['run'])
wait_time = int(options['wait'])
count = int(options['count'])
pumps = options['pumps'].replace(' ', '').split(',')
pumps = [int(p) for p in pumps]

driver = driver.MasterDriver("/dev/ttyS1", True);
driver.open()
driver.chain_init();

print "Found %s dispensers. I hope that is right!" % driver.count()

for t in xrange(times):
    print "pass %d:" % t
    steps = int(round((len(pumps) + .5) / count))
    for step in xrange(steps):
        for offset in xrange(count):
            pump = ((step * count) + offset)
            if pump >= len(pumps): break
            print "  pump %d on" % pumps[pump]
            driver.start(pumps[pump]-1)

        time.sleep(run_time) 

        for offset in xrange(count):
            pump = ((step * count) + offset)
            if pump >= len(pumps): break
            print "  pump %d off" % pumps[pump]
            driver.stop(pumps[pump]-1)
        print
             
        time.sleep(wait_time) 
