#!/usr/bin/env python

from bartendro import app
import logging
import os
import memcache
from bartendro.router import driver
from bartendro import mixer

try: 
    app.software_only = int(os.environ['BARTENDRO_SOFTWARE_ONLY'])
    app.num_dispensers = 15
except KeyError:
    app.software_only = 0

# Create a memcache connection and flush everything
app.mc = memcache.Client(['127.0.0.1:11211'], debug=0)
app.mc.flush_all()

app.log = logging.getLogger('bartendro')

app.driver = driver.RouterDriver("/dev/ttyAMA0", app.software_only);
app.driver.open()
app.log.info("Found %d dispensers." % app.driver.count())

app.mixer = mixer.Mixer(app.driver, app.mc)

if app.software_only:
    app.log.info("Running SOFTWARE ONLY VERSION. No communication between software and hardware chain will happen!")

app.log.info("Bartendro starting")

app.run(host='0.0.0.0', port=8080)
