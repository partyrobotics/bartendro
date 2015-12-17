# States that Bartendro can be in
STATE_START =         0
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
STATE_TEST_DISPENSE = 11
STATE_PRE_SHOT      = 12
STATE_POUR_SHOT     = 13

# Events that cause changes in Bartendro states
EVENT_START =          0
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
EVENT_TEST_DISPENSE  = 13
EVENT_MAKE_SHOT      = 14

# Transition table for Bartendro
transition_table = [
#   Current state                     Event                         Next state
    (STATE_START,                     EVENT_START,                  STATE_CHECK),

    (STATE_READY,                     EVENT_MAKE_DRINK,             STATE_PRE_POUR),
    (STATE_READY,                     EVENT_CHECK_LEVELS,           STATE_CHECK),
    (STATE_READY,                     EVENT_TEST_DISPENSE,          STATE_TEST_DISPENSE),
    (STATE_READY,                     EVENT_MAKE_SHOT,              STATE_PRE_SHOT),
    (STATE_LOW,                       EVENT_MAKE_DRINK,             STATE_PRE_POUR),
    (STATE_LOW,                       EVENT_CHECK_LEVELS,           STATE_CHECK),
    (STATE_LOW,                       EVENT_TEST_DISPENSE,          STATE_TEST_DISPENSE),
    (STATE_LOW,                       EVENT_MAKE_SHOT,              STATE_PRE_SHOT),
    (STATE_OUT,                       EVENT_MAKE_DRINK,             STATE_PRE_POUR),
    (STATE_OUT,                       EVENT_CHECK_LEVELS,           STATE_CHECK),
    (STATE_OUT,                       EVENT_TEST_DISPENSE,          STATE_TEST_DISPENSE),
    (STATE_OUT,                       EVENT_MAKE_SHOT,              STATE_PRE_SHOT),
    (STATE_HARD_OUT,                  EVENT_CHECK_LEVELS,           STATE_CHECK),
    (STATE_HARD_OUT,                  EVENT_TEST_DISPENSE,          STATE_TEST_DISPENSE),
    # A shot can still be possible even when in HARD_OUT
    (STATE_HARD_OUT,                  EVENT_MAKE_DRINK,             STATE_PRE_POUR),
    (STATE_HARD_OUT,                  EVENT_MAKE_SHOT,              STATE_PRE_SHOT),
    (STATE_CURRENT_SENSE,             EVENT_RESET,                  STATE_CHECK),
    (STATE_ERROR,                     EVENT_RESET,                  STATE_CHECK),
    (STATE_ERROR,                     EVENT_TEST_DISPENSE,          STATE_TEST_DISPENSE),
    (STATE_ERROR,                     EVENT_CHECK_LEVELS,           STATE_CHECK),

    (STATE_TEST_DISPENSE,             EVENT_POUR_DONE,              STATE_CHECK),

    (STATE_PRE_POUR,                  EVENT_LL_OK,                  STATE_POURING),
    (STATE_PRE_POUR,                  EVENT_LL_LOW,                 STATE_POURING),
    (STATE_PRE_POUR,                  EVENT_LL_OUT,                 STATE_POURING),
    (STATE_PRE_POUR,                  EVENT_LL_HARD_OUT,            STATE_HARD_OUT),

    (STATE_POURING,                   EVENT_POUR_DONE,              STATE_POUR_DONE),
    (STATE_POURING,                   EVENT_CURRENT_SENSE,          STATE_CURRENT_SENSE),
    (STATE_POURING,                   EVENT_ERROR,                  STATE_ERROR),

    (STATE_POUR_DONE,                 EVENT_POST_POUR_DONE,         STATE_CHECK),

    (STATE_PRE_SHOT,                  EVENT_LL_OK,                  STATE_POUR_SHOT),
    (STATE_PRE_SHOT,                  EVENT_LL_LOW,                 STATE_POUR_SHOT),

    (STATE_POUR_SHOT,                 EVENT_POUR_DONE,              STATE_POUR_DONE),
    (STATE_POUR_SHOT,                 EVENT_CURRENT_SENSE,          STATE_CURRENT_SENSE),
    (STATE_POUR_SHOT,                 EVENT_ERROR,                  STATE_ERROR),

    (STATE_POUR_DONE,                 EVENT_POST_POUR_DONE,         STATE_CHECK),

    (STATE_CHECK,                     EVENT_LL_OK,                  STATE_READY),
    (STATE_CHECK,                     EVENT_LL_LOW,                 STATE_LOW),
    (STATE_CHECK,                     EVENT_LL_OUT,                 STATE_OUT),
    (STATE_CHECK,                     EVENT_LL_HARD_OUT,            STATE_HARD_OUT),
]

end_states = [STATE_READY, STATE_LOW, STATE_OUT, STATE_HARD_OUT, STATE_CURRENT_SENSE, STATE_ERROR]
