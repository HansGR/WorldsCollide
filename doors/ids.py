"""The door-randomization element id space.

Every element the planner and realizer handle -- doors, traps, pits, and
their layered copies -- is identified by an integer id (plus a handful
of string variants); its numeric range encodes what it is. This module
is the one authoritative statement of those ranges; the data tables,
planner, and realizer all follow it.

    0-1280       vanilla exits (short 0-1128, long 1129-1280), compiled
                 into doors/atlas from the ROM's exit tables
    1281-1300    "safe ids": synthetic partner slots the dungeon-crawl
                 destination override allocates at realization
    1500-1999    event-tile doors: tiles that behave as two-way doors
                 (records in data/event_exit_data.py)
    2000-2999    traps, i.e. one-way exits ('2035a'-style string
                 variants are traps too)
    3000-3999    pits, i.e. one-way entrances; a trap's landing pit is
                 trap + 1000
    4000-5999    logical WoR copies of doors (door + 4000): the same
                 physical exit addressed in the other world
    6000-7999    door-as-trap landings (door + 6000): the receiving side
                 when a two-way door is used as a one-way exit
    10000+       virtual doors the planners inject and strip before
                 realization: the -dra/-drx meta-root doors
    20000-20001  the -mapx crossworld link pair (also virtual)
    30000+       protect stand-ins (door + 30000): map-shuffle-protected
                 doors walk as stand-ins so the real door stays vanilla

Room ids are NOT in this space: rooms are named strings (data/rooms.py).
Numbers are always exits; formatted strings are always rooms.

doors/model.py classifies by these ranges (_element_kind), with list
membership overriding ranges for live elements (live_kind): a door
listed in a room's trap bucket IS a trap. Established code compares
against the literal numbers throughout; new code may prefer the named
constants below -- the table above is the contract either way.
"""

# Two-way doors
NUM_VANILLA_EXITS = 1281            # short 0-1128, long 1129-1280
SAFE_ID_MIN, SAFE_ID_MAX = 1281, 1300
EVENT_DOOR_MIN, EVENT_DOOR_MAX = 1500, 1999

# One-ways
TRAP_MIN, TRAP_MAX = 2000, 2999
PIT_MIN, PIT_MAX = 3000, 3999
TRAP_TO_PIT = 1000                  # a trap's landing pit is trap + 1000

# Layered copies of doors
WOR_COPY = 4000                     # logical WoR copy: door + 4000
DOOR_AS_TRAP_LANDING = 6000         # one-way landing of a door: door + 6000

# Planner-only synthetics (stripped before realization)
VIRTUAL_DOOR_MIN = 10000            # -dra/-drx meta-root doors
CROSSWORLD_LINKS = (20000, 20001)   # -mapx WoB <-> WoR link pair
PROTECT_STANDIN = 30000             # map-shuffle protect stand-in: door + 30000
