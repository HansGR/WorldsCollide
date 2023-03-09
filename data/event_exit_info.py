# event exit information:  Event_ID:  [original address, event bit length, split point, transition state, description, location]
#   transition state = [is_chararacter_hidden, is_song_override_on, is_screen_hold_on, is_on_raft]
#   location = [map_id, x, y]
#   None = not implemented
event_exit_info = {
    # UMARO'S CAVE
    2001: [0xcd8d4, 34, 24, [True, True, False, False], 'Umaro Cave 1st Room trapdoor top', [281, 11, 53] ],
    2002: [0xcd8b2, 34, 24, [True, True, False, False], 'Umaro Cave 1st Room trapdoor left', [281, 10, 54] ],
    2003: [0xcd93a, 45, 35, [True, True, False, False], 'Umaro Cave Switch Room trapdoor to 2nd Room', [281, 31, 9] ],
    2004: [0xcd967, 45, 35, [True, True, False, False], 'Umaro Cave Switch Room trapdoor to Boss Room', [281, 40, 12] ],
    2005: [0xcd918, 34, 24, [True, True, False, False], 'Umaro Cave 2nd Room west trapdoor', [282, 33, 26] ],
    2006: [0xcd918, 34, 24, [True, True, False, False], 'Umaro Cave 2nd Room west trapdoor ***duplicate***', [282, 33, 26] ],
    2007: [0xcd8f6, 34, 24, [True, True, False, False], 'Umaro Cave 2nd Room east trapdoor', [282, 14, 30] ],
    2008: [0xcd8f6, 34, 24, [True, True, False, False], 'Umaro Cave 2nd Room east trapdoor ***duplicate***', [282, 14, 30] ],
    2009: [0xc3839, 50, 1, [False, False, False, False], 'Umaro Cave Boss Room trapdoor to Narshe', [283, 57, 7] ],
    2010: [0xc37e7, 82, 67, [True, True, True, False], 'Narshe Peak WoR entrance to Umaros Cave', [35, 9, 12] ],

    # ESPER MOUNTAIN
    2011: [0xbee80, 15, 0, [None, None, None, None], 'Esper Mtn 2nd Room bridge jump west', [0x177, 36, 53] ],
    # forced connection, no mod
    2012: [0xbee71, 15, 0, [None, None, None, None], 'Esper Mtn 2nd Room bridge jump middle', [0x177, 39, 54] ],
    # forced connection, no mod
    2013: [0xbee62, 15, 0, [None, None, None,None], 'Esper Mtn 2nd Room bridge jump east', [0x177, 47, 53] ],
    # forced connection, no mod
    2014: [0xbee8f, 47, 30, [False, False, True, False], 'Esper Mtn Pit Room South trapdoor', [0x177, 11, 51] ],
    2015: [0xbeebe, 46, 30, [False, False, True, False], 'Esper Mtn Pit Room North trapdoor', [0x177, 12, 46] ],
    # no "38 (Hold screen)" after transition
    2016: [0xbeeec, 47, 30, [False, False, True, False], 'Esper Mtn Pit Room East trapdoor', [0x177, 17, 49]],

    # OWZER'S MANSION
    2017: [0xb4b86, 47, 1, [False, False, False, False], 'Owzers Mansion switching door left', [0x0CF, 90, 50]],
    2018: [0xb4b86, 47, 1, [False, False, False, False], 'Owzers Mansion switching door right', [0x0CF, 92, 50]],
    # same destination, same event!
    2019: [0xb4bb5, 53, 3, [False, False, False, False], 'Owzers Mansion behind switching door exit', [0x0CF, 85, 50]],
    # set event bit 0x24c?
    2020: [0xb4c94, 13, 1, [False, False, False, False], 'Owzers Mansion floating chest room exit', [0x0CF, 76, 51]],
    2021: [0xb4bea, 51, 1, [False, False, False, False], 'Owzers Mansion save point room oneway', [0x0CF, 86, 38]],

    # MAGITEK FACTORY
    2022: [0xc7651, 49, 29, [False, False, False, False], 'Magitek factory 1 conveyor to Mtek-2 top tile', [0x106, 22, 53]],
    # will require address patching
    '2022a': [0xc765f, 0, 0, [None, None, None, None], 'Magitek factory 1 conveyor to Mtek-2 bottom tile', [0x106, 22, 54]],
    # same exit as above; requires address patch & tile edit
    2023: [0xc7682, 37, 0, [None, None, None, None], 'Magitek factory platform elevator to Mtek-1', [0x106, 10, 54]],
    2024: [0xc7905, 50, 10, [False, False, False, False], 'Magitek factory 2 pipe exit loop', [0x107, 49, 48]],
    2025: [0xc7565, 86, 58, [True, False, False, False], 'Magitek factory 2 conveyor to pit left tile', [0x107, 36, 44]],
    # will require address patching
    '2025a': [0xc7581, 0, 0, [None, None, None, None], 'Magitek factory 2 conveyor to pit mid tile', [0x107, 37, 44]],
    # same exit as above; requires address patch & tile edit
    '2025b': [0xc7573, 0, 0, [None, None, None, None], 'Magitek factory 2 conveyor to pit right tile', [0x107, 38, 44]],
    # same exit as above; requires address patch & tile edit
    2026: [0xc75f6, 91, 39, [False, False, False, False], 'Magitek factory pit hook to Mtek-2', [0x108, 6, 6]],
    2027: [0xc7f43, 217, 131, [False, False, False, False], 'Magitek factory lab Cid''s elevator', [0x112, 20, 13]],
    # bit $1E80($068) set by switch (0c7a60)?  Look for conflicts with event patch code.
    2028: [0xc8022, 309, 152, [False, True, False, False], 'Magitek factory minecart start event', [0x110, 'NPC', 0]],
    # NPC #0 on this map. Not an event tile.  Started by talking to Cid.  Position: # [0x110, 9, 51]

    # CAVE TO THE SEALED GATE
    2029: [0xb3176, 84, 0, [None, None, None, None], 'Cave to the Sealed Gate grand staircase', [0x180, 71, 15]],
    # Grand staircase event
    2030: [0xb33c9, 32, 0, [None, None, None, None], 'Cave to the Sealed Gate switch bridges', [0x180, 104, 17]],
    # Switch bridge events
    2031: [0xb2a9f, 7, 1, [False, False, False, False], 'Cave to the Sealed Gate shortcut exit', [0x180, 5, 43]],  # Shortcut exit

    # ZOZO (WORLD OF BALANCE)
    2032: [0xa963d, 22, 0, [None, None, None, None], 'Zozo hook descent from building', [0x0DD, 35, 41] ],
    2033: [0x00000, 0, 0, [None, None, None, None], 'Zozo line of walking guys (logical)', [0x0E1, 0, 0] ],

    # LETE RIVER
    2034: [0xb059f, 151, 146, [False, False, False, True], 'Lete River start', [0x071, 'JMP', None]], # [x,y] = [31, 51]
    2035: [0xb0636, 193, 182, [False, False, False, True], 'Lete River Section 1', [0x071, 'JMP', None]],
    '2035a': [0xb06f7, 101, 90, [False, False, False, True], 'Lete River Section 1 (LEFT)', [0x071, 'JMP', None]],
    '2035b': [0xb07c0, 106, 95, [False, False, False, True], 'Lete River Section 1 (RIGHT)', [0x071, 'JMP', None]],
    2036: [0xb051c, 64, 52, [False, False, False, True], 'Lete River Cave 1', [0x072, 'JMP', None]], # [x,y] = [20, 24]
    2037: [0xb07cc, 157, 145, [False, False, False, True], 'Lete River Section 2', [0x071, 'JMP', None]],
    2038: [0xb055c, 67, 55, [False, False, False, True], 'Lete River Cave 2', [0x072, 'JMP', None]],  # [x,y] = [6, 15]:
    2039: [0xb0869, 229, 108, [False, False, False, True], 'Lete River Section 3 + boss', [0x071, 'JMP', None]],

    # EVENT TILES that behave as if they are doors:
    #       WOB: Imperial Camp; Figaro Castle (@ Figaro & Kohlingen); Thamasa; Vector; Cave to SF south entrance
    #       WOR: Figaro Castle (@ Figaro & Kohlingen); Solitary Island Cliff
    #       Other: Opera House Lobby, Mobliz Outside, ...
    # To do this: must add index to map_exit_extra.
    1501: [0xb0bb7, 0, 0, [None, None, None], 'Imperial Camp WoB', [0x000, 179, 71] ],
    1502: [0xa5eb5, 0, 0, [None, None, None], 'Figaro Castle WoB', [0x000, 64, 76] ],
    '1502a': [0xa5eb5, 0, 0, [None, None, None], 'Figaro Castle WoB 2', [0x000, 65, 76] ],
    1503: [0xa5ec2, 0, 0, [None, None, None], 'Figaro Castle WoB (kohlingen)', [0x000, 30, 48] ],
    '1503c': [0xa5ec2, 0, 0, [None, None, None], 'Figaro Castle WoB (kohlingen) 2', [0x000, 31, 48] ],
    1504: [0xbd2ee, 0, 0, [None, None, None], 'Thamasa WoB', [0x000, 250, 128] ],  # wtf is this event doing?
    1505: [0xa5ecf, 14, 7, [None, None, None], 'Vector entrance event tile', [0x000, 120, 187] ],
    '1505a': [0xa5ecf, 14, 7, [None, None, None], 'Vector entrance event tile 2', [0x000, 121, 187] ],
    1506: [0xa5ee3, 0, 0, [None, None, None], 'Cave to South Figaro South Entrance WoB', [0x000, 75, 102] ],

    1507: [0xa5f0b, 0, 0, [None, None, None], 'Figaro Castle WoR', [0x001, 81, 85] ],
    '1507a': [0xa5f0b, 0, 0, [None, None, None], 'Figaro Castle WoR 2', [0x001, 82, 85] ],
    1508: [0xa5f18, 0, 0, [None, None, None], 'Figaro Castle WoR (kohlingen)', [0x001, 53, 58] ],
    '1508a': [0xa5f18, 0, 0, [None, None, None], 'Figaro Castle WoR (kohlingen) 2', [0x001, 54, 58] ],
    1509: [0xa5f39, 0, 0, [None, None, None], 'Solitary Island cliff entrance', [0x001, 73, 231] ]

}
# Notes:
#   1. is_screen_hold_on is False for Umaro's Cave trapdoor events, but they all include a hold screen / free screen
#       pair after the transition, so it technically does not need to be patched in for entrances.  It also doesn't need
#       to be patched in for exits, so the value shouldn't be "True" either.  If there were a value for which both
#       "i" and "not i" were false, I would use it here.
#   2. Currently choosing to randomize destination of mine cart event.
#       Talking to Cid always starts minecart event, but destination can take you elsewhere
#       What happens with MTek3 prize?  Is it triggered by minecart, or by entering Vector?

from instruction.event import EVENT_CODE_START
from instruction import field
import data.event_bit as event_bit

# from instruction.field.functions import ORIGINAL_CHECK_GAME_OVER
exit_event_patch = {
    # Jump into Umaro's Cave:
    #   - add falling sound effect [0xf4, 0xba] after map load (src_end[5]);
    #   - force load Umaro's music [0xf0, 0x30] just before return (src_end[-1])
    # In original event at: CC/3836
    # NOTE you only really want to force load this music if it's in Umaro's Cave...
    # 2010 : lambda src, src_end: [ src, src_end[:5] + [0xf4, 0xba] + src_end[5:-1] + [0xf0, 0x30] + src_end[-1:] ],
    2010: lambda src, src_end: tritoch_event_mod(src, src_end),

    # Trapdoors in Esper Mountain: remove the check to see if the boss has been defeated yet.
    # e.g. "CB/EE8F: C0    If ($1E80($097) [$1E92, bit 7] is clear), branch to $CA5EB3 (simply returns)
    2014: lambda src, src_end: [src[6:], src_end],
    2015: lambda src, src_end: [src[6:], src_end],
    2016: lambda src, src_end: [src[6:], src_end],

    # Switching door events in Owzer's Mansion: turn off the door timer before transitioning
    # Call subroutine $CB/2CAA (resets all timers).
    # # May also be necessary to clear event bits $1FC, $1FD, $1FE: [0xd3, 0xfc, 0xd3, 0xfd, 0xd3, 0xfe], but
    # # supposedly these are cleared on map load.
    2017: lambda src, src_end: [[0xb2, 0xaa, 0x2c, 0x01] + src, src_end],
    2018: lambda src, src_end: [[0xb2, 0xaa, 0x2c, 0x01] + src, src_end],
    586: [field.Call(0xb2caa)],  # [0xb2, 0xaa, 0x2c, 0x01],  # South door.
    587: [field.Call(0xb2caa)],  # [0xb2, 0xaa, 0x2c, 0x01],  # North door.

    # Cave to the sealed gate: force reset timers when leaving lava room
    1075: [field.Call(0xb2caa)],  # [0xb2, 0xaa, 0x2c, 0x01],  # North door.
    1077: [field.Call(0xb2caa)]  # [0xb2, 0xaa, 0x2c, 0x01],  # South door.

}

entrance_event_patch = {
    # Jump back to Narshe from Umaro's cave: force "clear $1EB9 bit 4" (song override) before transition
    # Now handled in map_events.mod() with common patches
    # 3009: lambda src, src_end: [src[:-1] + [0xd3, 0xcc] + src[-1:], src_end],

    # Jump from Narshe into Umaro's cave: Remove extra falling sound effect (src_end[5:6])
    3010: lambda src, src_end: [src, src_end[:5] + src_end[7:]],

    # Jump into Esper Mountain room 2, North trapdoor: patch in "hold screen" (0x38) after map transition
    # The other trapdoors have this, maybe it's just a typo?
    3015: lambda src, src_end: [src, src_end[:5] + [0x38] + src_end[5:]],

    # Cid's Elevator Ride: remove move-party-down after elevator.
    # space = Reserve(0xc8014, 0xc801a, "magitek factory move party down after elevator", field.NOP())
    # NOTE: should now be handled in Events(), no need to repeat.
    # 3027: lambda src, src_end: [ src, src_end[:-8] + src_end[-1:]]

    # Minecart Ride: if Cranes are defeated, instead go to normal Vector
    3028: lambda src, src_end: minecart_event_mod(src, src_end),

}


def minecart_event_mod(src, src_end):
    # Special event for outro of minecart ride: return to Vector if cranes have been defeated.
    # C0    If ($1E80($06B) is set), branch to $(new event) that sends you to Vector map instead
    # C0    If ($1E80($069) is set), branch to $(new event) that sends you to MTek3 Vector map without animation
    from memory.space import Write, Bank
    from event.event import direction
    go_to_vector = (
        field.LoadMap(0xf2, direction.LEFT, default_music=True, x=62, y=13, entrance_event=True),
        field.FadeInScreen(),
        field.Return()
    )
    go_to_mtek3_vector = (
        field.LoadMap(0xf0, direction.LEFT, default_music=True, x=62, y=13, entrance_event=True),
        field.FadeInScreen(),
        field.Return()
    )
    space = Write(Bank.CC, go_to_vector, "Return to Vector")
    patch1 = branch_code(space.start_address, 0)
    space = Write(Bank.CC, go_to_mtek3_vector, "Return to MTek3 Vector")
    patch2 = branch_code(space.start_address, 0)
    src = src[:-1] + [0xc0, 0x6b, 0x80] + patch1 + [0xc0, 0x69, 0x80] + patch2 + src[-1:]
    return src, src_end


def tritoch_event_mod(src, src_end):
    new_src = [0xc0, 0x9e, 0x2, 0xb3, 0x5e, 0x0]  # field.BranchIfEventBitClear(event_bit.GOT_TRITOCH, 0xa5eb3),

    if src[6] == 0xc0:
        # Special event for cliff jump behind Tritoch: reproduce the modified WC event for character gating
        atma_event_addr = code_address(src[10:13]) + EVENT_CODE_START
        # atma_src = rom.ROM.get_bytes(atma_event_addr, 0xed-0xd8)
        new_src += [0xc0, 0xed, 0x2] + branch_code(atma_event_addr, 17) # field.BranchIfEventBitClear(0x2ed, 0xc74e9)

    new_src += [0x4b, 0x3b, 0xa] + [  # display text box $a3b
                0xb6] + [0x0, 0x0, 0x0] + [0xf8, 0x37, 0x2] + [   # Yes --> branch to (placeholder), No --> branch to step back;
                0xfe] + src[23:]  # return; source code for jumping animation

    return new_src, src_end


def branch_code(addr, offset):
    return [(offset + addr) % 0x100, ((offset + addr) >> 8) % 0x100, ((offset + addr - EVENT_CODE_START) >> 16) % 0x100]


def code_address(code):
    return (code[2] << 16) + (code[1] << 8) + code[0]


event_address_patch = {
    # Jump into Umaro's Cave: update branched event address.  Slightly risky search for 1st instance of 0xb6.
    2010: lambda src, addr: src[:src.index(0xb6)+1] + branch_code(addr, 23) + src[src.index(0xb6)+4:],

    # Magitek factory Room 1 conveyor into room 2:
    #   At CC/7658 (+7), branch-if-clear [0xc0, ] to CC/7666 (+21)
    #   Paired event starts at CC/765F (+14).
    2022: lambda src, addr: src[:10] + branch_code(addr, 21) + src[13:],

    # Magitek factory Room 2 conveyor into pit room:
    #   At CC/756C (+7), branch-if-clear [0xc0, ] to CC/7588 (+35)
    #   At CC/757A (+21), branch-if-clear [0xc0, ] to CC/7588 (+35)
    #   Paired events start at CC/7573 (+14) and CC/7581 (+28).
    2025: lambda src, addr: src[:10] + branch_code(addr, 35) + src[13:24] + branch_code(addr, 35) + src[27:]

}

# We define "multi events" as multiple event tiles that are all logically the same exit and partially share
# the same code.  The event tile with the earliest address should be the key event, others will be referenced to it.
multi_events = {
    2022: ['2022a'],  # Magitek factory room 1 conveyor belt
    2025: ['2025a', '2025b'],  # Magitek factory room 1 conveyor belt

    2035: ['2035a', '2035b'],  # Lete River section 1 branching code

    1502: ['1502a'],  # Figaro Castle WoB entrance tiles
    1503: ['1503c'],  # Figaro Castle WoB (kohlingen) entrance tiles
    1505: ['1505a'],   # Vector entrance tiles WoB

    1507: ['1507a'],  # Figaro Castle WoR entrance tiles
    1508: ['1508a']   # Figaro Castle WoR (kohlingen) entrance tiles
}

# NOTES ON JUMP/CALL vs REWRITE:
# 1. If we use jumping/calling instead of writing, we are probably much efficient...
# --> UNLESS we can reclaim all the original event space, in which case rewriting would be much more efficient because
# --> we can reclaim all the NOP space!
# 2. Using jumping/calling removes the need for event_address_patch and the Magitek use of multi_events (2 in, 1 out)
# 3. Using jumping/calling adds a need for Lete river use of multi_events (1 in, 3 out).

# Some events need to be modified by different parts of the code before being written.  We identify them here by where
# the event script starts in the code.
# key_events = [0xc7f43,  # Cid's elevator ride
#              0xc8022   # Cid's minecart ride
#              ]

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