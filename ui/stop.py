#!/usr/bin/env python

import os
import sys
import time
from optparse import OptionParser
from bartendro.master import driver

driver = driver.MasterDriver("/dev/ttyS1", True);
driver.open()
driver.chain_init();
