from memory.space import Bank, Reserve, Write
import instruction.asm as asm
import args

# Required characters (-rc/--require-characters) are marked "unmovable" on the party-select
# (Lineup) screen.  Each forced character locks the menu slot it occupies: the lock array at
# $7EAC8D is rebuilt from the forced-character bitmask at $0202 by the "Establish locked actor
# slots" routine (C3/790C).  The lock is enforced at exactly two points -- when the player picks
# up a slot (C3/717B/717F) and when the player chooses a destination slot (C3/7222/7226).
#
# In vanilla the lock is absolute: a locked slot can neither be picked up nor be a swap
# destination.  As a result, when more than one party is shown (entering Kefka's Tower, and the
# two-party Narshe Battle / Phoenix Cave when every available character is required), the player
# cannot choose which required character goes into which party.
#
# This mod relaxes the rule so that a locked slot may be swapped with another locked slot -- two
# required characters can trade places -- while still forbidding any swap between a locked and an
# unlocked slot.  The party-membership requirement is preserved, because swapping two required
# characters leaves each of them in a (forced) party slot.

class RequiredCharacterSwap:
    def __init__(self):
        # Nothing is locked unless the -rc flag forced characters into parties, so leave the
        # vanilla Lineup menu completely untouched when the feature is not in use.
        if not getattr(args, "required_character_ids", None):
            return
        self.mod()

    def mod(self):
        # Subroutine: return A = lock(src) EOR lock(dst), which is $00 when the source and
        # destination slots have the same locked status and $FF (negative -> N set) when they
        # differ.  On entry X = destination slot index (set by the caller at C3/7221) and the lock
        # array holds $FF (locked) or $00 (unlocked).  $E1 is free scratch here and $E0 (the
        # destination index, used again by the original code at C3/7230) is preserved.
        space = Write(Bank.C3, [
            asm.LDA(0x7eac8d, asm.LNG_X),   # a = lock(dst); x = dst slot index on entry
            asm.STA(0xe1, asm.DIR),         # save lock(dst)
            asm.TDC(),                      # a = 0
            asm.LDA(0x28, asm.DIR),         # a = source cursor slot
            asm.CLC(),
            asm.ADC(0x49, asm.DIR),         # + 16 if the source is in a party area
            asm.ADC(0x5b, asm.DIR),         # (+ 0)
            asm.TAX(),                      # x = source slot index
            asm.LDA(0x7eac8d, asm.LNG_X),   # a = lock(src)
            asm.EOR(0xe1, asm.DIR),         # a = lock(src) EOR lock(dst)
            asm.RTS(),
        ], "require characters: party-select like-lock compare")
        like_lock_compare = space.start_address

        # Subroutine: rebuild the menu after a swap and then recompute the lock array, so the two
        # swapped required characters stay locked in their new positions.  The vanilla post-swap
        # path (C3/7613) does not refresh the lock array -- vanilla never needs to, because locked
        # slots can never move -- so the relock (C3/790C) is added here.
        space = Write(Bank.C3, [
            asm.JSR(0x7613, asm.ABS),       # list members / create actors after change
            asm.JSR(0x790c, asm.ABS),       # establish locked actor slots
            asm.RTS(),
        ], "require characters: recreate party-select and relock")
        recreate_and_relock = space.start_address

        # Choice 1 (pick up a slot, C3/717F): allow a locked slot to be picked up by NOPing the
        # "fail if locked" branch (BMI $71A2).  Whether the pick-up is legal is now decided at
        # placement time, by the like-lock comparison below.
        space = Reserve(0x3717f, 0x37180, "require characters: allow picking up locked slot")
        space.write(
            asm.NOP(),
            asm.NOP(),
        )

        # Choice 2 (choose a destination slot, C3/7222): replace "a = lock(dst)" with a call that
        # yields "lock(src) EOR lock(dst)".  The original "BMI <fail>" that immediately follows
        # (C3/7226) is left untouched, so the placement now fails only when the two slots' locked
        # status differs (locked<->unlocked), and succeeds for locked<->locked and unlocked<->
        # unlocked.
        space = Reserve(0x37222, 0x37225, "require characters: compare slot locks on placement")
        space.write(
            asm.JSR(like_lock_compare, asm.ABS),
            asm.NOP(),
        )

        # Swap handler (C3/7272): redirect the post-swap "create actors" call so it also recomputes
        # the lock array.
        space = Reserve(0x37272, 0x37274, "require characters: relock after swap")
        space.write(
            asm.JSR(recreate_and_relock, asm.ABS),
        )
