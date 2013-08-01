#!/usr/bin/env python

from bartendro import app
import logging
import logging.handlers
import os
import memcache
import sys
from bartendro.router import driver
from bartendro import mixer
from bartendro.errors import SerialIOError, I2CIOError
import argparse

LOG_SIZE = 1024 * 500  # 500k maximum log file size
LOG_FILES_SAVED = 3    # number of log files to compress and save


parser = argparse.ArgumentParser(description='Bartendro application process')
parser.add_argument("-d", "--debug", help="Turn on debugging mode to see stack traces in the error log", default=True, action='store_true')
parser.add_argument("-t", "--host", help="Which interfaces to listen on. Default: 127.0.0.1", default="127.0.0.1", type=str)
parser.add_argument("-p", "--port", help="Which port to listen on. Default: 8080", default="8080", type=int)

args = parser.parse_args()
if args.debug: print " * Debugging has been enabled."

try:
    import uwsgi
    have_uwsgi = True
except ImportError:
    have_uwsgi = False
    
class BartendroLock(object):

    def lock_bartendro(self):
        """Call this function before making a drink or doing anything that where two users' action may conflict.
           This function will return True if the lock was granted, of False is someone else has already locked 
           Bartendro."""

        # If we're not running inside uwsgi, then don't try to use the lock
        if not have_uwsgi: return True

        uwsgi.lock()
        is_locked = uwsgi.sharedarea_readbyte(0)
        if is_locked:
           uwsgi.unlock()
           return False
        uwsgi.sharedarea_writebyte(0, 1)
        uwsgi.unlock()

        return True

    def unlock_bartendro(self):
        """Call this function when you've previously locked bartendro and now you want to unlock it."""

        # If we're not running inside uwsgi, then don't try to use the lock
        if not have_uwsgi: return True

        uwsgi.lock()
        is_locked = uwsgi.sharedarea_readbyte(0)
        if not is_locked:
           uwsgi.unlock()
           return False
        uwsgi.sharedarea_writebyte(0, 0)
        uwsgi.unlock()

        return True

def print_software_only_notice():
    print """If you're trying to run this code without having Bartendro hardware,
you can still run the software portion of it in a simulation mode. In this mode no 
communication with the Bartendro hardware will happen to allow the software to run.
To enable this mode, set the BARTENDRO_SOFTWARE_ONLY environment variable to 1 and 
try again:

    > export BARTENDRO_SOFTWARE_ONLY=1

"""

try:
    import config
except ImportError:
    print "You need to create a configuration file called config.py by copying"
    print "config.py.default to config.py . Edit the configuration options in that"
    print "file to tune bartendro to your needs, then start the server again."
    sys.exit(-1)
app.options = config


try: 
    app.software_only = int(os.environ['BARTENDRO_SOFTWARE_ONLY'])
    app.num_dispensers = 15
except KeyError:
    app.software_only = 0

if not os.path.exists("bartendro.db"):
    print "bartendro.db file not found. Please copy bartendro.db.default to "
    print "bartendro.db in order to provide Bartendro with a starting database."
    sys.exit(-1)

# Create a memcache connection and flush everything
app.mc = memcache.Client(['127.0.0.1:11211'], debug=0)
app.mc.flush_all()

# Create the Bartendro lock to prevent multiple people from using it at the same time.
app.lock = BartendroLock()

# Set up logging
if not os.path.exists("logs"):
    os.mkdir("logs")

handler = logging.handlers.RotatingFileHandler(os.path.join("logs", "bartendro.log"), 
                                               maxBytes=LOG_SIZE, 
                                               backupCount=LOG_FILES_SAVED)
logging.basicConfig(format='%(levelname)s: %(message)s', level=logging.INFO)
logger = logging.getLogger('bartendro')
logger.addHandler(handler)

# Start the driver, which talks to the hardware
try:
    app.driver = driver.RouterDriver("/dev/ttyAMA0", app.software_only);
    app.driver.open()
except I2CIOError:
    print
    print "Cannot open I2C interface to a router board."
    print
    print_software_only_notice()
    sys.exit(-1)
except SerialIOError:
    print
    print "Cannot open serial interface to a router board."
    print
    print_software_only_notice()
    sys.exit(-1)

logging.info("Found %d dispensers." % app.driver.count())

app.mixer = mixer.Mixer(app.driver, app.mc)
if app.software_only:
    logging.info("Running SOFTWARE ONLY VERSION. No communication between software and hardware chain will happen!")

logging.info("Bartendro starting")
app.debug = args.debug

if __name__ == '__main__':
    app.run(host=args.host, port=args.port)
