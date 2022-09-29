#event exit information:  Event_ID:  [original address, event bit length, split point, transition state, description]
#   transition state = [is_chararacter_hidden, is_song_override_on, is_screen_hold_on, required_world]
#   None = not implemented
event_exit_info = {
    2001 : [int('0cd8d4',16), 34, 24, [True, True, False], 'Umaro Cave 1st Room trapdoor top'],
    2002 : [int('0cd8b2',16), 34, 24, [True, True, False], 'Umaro Cave 1st Room trapdoor left'],
    2003 : [int('0cd93a',16), 45, 35, [True, True, False], 'Umaro Cave Switch Room trapdoor to 2nd Room'],
    2004 : [int('0cd967',16), 45, 35, [True, True, False], 'Umaro Cave Switch Room trapdoor to Boss Room'],
    2005 : [int('0cd918',16), 34, 24, [True, True, False], 'Umaro Cave 2nd Room west trapdoor'],
    2006 : [int('0cd918',16), 34, 24, [True, True, False], 'Umaro Cave 2nd Room west trapdoor ***duplicate***'],
    2007 : [int('0cd8f6',16), 34, 24, [True, True, False], 'Umaro Cave 2nd Room east trapdoor'],
    2008 : [int('0cd8f6',16), 34, 24, [True, True, False], 'Umaro Cave 2nd Room east trapdoor ***duplicate***'],
    2009 : [int('0c3839',16), 50, 1 , [False, False, False], 'Umaro Cave Boss Room trapdoor to Narshe'],
    2010 : [int('0c37e7',16), 82, 67, [True, True, True], 'Narshe Peak WoR entrance to Umaros Cave'],
    2011 : [int('0bee80',16), 15, 0 , [None, None, None], 'Esper Mtn 2nd Room bridge jump west'],   # forced connection, no mod
    2012 : [int('0bee71',16), 15, 0 , [None, None, None], 'Esper Mtn 2nd Room bridge jump middle'], # forced connection, no mod
    2013 : [int('0bee62',16), 15, 0 , [None, None, None], 'Esper Mtn 2nd Room bridge jump east'],    # forced connection, no mod
    2014 : [int('0bee8f',16), 47, 30, [False, False, True], 'Esper Mtn Pit Room South trapdoor'],
    2015 : [int('0beebe',16), 46, 30, [False, False, True], 'Esper Mtn Pit Room North trapdoor'],  # no "38 (Hold screen)" after transition
    2016 : [int('0beeec',16), 47, 30, [False, False, True], 'Esper Mtn Pit Room East trapdoor'],
    2017 : [int('0b4b86',16), 47, 1 , [False, False, False], 'Owzers Mansion switching door left'],
    2018 : [int('0b4b86',16), 47, 1 , [False, False, False], 'Owzers Mansion switching door right'],  # same destination, same event!
    2019 : [int('0b4bb5',16), 53, 3 , [False, False, False], 'Owzers Mansion behind switching door exit'],  # set event bit 0x24c?
    2020 : [int('0b4c94',16), 13, 1 , [False, False, False], 'Owzers Mansion floating chest room exit'],
    2021 : [int('0b4bea',16), 51, 1 , [False, False, False], 'Owzers Mansion save point room oneway']
    }
# Notes:
#   1. is_screen_hold_on is False for Umaro's Cave trapdoor events, but they all include a hold screen / free screen
#       pair after the transition, so it technically does not need to be patched in for entrances.  It also doesn't need
#       to be patched in for exits, so the value shouldn't be "True" either.  If there were a value for which both
#       "i" and "not i" were false, I would use it here.

from instruction.event import EVENT_CODE_START
import instruction.field as field
from utils.flatten import flatten
exit_event_patch = {
    # Jump into Umaro's Cave:
    #   - add falling sound effect [0xf4, 0xba] after map load (src_end[5]);
    #   - force load Umaro's music [0xf0, 0x30] just before return (src_end[-1])
    # In original event at: CC/3836
    # NOTE you only really want to force load this music if it's in Umaro's Cave...
    2010 : lambda src, src_end: [ src, src_end[:5] + [0xf4, 0xba] + src_end[5:-1] + [0xf0, 0x30] + src_end[-1:] ],

    # Trapdoors in Esper Mountain: remove the check to see if the boss has been defeated yet.
    # e.g. "CB/EE8F: C0    If ($1E80($097) [$1E92, bit 7] is clear), branch to $CA5EB3 (simply returns)
    2014 : lambda src, src_end: [ src[6:], src_end ],
    2015 : lambda src, src_end: [ src[6:], src_end ],
    2016 : lambda src, src_end: [ src[6:], src_end ],

    # Switching door events in Owzer's Mansion: turn off the door timer before transitioning
    # Call subroutine $CB/2CAA (resets all timers).
    # # May also be necessary to clear event bits $1FC, $1FD, $1FE: [0xd3, 0xfc, 0xd3, 0xfd, 0xd3, 0xfe], but
    # # supposedly these are cleared on map load.
    2017 : lambda src, src_end: [ [0xb2, 0xaa, 0x2c, 0x01] + src, src_end ],
    2018 : lambda src, src_end: [ [0xb2, 0xaa, 0x2c, 0x01] + src, src_end ],
    587 : [0xb2, 0xaa, 0x2c, 0x01]  # field.Call(0xb2caa)
}

entrance_event_patch = {
    # Jump back to Narshe from Umaro's cave: force "clear $1EB9 bit 4" (song override) before transition
    # Now handled in map_events.mod() with common patches
    #3009: lambda src, src_end: [src[:-1] + [0xd3, 0xcc] + src[-1:], src_end],

    # Jump from Narshe into Umaro's cave: Remove extra falling sound effect (src_end[5:6])
    3010: lambda src, src_end: [ src, src_end[:5] + src_end[7:] ],

    # Jump into Esper Mountain room 2, North trapdoor: patch in "hold screen" (0x38) after map transition
    # The other trapdoors have this, maybe it's just a typo?
    3015: lambda src, src_end: [ src, src_end[:5] + [0x38] + src_end[5:] ]
}

event_address_patch = {
    # Jump into Umaro's Cave: update branched event addresses
    2010 : lambda src, addr: src[:10] +
                             [(23 + addr) % 0x100, ((23 + addr) >> 8) % 0x100, ((23 + addr - EVENT_CODE_START) >> 16) % 0x100,
                              (17 + addr) % 0x100, ((17 + addr) >> 8) % 0x100, ((17 + addr - EVENT_CODE_START) >> 16) % 0x100] +
                             src[16:]
}

# Notes:
# 2009.  The transition out of Umaro's cave and back to Narshe should load the Narshe music, but instead just keeps
#   playing the Umaro music when randomized. I am not sure why this happens: look at the post-transition code for 2009?
#   Maybe something having to do with the door exit?
#
#   Music is going to be tricky in general: should we always load music when changing between maps with different
#   default music?  We probably want different behavior for different cases.
#       How do we figure out what the default music is for an area?
#
# 2010b. The transition to the correct location happens now, but the fade behavior is weird and the music is not loaded.
#   There's a momentary fade up on the cliff, fade down, transition, and then land animation & sound effect, no music.
#   Here's the code in the 2010 post-transition:
#       CC/3829: 6B    Load map $0119 (Umaro's Cave first room), place party at (14, 55), facing down
#       CC/382F: F4    Play sound effect 186
#       CC/3831: B2    Call subroutine $CCD9A6  <-- standard Umaro's cave trapdoor animation
#       CC/3835: 92    Pause for 30 units
#       CC/3836: F0    Play song 48 (Umaro), (high bit clear), full volume:  <-- "[0xf0, 0x30]" = [240, 48]
#       CC/3838: FE    Return
#   Fade behavior is weird because this is a 6B call instead of a 6A call; all the other transitions are 6A's
#       6A is "Fade out & load new map"; 6B is "Load new map assuming fadeout already happened."
#       They have the same parameters - so we can get around this by moving the split one byte later:
#       the original type of transition is preserved but destination is modified. IMPLEMENTED/NOT TESTED.
#   For the music, just patch in [0xf0, 0x30] just before the return bit.  IMPLEMENTED/NOT TESTED

# 2010. The Narshe Peak WoR jump into Umaro's cave event has a branch point (B6) at CC/37F0 (byte 10).  Code is:
#       B6 FE 37 02 F8 37 02 = (branch cmd) (choice 1 address bytes [x3]) (choice 2 address bytes [x3])
#   Choice address bytes are in order [low byte, mid byte, hi byte]; the address is also relative to offset $CA0000
#   so this translates as:  (Branch to) (1. CC/37FE [enter cave]) (2. CC/37F8 [return])
#   since we are copying the entire event with both branches, we need to patch these bytes with updated addresses:
#   specifically, we need to take them to e.g. 0C37FE + (New Address) - 0c37e7.  Also subtract 0A0000 (offset).