#event exit information:  Event_ID:  [original address, event bit length, split point, is chararacter hidden, description]
event_exit_info = {
    2001 : [int('0cd8d4',16), 34, 23, True, 'Umaro Cave 1st Room trapdoor top'],
    2002 : [int('0cd8b2',16), 34, 23, True, 'Umaro Cave 1st Room trapdoor left'],
    2003 : [int('0cd93a',16), 45, 34, True, 'Umaro Cave Switch Room trapdoor to 2nd Room'],
    2004 : [int('0cd967',16), 45, 34, True, 'Umaro Cave Switch Room trapdoor to Boss Room'],
    2005 : [int('0cd918',16), 34, 23, True, 'Umaro Cave 2nd Room west trapdoor'],
    2006 : [int('0cd918',16), 34, 23, True, 'Umaro Cave 2nd Room west trapdoor ***duplicate***'],
    2007 : [int('0cd8f6',16), 34, 23, True, 'Umaro Cave 2nd Room east trapdoor'],
    2008 : [int('0cd8f6',16), 34, 23, True, 'Umaro Cave 2nd Room east trapdoor ***duplicate***'],
    2009 : [int('0c3839',16), 50, 0 , False, 'Umaro Cave Boss Room trapdoor to Narshe'],
    2010 : [int('0c37e7',16), 82, 66, True, 'Narshe Peak WoR entrance to Umaros Cave']  # Note 1
    }

# Notes:
# 1. The Narshe Peak WoR jump into Umaro's cave event has a branch point (B6) at CC/37F0 (byte 10).  Code is:
#       B6 FE 37 02 F8 37 02 = (branch cmd) (choice 1 address bytes [x3]) (choice 2 address bytes [x3])
#    Choice address bytes are in order [low byte, mid byte, hi byte]; the address is also relative to offset $CA0000
#    so this translates as:  (Branch to) (1. CC/37FE [enter cave]) (2. CC/37F8 [return])
#    since we are copying the entire event with both branches, we need to patch these bytes with updated addresses:
#    specifically, we need to take them to e.g. 0C37FE + (New Address) - 0c37e7.  Also subtract 0A0000 (offset)
# 1b. The transition to the correct location happens now, but the music is not loaded and the fade behavior is weird.
#    There's a momentary fade up on the cliff, fade down, transition, and then land animation & sound effect.
#    Looks like there's code in the 2010 post-transition that will need to be patched in: 
BASE_OFFSET = 0xA0000

exit_event_patch = {
    2010 : lambda src, addr: src[:10] +
                             [(23 + addr) % 0x100, ((23 + addr) >> 8) % 0x100, ((23 + addr - BASE_OFFSET) >> 16) % 0x100,
                              (17 + addr) % 0x100, ((17 + addr) >> 8) % 0x100, ((17 + addr - BASE_OFFSET) >> 16) % 0x100] + src[16:]
}
