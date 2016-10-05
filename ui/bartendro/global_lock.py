#!/usr/bin/env python

from bartendro import fsm
from bartendro.error import BartendroBusyError

try:
    import uwsgi
    have_uwsgi = True
except ImportError:
    have_uwsgi = False

class BartendroLock(object):
    def __init__(self, globals):
        self.globals = globals

    def __enter__(self):
        if not self.globals.lock_bartendro():
            raise BartendroBusyError("Bartendro is busy dispensing")

    def __exit__(self, type, value, traceback):
        self.globals.unlock_bartendro()
    
class BartendroGlobalLock(object):
    '''This class manages the few global settings that Bartendro needs including a global state and
       a global Bartendro lock to prevent concurrent access to the hardware'''


    def __init__(self):
        self.state = fsm.STATE_START

    def lock_bartendro(self):
        """Call this function before making a drink or doing anything that where two users' action may conflict.
           This function will return True if the lock was granted, of False is someone else has already locked 
           Bartendro."""

        # If we're not running inside uwsgi, then don't try to use the lock
        if not have_uwsgi: return True

        uwsgi.lock()
        is_locked = uwsgi.sharedarea_read8(0, 0)
        if is_locked:
           uwsgi.unlock()
           return False
        uwsgi.sharedarea_write8(0, 0, 1)
        uwsgi.unlock()

        return True

    def unlock_bartendro(self):
        """Call this function when you've previously locked bartendro and now you want to unlock it."""

        # If we're not running inside uwsgi, then don't try to use the lock
        if not have_uwsgi: return True

        uwsgi.lock()
        is_locked = uwsgi.sharedarea_read8(0, 0)
        if not is_locked:
           uwsgi.unlock()
           return False
        uwsgi.sharedarea_write8(0, 0, 0)
        uwsgi.unlock()

        return True

    def get_state(self):
        '''Get the current state of Bartendro'''

        # If we're not running inside uwsgi, then we can't keep global state
        if not have_uwsgi: return self.state

        uwsgi.lock()
        state = uwsgi.sharedarea_read8(0, 1)
        uwsgi.unlock()

        return state

    def set_state(self, state):
        """Set the current state of Bartendro"""

        # If we're not running inside uwsgi, then don't try to use the lock
        if not have_uwsgi: 
            self.state = state
            return

        uwsgi.lock()
        uwsgi.sharedarea_write8(0, 1, state)
        uwsgi.unlock()

        return True
