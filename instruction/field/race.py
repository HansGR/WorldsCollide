"""Race builds: the check-reward command family (L3 / L3-C).

Everything a converted check's script needs to grant, name, and stage a
reward without the reward appearing in the rom: the $9E grant, the $EE
reward dialog, the <reward>/<reward2> message codes, and the $EC
reward-entity umbrella.  See RACE_OBFUSCATION_PLAN.md for the design and
obfuscation/rewards.py for the table the slots index.  Non-race builds
never emit any of it.
"""
from memory.space import Bank, START_ADDRESS_SNES, Reserve, Write, Read
from instruction.event import _Instruction
import instruction.asm as asm
import instruction.c0 as c0
import args

from instruction.field.custom import _set_opcode_address

# --- L3: check rewards -------------------------------------------------
#
# Everything about a check reward - which kind it is and which one - lives
# in one masked table (obfuscation/rewards.py); scripts carry only an
# opaque slot.  Items and espers deliberately share the table, the grant
# command and the name-rendering control code, so nothing static tells an
# esper check from an item check: each dispatches on the kind byte it
# decodes at runtime.
#
# Control codes are installed by chaining onto the end of the message
# engine's control-code dispatch, where a byte matching nothing falls
# through to the literal-character path:
#
#   $1C <reward>   name of the reward whose slot is in $0584
#   $1D <reward2>  name of the reward in the NEXT slot, for the one dialog
#                  that names two rewards at once (the Narshe WOR choice)
#
# $0584 is "Spell Index for Dialog Window Display", documented as unused
# in the US release (a leftover from FF6j).  $0583 is deliberately left
# alone: it is the item index vanilla's own <item> code reads, and the
# chest-opening path sets it.
CHAIN_END = 0x0844b             # C0/844B: SEC : SBC #$1b, the literal path
CHAIN_RESUME = 0x844e

REWARD_CODE = 0x1c
REWARD2_CODE = 0x1d
REWARD_SLOT = 0x0584

ESPER_NAMES_SNES = 0xe6f6e1     # 8 bytes/entry, $ff padded
ESPER_NAME_LENGTH = 8
ESPER_NAME_STRIDE = 8
ITEM_NAMES_SNES = 0xd2b301      # 13 bytes/entry: icon byte then 12 chars
ITEM_NAME_LENGTH = 12
ITEM_NAME_STRIDE = 13
CHARACTER_NAMES_WRAM = 0x1602   # in character data, 37 bytes/record
CHARACTER_NAME_LENGTH = 6
CHARACTER_NAME_STRIDE = 37      # sizeof character data record

TEXT_BUFFER = 0x9183            # $7E9183, the message engine's text buffer
TEXT2_TO_TEXT1 = 0x60           # name charset -> dialog charset
NAME_PAD = 0xff - TEXT2_TO_TEXT1

_name_codes = None

def _reward_table():
    from obfuscation import claim
    from obfuscation.claim import snes
    layout = claim.layout(args)
    return snes(layout["rewards"]), snes(layout["rewards_pad"])

def _index_slot_src():
    """asm: X = (slot in A) * reward entry size.

    Ends with TDC: for slots >= 0x80 the 16-bit ASL leaves b (the
    accumulator high byte) set, and the vanilla handlers the reward code
    jumps into transfer b along with a in their TAX/TAY, spraying indexed
    writes 0x100 bytes off.  Every consumer of a slot index goes through
    here so that rule has one home (and one verifier check).
    """
    return [
        asm.REP(0x20),
        asm.AND(0x00ff, asm.IMM16),
        asm.ASL(),
        asm.TAX(),
        asm.SEP(0x20),
        asm.TDC(),
    ]

def _decode_slot_src(field):
    """asm reading one masked byte of the reward slot in X (X = slot * 2)."""
    table, pad = _reward_table()
    return [asm.LDA(table + field, asm.LNG_X),
            asm.EOR(pad + field, asm.LNG_X)]

def _copy_name_src(tag, names_snes, stride, length, wram = False):
    """asm copying a name into the message engine's text buffer.

    A holds the id on entry.  Mirrors vanilla's <item>/<skill> handlers:
    multiply by the table stride, convert each character from the name
    charset to the dialog charset, and stop at the name's $ff padding.

    `wram` reads the name from work ram instead of a rom table (character
    names live at $1602 + 37*id): the data bank is already $7E for the
    text buffer stores, and $7E1602 addresses the same low WRAM the
    vanilla name code reads through the bank $00 mirror.
    """
    copy, done = f"COPY_{tag}", f"DONE_{tag}"
    load = (asm.LDA(names_snes, asm.ABS_X) if wram
            else asm.LDA(names_snes, asm.LNG_X))
    return [
        asm.STA(0x4202, asm.ABS),
        asm.LDA(stride, asm.IMM8),
        asm.STA(0x4203, asm.ABS),
        asm.NOP(),
        asm.NOP(),
        asm.NOP(),
        asm.NOP(),                          # multiplier settle time
        asm.LDX(0x4216, asm.ABS),           # X = id * stride (16-bit X)
        asm.LDY(0x00, asm.DIR),             # Y = text buffer offset
        asm.LDA(0x7e, asm.IMM8),
        asm.PHA(),
        asm.PLB(),                          # data bank = $7E for the stores

        copy,
        load,
        asm.SEC(),
        asm.SBC(TEXT2_TO_TEXT1, asm.IMM8),
        asm.STA(TEXT_BUFFER, asm.ABS_Y),
        asm.CMP(NAME_PAD, asm.IMM8),        # name padding: stop here
        asm.BEQ(done),
        asm.INX(),
        asm.INY(),
        asm.CPY(length, asm.IMM16),
        asm.BNE(copy),

        done,
        asm.TDC(),
        asm.STA(TEXT_BUFFER, asm.ABS_Y),    # terminate the substitution
        asm.TDC(),
        asm.PHA(),
        asm.PLB(),                          # data bank back to $00
        asm.STZ(0xcf, asm.DIR),
        asm.JMP(0x8263, asm.ABS),           # back to the message engine
    ]

def name_codes():
    """Install the <reward>/<reward2> control codes (once)."""
    global _name_codes
    if _name_codes is not None:
        return _name_codes

    src = [
        # dispatch: ours, or the displaced literal-character path
        asm.CMP(REWARD_CODE, asm.IMM8),
        asm.BEQ("REWARD"),
        asm.CMP(REWARD2_CODE, asm.IMM8),
        asm.BEQ("REWARD2"),
        asm.SEC(),                          # displaced from C0/844B
        asm.SBC(0x1b, asm.IMM8),
        asm.JMP(CHAIN_RESUME, asm.ABS),

        # entry state at every control code: A 8-bit, X/Y 16-bit,
        # direct page $00 = current offset into the text buffer
        "REWARD2",
        asm.LDA(REWARD_SLOT, asm.ABS),
        asm.INC(),                        # the reward after this one
        asm.BRA("LOOKUP"),

        "REWARD",
        asm.LDA(REWARD_SLOT, asm.ABS),

        "LOOKUP",
        *_index_slot_src(),                 # X = slot * 2 (entry size)

        *_decode_slot_src(0),               # kind
        asm.BNE("NOT_ITEM_NAME"),
        *_decode_slot_src(1),               # item id
        *_copy_name_src("ITEM", ITEM_NAMES_SNES, ITEM_NAME_STRIDE, ITEM_NAME_LENGTH),

        "NOT_ITEM_NAME",
        asm.CMP(0x01, asm.IMM8),
        asm.BNE("CHARACTER_NAME"),
        *_decode_slot_src(1),               # esper id
        *_copy_name_src("ESPER", ESPER_NAMES_SNES, ESPER_NAME_STRIDE, ESPER_NAME_LENGTH),

        # character names live in work ram (so renames render right), in
        # the same charset as the rom name tables - the same copy loop
        # with a wram source, exactly as vanilla's own <TERRA>-style
        # codes read them (C0/82CC)
        "CHARACTER_NAME",
        *_decode_slot_src(1),               # character id
        *_copy_name_src("CHARACTER", CHARACTER_NAMES_WRAM,
                        CHARACTER_NAME_STRIDE, CHARACTER_NAME_LENGTH,
                        wram = True),
    ]
    space = Write(Bank.C0, src, "race: <reward>/<reward2> message control codes")
    _name_codes = space.start_address

    space = Reserve(CHAIN_END, CHAIN_END + 2, "race: reward name control code hook")
    space.write(asm.JMP(_name_codes, asm.ABS))
    return _name_codes


ADD_CHECK_REWARD_OPCODE = 0x9e  # unused by vanilla, WC dev and the fork
_add_check_reward_handler = None

def add_check_reward_opcode():
    """Write the reward-grant handler once and return its opcode.

    One command grants any kind: it decodes (kind, id) from the masked
    table and runs the vanilla add-inventory routine, the vanilla
    AddEsper handler, or WC's recruit_character function accordingly.
    It also leaves the slot in $0584 so a receive dialog that follows
    the grant can name it without carrying its own copy.
    """
    global _add_check_reward_handler
    if _add_check_reward_handler is None:
        name_codes()

        src = [
            asm.LDA(0xeb, asm.DIR),         # slot (command operand)
            asm.STA(REWARD_SLOT, asm.ABS),  # for a dialog after the grant
            *_index_slot_src(),             # X = slot * 2

            *_decode_slot_src(0),           # kind
            asm.BNE("NOT_ITEM"),

            *_decode_slot_src(1),           # item id
            asm.STA(0x1a, asm.DIR),         # the add-inventory routine
            asm.STA(0x0583, asm.ABS),       # vanilla's <item> index, as the
                                            # chest path at C0/4C86 sets it
            asm.JSR(0xacfc, asm.ABS),       # vanilla add-to-inventory
            asm.LDA(0x02, asm.IMM8),        # command size (opcode + slot)
            asm.JMP(0x9b5c, asm.ABS),       # next command

            "NOT_ITEM",
            asm.CMP(0x01, asm.IMM8),
            asm.BNE("GRANT_CHARACTER"),

            *_decode_slot_src(1),           # esper id
            asm.CLC(),
            asm.ADC(0x36, asm.IMM8),        # the form the $86 handler reads
            asm.STA(0xeb, asm.DIR),
            asm.JMP(0xadb8, asm.ABS),       # vanilla AddEsper (grant + next)

            "GRANT_CHARACTER",
            *_decode_slot_src(1),           # character id
            asm.STA(0xeb, asm.DIR),         # recruit_character's argument
            asm.JSL(START_ADDRESS_SNES + c0.recruit_character),
            asm.LDA(0x02, asm.IMM8),        # command size (opcode + slot)
            asm.JMP(0x9b5c, asm.ABS),       # next command
        ]
        space = Write(Bank.C0, src, "race: add check reward (decode + grant)")
        _set_opcode_address(ADD_CHECK_REWARD_OPCODE, space.start_address)
        _add_check_reward_handler = space.start_address
    return ADD_CHECK_REWARD_OPCODE

class AddCheckReward(_Instruction):
    """Race builds: grant the reward in a slot, kind decided at runtime."""
    def __init__(self, slot):
        super().__init__(add_check_reward_opcode(), slot)

    def __str__(self):
        return super().__str__(self.args[0])


REWARD_DIALOG_OPCODE = 0xee     # unused by vanilla, WC dev and the fork
_reward_dialog_handler = None

def reward_dialog_opcode():
    """Write the reward-dialog handler once and return its opcode.

    Three bytes, so it drops straight onto a vanilla Dialog command with
    no script shifting.  Its operand is a slot in the masked dialog side
    table, holding the reward slot and two dialog ids; the handler puts
    the reward slot where <reward> will find it, picks the dialog whose
    wording matches the reward's kind, and hands off to $4B at C0/A4BC -
    which advances the script by 3, exactly this command's length.

    Because the dialog decodes the reward itself, it works whether the
    event grants before or after showing the text; and because the kind
    only decides things at runtime, the script looks the same either way.
    """
    global _reward_dialog_handler
    if _reward_dialog_handler is None:
        from obfuscation import claim
        from obfuscation.claim import snes
        from obfuscation.rewards import DIALOG_SLOT_SIZE

        name_codes()

        layout = claim.layout(args)
        slots, slots_pad = snes(layout["reward_dialogs"]), snes(layout["reward_dialogs_pad"])

        def dialog_field(offset):
            return [asm.LDA(slots + offset, asm.LNG_X),
                    asm.EOR(slots_pad + offset, asm.LNG_X)]

        src = [
            # X = dialog slot * entry size, via the hardware multiplier
            asm.LDA(0xeb, asm.DIR),
            asm.STA(0x4202, asm.ABS),
            asm.LDA(DIALOG_SLOT_SIZE, asm.IMM8),
            asm.STA(0x4203, asm.ABS),
            asm.NOP(),
            asm.NOP(),
            asm.NOP(),
            asm.NOP(),                      # multiplier settle time
            asm.LDX(0x4216, asm.ABS),

            *dialog_field(0),               # reward slot
            asm.STA(REWARD_SLOT, asm.ABS),  # what <reward> will render

            # pick the wording that matches the reward's kind.  X is still
            # the dialog slot offset, so read both ids before touching it
            *dialog_field(1), asm.STA(0xeb, asm.DIR),
            *dialog_field(2), asm.STA(0xec, asm.DIR),
            *dialog_field(3), asm.PHA(),
            *dialog_field(4), asm.PHA(),

            # kind of the reward this dialog names
            asm.LDA(REWARD_SLOT, asm.ABS),
            *_index_slot_src(),
            *_decode_slot_src(0),
            asm.CMP(0x01, asm.IMM8),
            asm.BNE("SHOW"),                # not an esper: first wording.
                                            # characters only appear in
                                            # bespoke dialogs, which are
                                            # registered with one wording
                                            # in both ids, so the first is
                                            # always right for them

            asm.PLA(),                      # esper: use the second
            asm.STA(0xec, asm.DIR),
            asm.PLA(),
            asm.STA(0xeb, asm.DIR),
            asm.JMP(0xa4bc, asm.ABS),       # $4B dialog handler (advances 3)

            "SHOW",
            asm.PLA(),                      # discard the esper wording
            asm.PLA(),
            asm.JMP(0xa4bc, asm.ABS),
        ]
        space = Write(Bank.C0, src, "race: reward dialog (decode name + show)")
        _set_opcode_address(REWARD_DIALOG_OPCODE, space.start_address)
        _reward_dialog_handler = space.start_address
    return REWARD_DIALOG_OPCODE

class RewardDialog(_Instruction):
    """Race builds: a dialog naming a reward, decoded at display time."""
    def __init__(self, slot, item_dialog, esper_dialog):
        from obfuscation import rewards
        entry = rewards.register_dialog(slot, item_dialog, esper_dialog)
        # third byte pads to the 3 bytes the vanilla dialog handler
        # advances by
        super().__init__(reward_dialog_opcode(), entry, 0x00)

    def __str__(self):
        return super().__str__(self.args[0])


def _dialog_arg(dialog_id, wait_for_input = True, inside_text_box = True,
                top_of_screen = True):
    """The 16-bit operand the vanilla $4B dialog handler expects: the
    dialog id with the display flags in bits 14-15 (same encoding as
    field.Dialog).  RewardDialog stores this whole value in its side
    table, so the flags survive the indirection."""
    # the handler hands off to the $4B path; $48 (no input wait) has a
    # different handler, and no reward dialog uses it
    assert wait_for_input, "RewardDialog only supports wait_for_input"
    if not inside_text_box and top_of_screen:
        return dialog_id | 0x4000
    elif inside_text_box and not top_of_screen:
        return dialog_id | 0x8000
    elif not inside_text_box and not top_of_screen:
        return dialog_id | 0xc000
    return dialog_id


def reward_dialog(kind, value, dialog_id, second_item = None, **dialog_args):
    """Dialog naming a check reward: opaque in race builds, plain otherwise.

    `second_item` is for a dialog naming two rewards at once; it is
    registered in the next slot and rendered by <reward2>.
    """
    if not args.race:
        import instruction.field as field
        return field.Dialog(dialog_id, **dialog_args)
    from obfuscation import rewards
    if second_item is None:
        slot = rewards.register(kind, value)
    else:
        slot = rewards.register_pair(kind, value, second_item)
    arg = _dialog_arg(dialog_id, **dialog_args)
    return RewardDialog(slot, arg, arg)


def reward_slot_dialog(slot, dialog_id, **dialog_args):
    """Race builds: a bespoke dialog naming an already-registered slot
    (one wording for every kind - <reward> renders the right name)."""
    arg = _dialog_arg(dialog_id, **dialog_args)
    return RewardDialog(slot, arg, arg)


def receive_reward_dialog(slot):
    """Race builds: the standard receive dialog for a slot - vanilla's
    item wording or magicite wording, picked by the decoded kind."""
    from obfuscation import rewards
    item_wording, esper_wording = rewards.wordings()
    return RewardDialog(slot, item_wording, esper_wording)


def ReceiveCheckReward(slot):
    """Race builds: the standard esper/item receive - grant, chime,
    receive dialog - as one instruction group (the shape every converted
    check's esper/item arm uses)."""
    from instruction.field.instructions import PlaySoundEffect
    return (AddCheckReward(slot), PlaySoundEffect(141), receive_reward_dialog(slot))


# --- L3-C: character rewards - the RewardEntity command family ---------
#
# A character check's scene needs the character's id in many more places
# than the grant: the map NPC's sprite and palette, create/show/hide and
# action-queue commands (whose operand - or opcode, for action queues -
# is the entity id, which for party characters IS the character id), the
# party add, the naming screen, the character theme.  Every one of those
# id-valued operands is a placement leak.
#
# One umbrella opcode replaces them all: `$EC sub slot [extra...]`.  Each
# sub-command decodes the character id out of the masked reward table and
# then jumps INTO the corresponding vanilla handler with the id placed
# where that handler's own operand would be ($eb/$ec/$ea), so the runtime
# semantics are exactly vanilla's.  Where the vanilla command is shorter
# than ours (our sub and slot bytes replace its one id byte), the
# sub-handler first advances the script pointer by the difference, so the
# vanilla handler's own "advance by n" lands past our whole command.
#
# An umbrella rather than a dozen opcodes because vanilla only leaves 21
# unused slots in the command table and most are already claimed (WC dev,
# this branch, and the door-rando fork); $EC is one of the last four
# genuinely free bytes ($EC/$ED/$FC/$FF).
REWARD_ENTITY_OPCODE = 0xec     # unused by vanilla, WC dev and the fork

(SUB_CREATE, SUB_DELETE, SUB_SHOW, SUB_HIDE, SUB_WAIT, SUB_SPRITE,
 SUB_PALETTE, SUB_PARTY, SUB_PROPERTIES, SUB_NAME, SUB_THEME, SUB_ACT,
 SUB_LOAD_KIND, SUB_VEHICLE, SUB_SPLIT, SUB_RESTORE_HP,
 SUB_RESTORE_MP) = range(17)

_reward_entity_handler = None
_character_palette_table = None


def reset_build():
    """Forget the once-per-build handlers so the next in-process build
    writes them afresh (see obfuscation.reset_build)."""
    global _name_codes, _add_check_reward_handler, _reward_dialog_handler
    global _reward_entity_handler, _character_palette_table
    _name_codes = None
    _add_check_reward_handler = None
    _reward_dialog_handler = None
    _reward_entity_handler = None
    _character_palette_table = None


def _slot_to_x_src(operand_dp):
    """asm: X = (slot at the given operand byte) * reward entry size
    (see _index_slot_src for the trailing TDC)."""
    return [asm.LDA(operand_dp, asm.DIR), *_index_slot_src()]


def _decode_id_src(operand_dp):
    """asm: A = character id of the reward slot at the given operand."""
    return [*_slot_to_x_src(operand_dp), *_decode_slot_src(1)]


def _bump_src(tag, count = 1):
    """asm: advance the event script pointer ($e5-$e7, 24-bit) by count.

    Used before jumping into a vanilla handler whose command is `count`
    bytes shorter than ours, so its own final "advance by n" ends up
    exactly past our command.
    """
    src = []
    for i in range(count):
        done = f"BUMPED_{tag}_{i}"
        src += [
            asm.INC(0xe5, asm.DIR),
            asm.BNE(done),
            asm.INC(0xe6, asm.DIR),
            asm.BNE(done),
            asm.INC(0xe7, asm.DIR),
            done,
        ]
    return src


def character_palette_table():
    """rom address of the 16-entry character id -> palette table.

    Allocated (zeroed) with the handler; data.py fills it at write time
    from the build's Characters, because palettes can be customized by
    flags.  Flag-derived, so it is public information and lives in
    plaintext.
    """
    reward_entity_opcode()
    return _character_palette_table


def fill_character_palettes(get_palette):
    """Late-fill the palette table (no-op if no character command was
    ever emitted).  `get_palette` is Characters.get_palette."""
    if _character_palette_table is None:
        return
    from memory.space import Space
    from data.characters import Characters
    values = [get_palette(c) & 0xff for c in range(Characters.CHARACTER_COUNT)]
    Space.rom.set_bytes(_character_palette_table,
                        values + [0x00] * (16 - len(values)))


def reward_entity_opcode():
    """Write the reward-entity sub-handlers once and return the opcode."""
    global _reward_entity_handler, _character_palette_table
    if _reward_entity_handler is not None:
        return REWARD_ENTITY_OPCODE

    from music.song_utils import character_to_song

    NEXT_COMMAND = 0x9b5c
    # vanilla handlers, each entered with the decoded id where its own
    # operand would be (addresses from the vanilla command pointer table)
    VANILLA = {
        "create": 0x9e3c,       # $3D, advance 2
        "delete": 0x9e67,       # $3E, advance 2
        "show": 0xa2fa,         # $41, advance 2
        "hide": 0xa336,         # $42, advance 2
        "wait": 0x9c44,         # $35, advance 2
        "sprite": 0x9c8f,       # $37, advance 3
        "palette": 0x9ca9,      # $43, advance 3
        "party": 0x9d3b,        # $3F, advance 3
        "properties": 0xa07c,   # $40, advance 3
        "name": 0xa03a,         # $7F, advance 3
        "theme": 0xb780,        # $F0, advance 2
        "act": 0x9ba5,          # action queue, entered with A = entity
        "vehicle": 0x9cca,      # $44, advance 3
        "hp": 0xae7b,           # $8B, advance 3
        "mp": 0xaf3e,           # $8C, advance 3
    }

    # the sixteen-entry character id -> palette and -> theme song tables.
    # both mappings are public (palettes follow from flags, themes are
    # fixed knowledge), so plaintext is fine.
    space = Write(Bank.C0, [bytes(16)], "race: character palette table")
    _character_palette_table = space.start_address
    palette_table_snes = START_ADDRESS_SNES + _character_palette_table

    themes = bytes(character_to_song.get(c, 0) for c in range(16))
    space = Write(Bank.C0, [themes], "race: character theme table")
    theme_table_snes = START_ADDRESS_SNES + space.start_address

    def entity_sub(tag, target):
        # $EC sub slot (3 bytes); vanilla: $op id (2 bytes, reads $eb)
        return [
            *_decode_id_src(0xec),
            asm.STA(0xeb, asm.DIR),
            *_bump_src(tag),
            asm.JMP(target, asm.ABS),
        ]

    def pair_sub(tag, target):
        # $EC sub slot (3 bytes); vanilla: $op id id (3 bytes, and for
        # these commands both operands are the character id)
        return [
            *_decode_id_src(0xec),
            asm.STA(0xeb, asm.DIR),
            asm.STA(0xec, asm.DIR),
            asm.JMP(target, asm.ABS),
        ]

    def table_lookup_src(operand_dp, table_snes):
        # A = table[id of the reward slot at the operand].  TDC before
        # TAX so the high byte of 16-bit X is clean.
        return [
            *_decode_id_src(operand_dp),
            asm.STA(0x1a, asm.DIR),
            asm.TDC(),
            asm.LDA(0x1a, asm.DIR),
            asm.TAX(),
            asm.LDA(table_snes, asm.LNG_X),
        ]

    subs = {}

    subs[SUB_CREATE] = entity_sub("CREATE", VANILLA["create"])
    subs[SUB_DELETE] = entity_sub("DELETE", VANILLA["delete"])
    subs[SUB_SHOW] = entity_sub("SHOW", VANILLA["show"])
    subs[SUB_HIDE] = entity_sub("HIDE", VANILLA["hide"])
    subs[SUB_WAIT] = entity_sub("WAIT", VANILLA["wait"])

    # $EC sub entity slot (4 bytes); vanilla $37: entity sprite.  for
    # party characters the sprite id IS the character id.
    subs[SUB_SPRITE] = [
        *_decode_id_src(0xed),
        asm.PHA(),
        asm.LDA(0xec, asm.DIR),         # entity operand (not secret)
        asm.STA(0xeb, asm.DIR),
        asm.PLA(),
        asm.STA(0xec, asm.DIR),         # decoded id as the sprite
        *_bump_src("SPRITE"),
        asm.JMP(VANILLA["sprite"], asm.ABS),
    ]

    # $EC sub entity slot (4 bytes); vanilla $43: entity palette
    subs[SUB_PALETTE] = [
        *table_lookup_src(0xed, palette_table_snes),
        asm.PHA(),
        asm.LDA(0xec, asm.DIR),
        asm.STA(0xeb, asm.DIR),
        asm.PLA(),
        asm.STA(0xec, asm.DIR),
        *_bump_src("PALETTE"),
        asm.JMP(VANILLA["palette"], asm.ABS),
    ]

    # $EC sub slot party (4 bytes); vanilla $3F: character party
    subs[SUB_PARTY] = [
        *_decode_id_src(0xec),
        asm.STA(0xeb, asm.DIR),
        asm.LDA(0xed, asm.DIR),
        asm.STA(0xec, asm.DIR),
        *_bump_src("PARTY"),
        asm.JMP(VANILLA["party"], asm.ABS),
    ]

    # vanilla $40/$7F take (character, data index) where the data index
    # equals the character id at every reward site
    subs[SUB_PROPERTIES] = pair_sub("PROPERTIES", VANILLA["properties"])
    subs[SUB_NAME] = pair_sub("NAME", VANILLA["name"])

    # $EC sub slot amount (4 bytes); vanilla $8B/$8C: character hp/mp
    # (the pre-battle joins restore the joining character before they
    # fight, matching the non-race scripts)
    for sub, target in ((SUB_RESTORE_HP, VANILLA["hp"]),
                        (SUB_RESTORE_MP, VANILLA["mp"])):
        subs[sub] = [
            *_decode_id_src(0xec),
            asm.STA(0xeb, asm.DIR),
            asm.LDA(0xed, asm.DIR),
            asm.STA(0xec, asm.DIR),
            *_bump_src(f"RESTORE_{sub}"),
            asm.JMP(target, asm.ABS),
        ]

    # $EC sub slot (3 bytes); vanilla $F0: song
    subs[SUB_THEME] = [
        *table_lookup_src(0xec, theme_table_snes),
        asm.STA(0xeb, asm.DIR),
        *_bump_src("THEME"),
        asm.JMP(VANILLA["theme"], asm.ABS),
    ]

    # $EC sub slot len actions... ; vanilla: id len actions...  The
    # vanilla routine is entered with A = the entity (normally the
    # command byte itself), re-reads it from $ea on the wait path, takes
    # the length byte from $eb, and treats script+2 as the queue start -
    # so give it all three and shift the script pointer under it by our
    # two extra bytes.
    subs[SUB_ACT] = [
        *_decode_id_src(0xec),
        asm.STA(0xea, asm.DIR),
        asm.LDA(0xed, asm.DIR),
        asm.STA(0xeb, asm.DIR),
        *_bump_src("ACT", 2),
        asm.LDA(0xea, asm.DIR),
        asm.JMP(VANILLA["act"], asm.ABS),
    ]

    # $EC sub slot vehicle (4 bytes); vanilla $44: character vehicle
    subs[SUB_VEHICLE] = [
        *_decode_id_src(0xec),
        asm.STA(0xeb, asm.DIR),
        asm.LDA(0xed, asm.DIR),
        asm.STA(0xec, asm.DIR),
        *_bump_src("VEHICLE"),
        asm.JMP(VANILLA["vehicle"], asm.ABS),
    ]

    # $EC sub entity bits (4 bytes, both operands literal).  The npc
    # loader (C0/53D0) derives an object's special-animation state -
    # $088C = ..a nn ggg (a enable, nn frame type, ggg graphic offset) -
    # from the record's split_sprite/direction bits at map load; this
    # ORs the same state into the live object so an entrance event can
    # turn a decoy record into vanilla's magicite/chest look at runtime.
    ENTITY_OFFSET = 0x9df0          # Y = object number in $eb * 0x29
    subs[SUB_SPLIT] = [
        asm.LDA(0xec, asm.DIR),     # entity operand (not secret)
        asm.STA(0xeb, asm.DIR),
        asm.JSR(ENTITY_OFFSET, asm.ABS),
        asm.LDA(0xed, asm.DIR),     # special animation bits (not secret)
        asm.ORA(0x088c, asm.ABS_Y),
        asm.STA(0x088c, asm.ABS_Y),
        asm.LDA(0x04, asm.IMM8),    # command size
        asm.JMP(NEXT_COMMAND, asm.ABS),
    ]

    # $EC sub slot kind (4 bytes): multipurpose event bit 0 = (the
    # reward's kind == kind).  With the vanilla event-bit branches this
    # gives runtime branching on kind, so one script can carry every
    # kind's scene and a diff cannot tell which one runs.
    import data.event_bit as event_bit
    result_byte = event_bit.address(event_bit.multipurpose(0))
    subs[SUB_LOAD_KIND] = [
        *_slot_to_x_src(0xec),
        *_decode_slot_src(0),           # kind
        asm.CMP(0xed, asm.DIR),
        asm.BEQ("KIND_MATCH"),
        asm.LDA(0x00, asm.IMM8),
        asm.BRA("KIND_STORE"),
        "KIND_MATCH",
        asm.LDA(0x01, asm.IMM8),
        "KIND_STORE",
        asm.STA(result_byte, asm.ABS),
        asm.LDA(0x04, asm.IMM8),        # command size
        asm.JMP(NEXT_COMMAND, asm.ABS),
    ]

    addresses = {}
    for sub, src in subs.items():
        space = Write(Bank.C0, src, f"race: reward entity sub-command {sub}")
        addresses[sub] = space.start_address

    table = b"".join((addresses[sub] & 0xffff).to_bytes(2, "little")
                     for sub in range(len(subs)))
    space = Write(Bank.C0, [table], "race: reward entity dispatch table")
    table_address = space.start_address & 0xffff

    space = Write(Bank.C0, [
        asm.TDC(),
        asm.LDA(0xeb, asm.DIR),         # sub-command
        asm.ASL(),
        asm.TAX(),
        asm.JMP(table_address, asm.ABS_X_16),
    ], "race: reward entity dispatch")
    _set_opcode_address(REWARD_ENTITY_OPCODE, space.start_address)
    _reward_entity_handler = space.start_address
    return REWARD_ENTITY_OPCODE


class _RewardEntityInstruction(_Instruction):
    def __init__(self, sub, *operands):
        super().__init__(reward_entity_opcode(), sub, *operands)

    def __str__(self):
        return super().__str__(f"slot {self.args[1]}")


class CreateRewardEntity(_RewardEntityInstruction):
    def __init__(self, slot):
        super().__init__(SUB_CREATE, slot)

class DeleteRewardEntity(_RewardEntityInstruction):
    def __init__(self, slot):
        super().__init__(SUB_DELETE, slot)

class ShowRewardEntity(_RewardEntityInstruction):
    def __init__(self, slot):
        super().__init__(SUB_SHOW, slot)

class HideRewardEntity(_RewardEntityInstruction):
    def __init__(self, slot):
        super().__init__(SUB_HIDE, slot)

class WaitForRewardEntityAct(_RewardEntityInstruction):
    def __init__(self, slot):
        super().__init__(SUB_WAIT, slot)

class SetRewardSprite(_RewardEntityInstruction):
    def __init__(self, entity, slot):
        super().__init__(SUB_SPRITE, entity, slot)

    def __str__(self):
        return _Instruction.__str__(self, f"{self.args[1]} slot {self.args[2]}")

class SetRewardPalette(_RewardEntityInstruction):
    def __init__(self, entity, slot):
        super().__init__(SUB_PALETTE, entity, slot)

    def __str__(self):
        return _Instruction.__str__(self, f"{self.args[1]} slot {self.args[2]}")

class AddRewardToParty(_RewardEntityInstruction):
    def __init__(self, slot, party):
        super().__init__(SUB_PARTY, slot, party)

class SetRewardProperties(_RewardEntityInstruction):
    def __init__(self, slot):
        super().__init__(SUB_PROPERTIES, slot)

class SetRewardName(_RewardEntityInstruction):
    def __init__(self, slot):
        super().__init__(SUB_NAME, slot)

class PlayRewardTheme(_RewardEntityInstruction):
    def __init__(self, slot):
        super().__init__(SUB_THEME, slot)

class SetRewardVehicle(_RewardEntityInstruction):
    def __init__(self, slot, vehicle):
        super().__init__(SUB_VEHICLE, slot, vehicle)


class RestoreRewardHp(_RewardEntityInstruction):
    def __init__(self, slot, amount):
        super().__init__(SUB_RESTORE_HP, slot, amount)

class RestoreRewardMp(_RewardEntityInstruction):
    def __init__(self, slot, amount):
        super().__init__(SUB_RESTORE_MP, slot, amount)


class SetSplitSprite(_RewardEntityInstruction):
    """Give an entity the special-animation state the npc loader derives
    from a record's split_sprite flag, so a decoy record can take on
    vanilla's magicite/chest object look at runtime.  `direction` picks
    the animation frame type exactly as the record's direction bits
    would (magicite faces UP, the item chest DOWN)."""
    def __init__(self, entity, direction):
        super().__init__(SUB_SPLIT, entity,
                         0x20 | 0x02 | ((direction & 0x03) << 3))

    def __str__(self):
        return _Instruction.__str__(self, f"{self.args[1]} {self.args[2]:#04x}")


class _RewardEntityAct(_Instruction):
    """Action queue for the reward character - the opaque twin of
    EntityAct, whose opcode byte would otherwise be the character id."""
    def __init__(self, slot, wait_until_complete, *actions):
        import instruction.field.entity as field_entity
        actions = list(actions) + [field_entity.End()]

        self.actions_size = 0
        for action in actions:
            if not isinstance(action, str):
                self.actions_size += len(action)
        self.wait_until_complete = wait_until_complete

        size_wait = self.actions_size
        if wait_until_complete:
            size_wait |= 0x80

        super().__init__(reward_entity_opcode(), SUB_ACT, slot, size_wait)

    def __str__(self):
        result = f"{type(self).__name__}, {self.actions_size} bytes"
        result += ", Wait" if self.wait_until_complete else ", No Wait"
        return result


def RewardEntityAct(slot, wait_until_complete, *actions):
    import instruction.field.entity as field_entity
    RewardEntityAct = type("RewardEntityAct", (_RewardEntityAct,), {})
    return (RewardEntityAct(slot, wait_until_complete, *actions),
            list(actions), field_entity.End())


class RewardEntityActRaw(_RewardEntityInstruction):
    """Header for an action queue whose action bytes are spliced in raw
    (Read from a vanilla script), for relocating a vanilla scene queue
    whose opcode byte was the character id.  `size_wait` is the vanilla
    length byte: action byte count with the wait bit in bit 7.  The
    caller appends exactly that many action bytes (including vanilla's
    own $FF terminator)."""
    def __init__(self, slot, size_wait):
        super().__init__(SUB_ACT, slot, size_wait)


class LoadRewardKind(_RewardEntityInstruction):
    """Multipurpose event bit 0 = (reward in slot is the given kind)."""
    def __init__(self, slot, kind):
        from obfuscation.rewards import KINDS
        if isinstance(kind, str):
            kind = KINDS[kind]
        super().__init__(SUB_LOAD_KIND, slot, kind)


def BranchIfRewardKind(slot, kind, destination):
    import data.event_bit as event_bit
    from instruction.field.instructions import BranchIfEventBitSet
    return (LoadRewardKind(slot, kind),
            BranchIfEventBitSet(event_bit.multipurpose(0), destination))


def BranchIfRewardKindNot(slot, kind, destination):
    import data.event_bit as event_bit
    from instruction.field.instructions import BranchIfEventBitClear
    return (LoadRewardKind(slot, kind),
            BranchIfEventBitClear(event_bit.multipurpose(0), destination))


def UpdateRewardNpc(entity, slot):
    """The NPC updater: repaint a map NPC as the reward character at
    runtime (entrance events run before fade-in, so the player sees
    exactly what a non-race build bakes into the NPC record)."""
    return SetRewardSprite(entity, slot), SetRewardPalette(entity, slot)
