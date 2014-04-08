# -*- coding: utf-8 -*-
import logging

log = logging.getLogger('bartendro')

class BartendroBusyError(Exception):
    def __init__(self, err):
        self.err = err
    def __str__(self):
        return repr(self.err)

class BartendroBrokenError(Exception):
    def __init__(self, err):
        self.err = err
    def __str__(self):
        return repr(self.err)

class BartendroCantPourError(Exception):
    def __init__(self, err):
        self.err = err
    def __str__(self):
        return repr(self.err)

class BartendroCurrentSenseError(Exception):
    def __init__(self, err):
        self.err = err
    def __str__(self):
        return repr(self.err)

class BartendroLiquidLevelReadError(Exception):
    def __init__(self, err):
        self.err = err
    def __str__(self):
        return repr(self.err)

class I2CIOError(Exception):
    pass

class SerialIOError(Exception):
    pass
