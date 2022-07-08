#!/usr/bin/env python

import os
import memcache
import sys
import logging
import logging.handlers
import argparse
import subprocess
from time import sleep
from bartendro import app
from bartendro.router import driver

parser = argparse.ArgumentParser()
parser.add_argument('--ll', help="Test liquid level sensor", dest='ll',action='store_true')
parser.add_argument('--no-ll', help="Don't test liquid level sensor", dest='ll',action='store_false')
parser.set_defaults(ll=True)
args = parser.parse_args()

def test(ll):
    try:
        subprocess.check_call(["make", "-C", "../firmware/dispenser", "dispenser"])
    except subprocess.CalledProcessError:
        print("Failed to program dispenser!")
        sys.exit(-1)

    sleep(1)

    dt = driver.RouterDriver("/dev/ttyAMA0", False)
    dt.open()
    sleep(.1)
    if dt.ping(0):
        print( "ping ok")
    else:
        print( "ping failed")
        sys.exit(-1)

    dt.set_motor_direction(0, driver.MOTOR_DIRECTION_FORWARD)

    print("timed forward")
    if not dt.dispense_time(0, 950):
        print( "timed dispense forward failed.")
        sys.exit(-1)

    sleep(1.5)

    dt.set_motor_direction(0, driver.MOTOR_DIRECTION_BACKWARD)

    print( "ticks backward")
    if not dt.dispense_ticks(0, 24):
        print( "ticks dispense backward failed.")
        sys.exit(-1)
    sleep(1.5)

    dt.set_motor_direction(0, driver.MOTOR_DIRECTION_FORWARD)

    print("ticks forward")
    if not dt.dispense_ticks(0, 24):
        print( "tick dispense forward failed.")
        sys.exit(-1)
    sleep(1.5)

    dt.set_motor_direction(0, driver.MOTOR_DIRECTION_BACKWARD)

    print( "time backward")
    if not dt.dispense_time(0, 950):
        print("timed dispense backward failed.")
        sys.exit(-1)
    sleep(1.5)

    dt.set_motor_direction(0, driver.MOTOR_DIRECTION_FORWARD)

    if ll:
        while True:
            line = raw_input("Press Enter to check the liquid level sensor. Type 'q' to move on to the next dispenser... ")
            if line == 'q':
                break

            if not dt.update_liquid_levels():
                print("updating liquid levels failed.")
                sys.exit(-1)

            sleep(.1)
           
            ll = dt.get_liquid_level(0)
            if ll < 0:
                print( "updating liquid levels failed.")
                sys.exit(-1)

            print( "Current level: %d" % ll)
                    
    print( "All tests passed!")
    print()
    print()

while True:
    test(args.ll)

    line = raw_input("Press Enter to program/test the next dispenser.... Type 'q' to exit.")
    if line == 'q':
        break

sys.exit(0)
