#!/usr/bin/env python

import os
import sys
import time
from optparse import OptionParser
from bartendro.master import driver

driver = driver.MasterDriver("/dev/ttyACM0", True);
driver.open()
