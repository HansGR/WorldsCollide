#event exit information:  Event_ID:  [original address, event bit length, split point, is chararacter hidden, description]
event_exit_info = {
    2001 : [int('0cd8d4',16), 34, 24, True, 'Umaro Cave 1st Room trapdoor top'],
    2002 : [int('0cd8b2',16), 34, 24, True, 'Umaro Cave 1st Room trapdoor left'],
    2003 : [int('0cd93a',16), 45, 35, True, 'Umaro Cave Switch Room trapdoor to 2nd Room'],
    2004 : [int('0cd967',16), 45, 35, True, 'Umaro Cave Switch Room trapdoor to Boss Room'],
    2005 : [int('0cd918',16), 34, 24, True, 'Umaro Cave 2nd Room west trapdoor'],
    2006 : [int('0cd918',16), 34, 24, True, 'Umaro Cave 2nd Room west trapdoor ***duplicate***'],
    2007 : [int('0cd8f6',16), 34, 24, True, 'Umaro Cave 2nd Room east trapdoor'],
    2008 : [int('0cd8f6',16), 34, 24, True, 'Umaro Cave 2nd Room east trapdoor ***duplicate***'],
    2009 : [int('0c3839',16), 50, 1 , False, 'Umaro Cave Boss Room trapdoor to Narshe'],
    2010 : [int('0c37e7',16), 82, 67, True, 'Narshe Peak WoR entrance to Umaros Cave']
    }

BASE_OFFSET = 0xA0000

# ERROR: patches that change the length must happen BEFORE allocation; patches that depend on addresses must happen AFTER allocation!!!
exit_event_patch = {
    # Jump into Umaro's Cave: force load Umaro's music (new music?) at end of event
    # In original event at: CC/3836
    2010 : lambda src, src_end: [src, src_end[:-1] + [0xf0, 0x30] + src_end[-1:]]

}

entrance_event_patch = {
    # Jump back to Narshe from Umaro's cave: force "clear $1EB9 bit 4" (song override) before transition
    3009 : lambda src, src_end: [src[:-1] + [0xd3, 0xcc] + src[-1:], src_end]
}

event_address_patch = {
    # Jump into Umaro's Cave: update branched event addresses
    2010 : lambda src, addr: src[:10] +
                             [(23 + addr) % 0x100, ((23 + addr) >> 8) % 0x100, ((23 + addr - BASE_OFFSET) >> 16) % 0x100,
                              (17 + addr) % 0x100, ((17 + addr) >> 8) % 0x100, ((17 + addr - BASE_OFFSET) >> 16) % 0x100] +
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