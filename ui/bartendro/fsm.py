# States that Bartendro can be in
STATE_CHECK =         1
STATE_READY =         2
STATE_LOW =           3
STATE_OUT =           4
STATE_HARD_OUT =      5
STATE_PRE_POUR =      6
STATE_POURING  =      7
STATE_POUR_DONE =     8
STATE_CURRENT_SENSE = 9
STATE_ERROR =         10

# Events that cause changes in Bartendro states
EVENT_LL_OK =          1
EVENT_LL_LOW =         2
EVENT_LL_OUT =         3
EVENT_LL_HARD_OUT =    4
EVENT_MAKE_DRINK =     5
EVENT_CHECK_LEVELS =   6
EVENT_POUR_DONE =      7
EVENT_CURRENT_SENSE =  8
EVENT_ERROR =          9
EVENT_POST_POUR_DONE = 10
EVENT_RESET          = 11
EVENT_DONE           = 12

# Transition table for Bartendro
transition_table = [
#   Current state                     Event                         Next state
    (STATE_READY,                     EVENT_MAKE_DRINK,             STATE_PRE_POUR),
    (STATE_LOW,                       EVENT_MAKE_DRINK,             STATE_PRE_POUR),
    (STATE_OUT,                       EVENT_MAKE_DRINK,             STATE_PRE_POUR),
    (STATE_HARD_OUT,                  EVENT_CHECK_LEVELS,           STATE_CHECK),
    (STATE_CURRENT_SENSE,             EVENT_RESET,                  STATE_CHECK),
    (STATE_ERROR,                     EVENT_RESET,                  STATE_CHECK),

    (STATE_PRE_POUR,                  EVENT_LL_OK,                  STATE_POURING),
    (STATE_PRE_POUR,                  EVENT_LL_LOW,                 STATE_POURING),
    (STATE_PRE_POUR,                  EVENT_LL_OUT,                 STATE_POURING),
    (STATE_PRE_POUR,                  EVENT_LL_HARD_OUT,            STATE_HARD_OUT),

    (STATE_POURING,                   EVENT_POUR_DONE,              STATE_POUR_DONE),
    (STATE_POURING,                   EVENT_CURRENT_SENSE,          STATE_CURRENT_SENSE),
    (STATE_POURING,                   EVENT_ERROR,                  STATE_ERROR),

    (STATE_POUR_DONE,                 EVENT_POST_POUR_DONE,         STATE_CHECK),

    (STATE_CHECK,                     EVENT_LL_OK,                  STATE_READY),
    (STATE_CHECK,                     EVENT_LL_LOW,                 STATE_LOW),
    (STATE_CHECK,                     EVENT_LL_OUT,                 STATE_OUT),
    (STATE_CHECK,                     EVENT_LL_HARD_OUT,            STATE_HARD_OUT),
]

end_states = [STATE_READY, STATE_LOW, STATE_OUT, STATE_HARD_OUT, STATE_CURRENT_SENSE, STATE_ERROR]

