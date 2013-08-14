#!/usr/bin/env python

# The states that Bartendro can be in:
STATE_INIT  = 0   # Bartendro is initializing
STATE_READY = 1   # Bartendro is ready. If liquid levels are enabled all bottles are above low threshold
STATE_LOW   = 2   # If liquid levels are enabled, one or more bottles are low
STATE_OUT   = 3   # If liquid levels are enabled, one or more bottles are out
STATE_ERROR = 4   # Bartendro has encountered some serious problem and can't make shit right now.

try:
    import uwsgi
    have_uwsgi = True
except ImportError:
    have_uwsgi = False
    
class BartendroGlobalLock(object):
    '''This class manages the few global settings that Bartendro needs including a global state and
       a global Bartendro lock to prevent concurrent access to the hardware'''


    def __init__(self):
        self.state = STATE_INIT

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

    def get_state(self):
        '''Get the current state of Bartendro'''

        # If we're not running inside uwsgi, then we can't keep global state
        if not have_uwsgi: return STATE_READY

        uwsgi.lock()
        state = uwsgi.sharedarea_readbyte(1)
        uwsgi.unlock()

        return state

    def set_state(self, state):
        """Set the current state of Bartendro"""

        # If we're not running inside uwsgi, then don't try to use the lock
        if not have_uwsgi: return

        uwsgi.lock()
        uwsgi.sharedarea_writebyte(1, state)
        uwsgi.unlock()

        return True
