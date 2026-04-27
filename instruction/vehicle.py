from instruction.event import _Instruction, _Branch, _LoadMap
import data.event_bit as event_bit

class End(_Instruction):
    def __init__(self):
        super().__init__(0xff)

class SetPosition(_Instruction):
    def __init__(self, x, y):
        super().__init__(0xc7, x, y) # defined at ee/727b

    def __str__(self):
        return super().__str__(f"({self.args[0]}, {self.args[1]})")

class SetEventBit(_Instruction):
    def __init__(self, event_bit):
        self.event_bit = event_bit
        assert event_bit <= 0x6ff

        super().__init__(0xc8, self.event_bit.to_bytes(2, "little"))

    def __str__(self):
        return super().__str__(hex(self.event_bit))

class ClearEventBit(_Instruction):
    def __init__(self, event_bit):
        self.event_bit = event_bit
        assert event_bit <= 0x6ff

        super().__init__(0xc9, self.event_bit.to_bytes(2, "little"))

    def __str__(self):
        return super().__str__(hex(self.event_bit))

class BranchIfEventBitSet(_Branch):
    def __init__(self, event_bit, destination):
        self.event_bit = event_bit
        event_bit_arg = (event_bit | 0x8000).to_bytes(2, "little")

        super().__init__(0xb0, [event_bit_arg], destination)

    def __str__(self):
        return super().__str__(hex(self.event_bit))

class BranchIfEventBitClear(_Branch):
    def __init__(self, event_bit, destination):
        self.event_bit = event_bit
        event_bit_arg = event_bit.to_bytes(2, "little")

        super().__init__(0xb0, [event_bit_arg], destination)

    def __str__(self):
        return super().__str__(hex(self.event_bit))

class Branch(BranchIfEventBitClear):
    def __init__(self, destination):
        super().__init__(event_bit.ALWAYS_CLEAR, destination)

class _InvokeBattle(_Instruction):
    def __init__(self, pack, background, battle_sound, battle_animation):
        self.pack = pack

        pack_arg = pack - 0x100
        background_sound_animation = background
        if not battle_sound:
            background_sound_animation |= 0x40
        if not battle_animation:
            background_sound_animation |= 0x80

        super().__init__(0xcf, pack_arg, background_sound_animation)

    def __str__(self):
        return super().__str__(str(self.pack))

def InvokeBattle(pack, background = 0x3f, battle_sound = True, battle_animation = True):  # check_game_over = True
    InvokeBattle = type("InvokeBattle", (_InvokeBattle,), {})
    commands = [InvokeBattle(pack, background, battle_sound, battle_animation)]
    #if check_game_over:
    #    from instruction.field.functions import CHECK_GAME_OVER
    #    commands.append(Call(CHECK_GAME_OVER))
    return commands

# Custom vehicle-script opcode 0xE1: BranchProbability.
# Format: E1 cc dd_lo dd_mid dd_hi (5 bytes total).
#   cc        - 1-byte chance (0-255). Branch is taken iff RNG byte < cc.
#   dd_lo/mid/hi - 3-byte destination, encoded the same way the existing B0
#                  conditional-branch encodes its destination (caller passes a
#                  ROM offset; 0xCA is added by the handler to rebase to bank
#                  CA at run time).
#
# The vehicle dispatcher reads opcodes via `JMP ($76FB,X)` at SNES $EE/70A3.
# Opcodes E1-F2 are unused in the vanilla ROM (their pointer-table entries
# all dispatch to a no-op stub at $EE/74A4). We slot a real handler into
# the E1 table entry and write the handler ASM into Bank EE free space
# (memory/free.py declares 0x2eaf01-0x2eb1ff free, which corresponds to
# SNES $EEAF01-$EEB1FF, i.e. the unused 767-byte block per the FF6 ROM map).
#
# Installation is lazy: the first BranchProbability(...) constructor written
# in a build calls _install_branch_probability_handler() once, which writes
# the handler and patches the dispatch table.
_branch_probability_installed = False

def _set_vehicle_opcode_address(opcode, snes_handler_addr):
    # Vehicle-script opcode pointer table is at SNES $EE76FB
    # (= ROM offset 0x2e76fb), 256 entries * 2 bytes each. Each entry is the
    # low 16 bits of a SNES address inside Bank EE; the dispatcher does an
    # indirect `JMP ($76FB,X)` so the implicit program bank (EE) provides
    # the high byte.
    from memory.space import Reserve
    table_entry = 0x2e76fb + opcode * 2
    space = Reserve(table_entry, table_entry + 1,
                    f"vehicle opcode table {hex(opcode)}={hex(snes_handler_addr)}")
    space.write((snes_handler_addr & 0xffff).to_bytes(2, "little"))

def _install_branch_probability_handler():
    global _branch_probability_installed
    if _branch_probability_installed:
        return
    _branch_probability_installed = True

    # Local imports avoid taking a hard dependency on the Bank.EE heap and
    # the asm module at import time of this module.
    from memory.space import Bank, Write, START_ADDRESS_SNES
    import instruction.asm as asm

    # Vehicle script PC layout (Bank EE convention):
    #   $EA/$EB/$EC = 24-bit base address of the script
    #   $ED/$EE     = 16-bit offset within the script
    # On entry to a handler the dispatcher has already advanced $ED past
    # the opcode byte, so $ED points to operand 0 (the chance byte).
    # Register state on entry: A is 16-bit, X is 16-bit (= opcode * 2 from
    # the dispatcher's ASL+TAX), Y is 16-bit (the dispatcher used LDY $ED).
    src = [
        asm.A8(),                          # SEP #$20 - put A in 8-bit mode

        # Read chance byte at script offset $ED, stash in scratch DP $58.
        asm.LDY(0xed, asm.DIR),
        asm.LDA(0xea, asm.DIR_24_Y),       # A = [$EA],Y = chance byte
        asm.STA(0x58, asm.DIR),

        # Inline RNG, mirroring c0.rng but X-mode-safe. We need X 8-bit so
        # that LDA $C0FD00,X indexes correctly. Save/restore X (16-bit) so
        # the caller's X value (opcode*2) is preserved in case anything in
        # Bank EE relies on it after the handler returns to dispatch.
        asm.PHX(),
        asm.XY8(),                         # SEP #$10 - X/Y 8-bit
        asm.INC(0x1f6d, asm.ABS),          # ++ RNG index in SRAM
        asm.LDX(0x1f6d, asm.ABS),          # X = RNG index (8-bit)
        asm.LDA(0xc0fd00, asm.LNG_X),      # A = $C0FD00[X] = random byte
        asm.XY16(),                        # REP #$10 - X/Y back to 16-bit
        asm.PLX(),

        # If random < chance, take the branch.
        asm.CMP(0x58, asm.DIR),
        asm.BCC("BRANCH_TAKEN"),

        # Fall-through path: advance $ED past 4 operand bytes (chance +
        # 3-byte destination), then return to the dispatcher.
        asm.LDY(0xed, asm.DIR),
        asm.INY(),
        asm.INY(),
        asm.INY(),
        asm.INY(),
        asm.STY(0xed, asm.DIR),
        asm.JMP(0x7093, asm.ABS),

        "BRANCH_TAKEN",
        # Branch-taken path: rewrite script PC ($EA/$EB/$EC) to the encoded
        # destination, mirroring the tail of the vanilla B0 handler at
        # SNES $EE/715F. The destination's high byte is rebased by adding
        # 0xCA so that callers can pass a Bank-CA-relative offset (the
        # convention used by all existing vehicle-script destinations).
        asm.LDY(0xed, asm.DIR),
        asm.INY(),                         # skip past the chance byte
        asm.LDA(0xea, asm.DIR_24_Y),       # dest_low
        asm.STA(0x6a, asm.DIR),
        asm.INY(),
        asm.LDA(0xea, asm.DIR_24_Y),       # dest_mid
        asm.STA(0x6b, asm.DIR),
        asm.INY(),
        asm.LDA(0xea, asm.DIR_24_Y),       # dest_high
        asm.CLC(),
        asm.ADC(0xca, asm.IMM8),           # rebase to bank CA
        asm.STA(0xec, asm.DIR),
        asm.LDY(0x6a, asm.DIR),            # 16-bit Y reads $6A:$6B
        asm.STY(0xea, asm.DIR),            # and writes $EA:$EB in one op
        asm.STZ(0xed, asm.DIR),
        asm.STZ(0xee, asm.DIR),
        asm.JMP(0x7093, asm.ABS),
    ]
    handler_space = Write(Bank.EE, src,
                          "vehicle BranchProbability handler")
    handler_snes = START_ADDRESS_SNES + handler_space.start_address

    _set_vehicle_opcode_address(BranchProbability.OPCODE, handler_snes)

class BranchProbability(_Branch):
    OPCODE = 0xe1

    def __init__(self, chance, destination):
        self.chance = chance
        if chance > 255 or chance < 0:
            raise ValueError(f"branch_probability: invalid chance {chance}")
        if chance <= 1:
            chance = int(chance * 255)
        _install_branch_probability_handler()
        super().__init__(self.OPCODE, [chance], destination)

    def __str__(self):
        return super().__str__(f"{self.chance:0.3}")

class FadeLoadMap(_LoadMap):
    # same as load_map, except fades out screen
    def __init__(self, map_id, direction, default_music, x, y, fade_in = False, entrance_event = False,
                 airship = False, chocobo = False, update_parent_map = False, unknown = False):

        super().__init__(0xd2, map_id, direction, default_music, x, y,
                         fade_in, entrance_event, airship, chocobo, update_parent_map, unknown)

class LoadMap(_LoadMap):
    def __init__(self, map_id, direction, default_music, x, y, fade_in = False, entrance_event = False,
                 airship = False, chocobo = False, update_parent_map = False, unknown = False):

        super().__init__(0xd3, map_id, direction, default_music, x, y,
                         fade_in, entrance_event, airship, chocobo, update_parent_map, unknown)

class MoveForward(_Instruction):
    def __init__(self, direction, distance):
        self.direction = direction
        self.distance = distance

        import data.direction

        if direction == data.direction.UP:
            opcode = 0x24
        elif direction == data.direction.RIGHT:
            opcode = 0x0c
        elif direction == data.direction.DOWN:
            opcode = 0x44
        elif direction == data.direction.LEFT:
            opcode = 0x14
        else:
            opcode = 0x04

        super().__init__(opcode, distance)

    def __str__(self):
        return super().__str__(f"{str(self.direction)} {str(self.distance)}")

class BecomeShip(_Instruction):
    def __init__(self):
        super().__init__(0xfc)
