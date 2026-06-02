"""No-free-heals (-nfh) group modifications.

This module hosts the cross-event sweepers that run once when -nfh is on,
orchestrated by ``event/events.py`` ``Events.no_free_heals_mod()``:

- ``modify_inn_costs``      : multiplies every paid inn cost by
  ``INN_COST_MULTIPLIER`` and converts the free Returners Hideout and
  Figaro Castle inns into paid ones.
- ``modify_free_bed_heals`` : replaces the six vanilla free bed heals with
  a per-character state-dependent heal that has a 50%% chance of a pincer
  ambush.
- ``modify_recovery_springs``: randomises the effect of recovery springs
  (Phantom Forest pool, Cave to South Figaro) into one of nine outcomes.

Per-event heal removals/restrictions gated by ``args.no_free_heals`` live
in their respective event files (e.g. ``event/baren_falls.py``,
``event/collapsing_house.py``, ``event/doma_wob.py``,
``event/doma_wor.py``, ``event/magitek_factory.py``,
``event/narshe_wob.py``, ``event/burning_house.py``,
``event/phantom_train.py``). The ``BedHealCharacter`` field opcode used by
``modify_free_bed_heals`` is defined in ``instruction/field/custom.py``.
"""

import random

from memory.space import Bank, Reserve, Write
from instruction.event import EVENT_CODE_START
import instruction.field as field
import instruction.field.entity as field_entity
import data.event_bit as event_bit
import data.battle_bit as battle_bit


# Inn cost multiplier applied to every paid inn price and to the converted
# free inns at Returners Hideout and Figaro Castle.
INN_COST_MULTIPLIER = 3


def modify_inn_costs(maps, rom, dialogs, args):
    """
    Modifies all inn costs in the game by multiplying them by INN_COST_MULTIPLIER.
    Also updates the associated dialog text to reflect the new prices.
    Additionally converts free inns (Returners Hideout, Figaro Castle) to paid inns.

    Each inn event has a "Take GP" instruction (opcode 0x85) followed by a 2-byte
    little-endian amount. This function finds all these locations and multiplies
    the GP amount by the multiplier constant.

    Args:
        maps: The Maps object to modify NPCs and event tiles
        rom: The ROM object to modify
        dialogs: The Dialogs object to update dialog text
        args: Command line arguments
    """
    # List of all inn GP cost addresses in the ROM
    # Format: (address, original_cost, dialog_id, dialog_template, description)
    # dialog_id is None for entries that share a dialog with another entry
    # dialog_template uses {price} as placeholder for the GP amount
    # Chocobo stables are handled separately by event/ruination.py
    # disable_chocobo_stables() (ruination-only); the Thamasa inn price bump is
    # handled locally in event/burning_house.py ruination_inn_mod() when -nfh
    # is set.
    inn_costs = [
        (0xa78a0, 80, 0x0B89, "{price} GP per night.<line>Stay the night?<line><choice> Yes<line><choice> No<end>", "South Figaro inn"),
        (0xa8ef1, 150, 0x0B8A, "{price} GP per night!<line>Sound good?<line><choice> Yes<line><choice> No<end>", "Nikeah inn WoB"),
        (0xb449c, 250, 0x0112, "{price} GP per night.<line>Lights out?<line><choice> Yes<line><choice> No<end>", "Jidoor inn"),
        (0xc5caf, 350, 0x062A, "{price} GP per night!<line>Rest a while?<line><choice> Yes<line><choice> No<end>", "Tzen inn"),
        (0xc62b2, 300, 0x0649, "{price} GP if you wanna stay.<line>How 'bout it?<line><choice> Yes<line><choice> No<end>", "Albrook inn WOR"),
        (0xc6593, 200, 0x060D, "{price} GP per night!<line>Need a rest?<line><choice> Sure<line><choice> Nope<end>", "Maranda inn"),
        (0xc665f, 100, 0x064B, "You look tired!<line>{price} GP for a snooze.<line><choice> Yes<line><choice> No<end>", "Mobliz inn"),
        (0xb7870, 400, 0x0973, "{price} GP per night.<line>Wanna rest?<line><choice> Yes<line><choice> No<end>", "Coliseum inn"),
        (0xc69d6, 200, None, None, "Kohlingen inn"),  # Shares dialog 0x060D with Maranda
        (0xcd2b3, 200, None, None, "Narshe inn"),  # Shares dialog 0x060D with Maranda
    ]

    # Track which dialogs we've already updated to avoid double-updating shared dialogs
    updated_dialogs = set()

    for address, original_cost, dialog_id, dialog_template, description in inn_costs:
        # Calculate new cost
        new_cost = min(original_cost * INN_COST_MULTIPLIER, field.RemoveGP.MAX)

        # Write the new cost as 2-byte little-endian
        rom.set_bytes(address, new_cost.to_bytes(2, 'little'))

        # Update dialog text if this entry has its own dialog ID
        if dialog_id is not None and dialog_id not in updated_dialogs:
            new_text = dialog_template.format(price=new_cost)
            dialogs.set_text(dialog_id, new_text)
            updated_dialogs.add(dialog_id)

            if args.debug:
                print(f"Updated dialog {dialog_id:#x} for {description}: {original_cost} GP -> {new_cost} GP")

        if args.debug:
            print(f"Modified {description}: {original_cost} GP -> {new_cost} GP")

    # =========================================================================
    # FREE INNS - Convert to paid inns
    # =========================================================================
    # These locations originally provided free healing. We add GP charges
    # affected by INN_COST_MULTIPLIER.

    # Free inn base prices (before multiplier)
    RETURNERS_HIDEOUT_INN_PRICE = 100
    FIGARO_CASTLE_INN_PRICE = 150

    # -------------------------------------------------------------------------
    # RETURNERS HIDEOUT INN (Map 111, NPC ID 16)
    # -------------------------------------------------------------------------
    # Original event at 0xCAF64E displays "Take a nap? Yes/No"
    # If yes: movement animation, call $CACD3C (sleep), load inn map, call $CACF96 (wake)
    # New: Display price, take GP, then jump to original movement code at 0xCAF659
    RETURNERS_DIALOG_ID = 0x111
    RETURNERS_ORIGINAL_YES_CODE = 0xCAF659

    returners_price = min(RETURNERS_HIDEOUT_INN_PRICE * INN_COST_MULTIPLIER, field.RemoveGP.MAX)

    dialogs.set_text(RETURNERS_DIALOG_ID,
        f"{returners_price} GP per night!<line>Take a nap?<line><choice> Yes<line><choice> No<end>")

    returners_src = [
        field.DialogBranch(RETURNERS_DIALOG_ID, "RETURNERS_YES", "RETURNERS_NO"),
        field.Return(),

        "RETURNERS_YES",
        field.RemoveGP(returners_price),
        field.BranchIfEventBitSet(event_bit.NOT_ENOUGH_GP, "RETURNERS_NO_MONEY"),
        field.Branch(RETURNERS_ORIGINAL_YES_CODE),

        "RETURNERS_NO_MONEY",
        field.ClearEventBit(event_bit.NOT_ENOUGH_GP),
        "RETURNERS_NO",
        field.Return(),
    ]

    space = Write(Bank.CC, returners_src, "Returners Hideout inn with price")
    returners_npc = maps.get_npc(111, 0x10)
    returners_npc.event_address = space.start_address - EVENT_CODE_START

    if args.debug:
        print(f"Returners Hideout inn: {RETURNERS_HIDEOUT_INN_PRICE} GP -> {returners_price} GP")

    # -------------------------------------------------------------------------
    # FIGARO CASTLE REST (Map 59, event tile at (47, 52))
    # -------------------------------------------------------------------------
    # Original event at 0xCA71BF checks conditions then displays "Need a rest? Yes/No"
    # If yes: movement, check more conditions, call $CACD31 (sleep)
    # New: Same condition checks, display price, take GP, jump to original code
    # Note: We use dialog ID 1461 (0x5B5) instead of the original 0xB80 because
    # 0xB80 is also used by a Doma Castle event.
    FIGARO_DIALOG_ID = 1461
    FIGARO_ORIGINAL_YES_CODE = 0xCA71D9
    FIGARO_USED_ONCE_BIT = 0x1B5
    FIGARO_BANON_BIT = 0x1B0

    figaro_price = min(FIGARO_CASTLE_INN_PRICE * INN_COST_MULTIPLIER, field.RemoveGP.MAX)

    dialogs.set_text(FIGARO_DIALOG_ID,
        f"{figaro_price} GP per night!<line>Need a rest?<line><choice>(Yes)<line><choice>(No)<end>")

    animation_src = [field.Read(0xa71d9, 0xa71dd), field.Branch(0xa71d4)]
    space = Reserve(0xa71d9, 0xa71e8, "Figaro Castle Inn simplify", field.NOP())
    space.write(animation_src)
    animation_addr = space.start_address

    figaro_src = [
        field.BranchIfEventBitSet(event_bit.multipurpose_map(1), "FIGARO_RETURN"),
        field.SetEventBit(event_bit.multipurpose_map(1)),
        field.DialogBranch(FIGARO_DIALOG_ID, "FIGARO_YES", "FIGARO_RETURN"),
        "FIGARO_YES",
        field.RemoveGP(figaro_price),
        field.BranchIfEventBitSet(event_bit.NOT_ENOUGH_GP, "FIGARO_NO_MONEY"),
        field.Branch(animation_addr),

        "FIGARO_NO_MONEY",
        field.ClearEventBit(event_bit.NOT_ENOUGH_GP),
        "FIGARO_RETURN",
        field.Return(),
    ]

    space = Write(Bank.CC, figaro_src, "Figaro Castle rest with price")
    figaro_event = maps.get_event(59, 47, 52)
    if figaro_event is not None:
        figaro_event.event_address = space.start_address - EVENT_CODE_START
        if args.debug:
            print(f"Figaro Castle rest: {FIGARO_CASTLE_INN_PRICE} GP -> {figaro_price} GP")
    elif args.debug:
        print(f"Warning: Could not find Figaro Castle rest event at (47, 52)")


# Battle pack for nighttime ambush at free beds.
# Must be a PACK2 (event battle group, IDs 256-511); InvokeBattleType can only
# address PACK2 slots. Pack 416 is unused elsewhere, so we can overwrite its
# two formation slots without affecting other encounters.
FREE_BED_AMBUSH_PACK = 416
FREE_BED_DIALOG_ID = 443  # "Take a nap?" at Gau's Dad's House

# Vanilla free bed heal subroutine address (used by multiple bed event tiles)
VANILLA_BED_HEAL_ADDRESS = 0xcd17

# Address of the -nfh bed heal routine (set by modify_free_bed_heals)
RUINATION_BED_HEAL_ADDRESS = None

# Existing free bed heal event tile locations
# Most point to the vanilla subroutine at 0xcd17
# Gau's Father's House has its own inline code but we treat it the same way
# Format: (map_id, x, y, description)
FREE_BED_LOCATIONS = [
    (24, 45, 51, "Narshe Weapon Shop"),
    (94, 73, 31, "Sabin's House"),
    (94, 81, 29, "Sabin's House"),
    (94, 84, 29, "Sabin's House"),
    (116, 113, 9, "Gau's Father's House"),
    (162, 29, 12, "Mobliz Relic Shop"),
]


def modify_free_bed_heals(maps, dialogs, enemies, args):
    """
    Modifies existing free bed heal events as part of -nfh (no free heals).

    Changes the bed heals to:
    - Have a 50% chance of triggering a pincer attack (escape only allowed
      once half the enemies are defeated, or via Warp Stone / Smoke Bomb).
    - If the party flees the ambush, no heal is applied.
    - Otherwise apply a per-character state-dependent heal (see BedHealCharacter):
      dead -> revive to 1 HP (no-op under -permadeath), statused -> cure,
      hurt -> +half max HP, otherwise -> +half max MP.
    - Use the standard bed animation (fade, Nighty Night song, unfade)

    Args:
        maps: The Maps object to modify event tiles
        dialogs: The Dialogs object to modify dialog for these events
        enemies: The Enemies object (to adjust the ambush pack's enemies/formations)
        args: Command line arguments (for debug flag)
    """

    # NIGHTY_NIGHT song ID
    NIGHTY_NIGHT = 56 | 0x80  # High bit set for temporary song

    free_bed_dialog = "Sleep for the night?<line><choice> (Yes)<line><choice> (No)<end>"
    dialogs.set_text(FREE_BED_DIALOG_ID, free_bed_dialog)

    # Pick two different random formations that allow pincer attacks and
    # install them in the ambush pack's two slots.
    pincer_formations = [
        f_id for f_id in enemies.formations.normal
        if enemies.formations.formations[f_id].disable_pincer_attack == 0
    ]
    formation_a, formation_b = random.sample(pincer_formations, 2)
    ambush_pack = enemies.packs.packs[FREE_BED_AMBUSH_PACK]
    ambush_pack.formations[0] = formation_a
    ambush_pack.formations[1] = formation_b

    if args.debug:
        print(f"Bed ambush pack: {FREE_BED_AMBUSH_PACK}")
        print(f"  formation A: {formation_a} ({enemies.formations.get_name(formation_a)})")
        print(f"  formation B: {formation_b} ({enemies.formations.get_name(formation_b)})")

    # Create the new bed heal event code (50% chance of pincer ambush)
    src = [
        # Include a trigger so this can only be done once per map load
        field.ReturnIfEventBitSet(event_bit.multipurpose_map(0)),
        field.SetEventBit(event_bit.multipurpose_map(0)),

        # Ask if player wants to sleep for the night
        field.DialogBranch(FREE_BED_DIALOG_ID, dest1="CONTINUE", dest2="RETURN"),
        "CONTINUE",

        # Fade out current song
        field.FadeOutSong(48),
        field.PauseUnits(60),
        field.FadeOutScreen(8),
        field.WaitForFade(),

        # 50% chance of monster attack (branch to HEAL with 50% probability)
        field.BranchChance(0.5, "HEAL"),

        # Pincer attack -- escape allowed (after half the enemies are defeated,
        # or via Warp Stone / Smoke Bomb).
        field.InvokeBattleType(FREE_BED_AMBUSH_PACK, field.BattleType.PINCER),

        # If the party fought, heal; if they fled, skip straight to cleanup.
        # Battle bit RAN_AWAY is set by battle code only when the party ran.
        field.BranchIfBattleEventBitClear(battle_bit.RAN_AWAY, "HEAL"),
        field.Branch("AFTER_HEAL"),

        "HEAL",
        # Play Nighty Night song
        field.StartSong(NIGHTY_NIGHT),

        # Per-character state-dependent heal for each party slot.
        field.BedHealCharacter(field_entity.PARTY0),
        field.BedHealCharacter(field_entity.PARTY1),
        field.BedHealCharacter(field_entity.PARTY2),
        field.BedHealCharacter(field_entity.PARTY3),

        # Stop temporary song and restore the pre-battle song. Only valid on
        # this path because StartSong above sets up the "current"/"previous"
        # slots correctly; on the fled path the battle leaves the slots in an
        # inconsistent state and 0xF3 resurrects the battle music.
        field.WaitForSong(),
        field.FadeInPreviousSong(32),

        "AFTER_HEAL",
        field.FadeInScreen(8),

        "RETURN",
        field.Return(),
    ]

    space = Write(Bank.CC, src, "ruination free bed heal event")
    new_bed_heal_address = space.start_address
    #print(f"New ruination bed code at {hex(space.start_address)}--{hex(space.end_address)}")

    # Export the address for use by other modules (e.g., doma_wor.py)
    global RUINATION_BED_HEAL_ADDRESS
    RUINATION_BED_HEAL_ADDRESS = new_bed_heal_address

    if args.debug:
        print(f"Created modified bed heal event at {new_bed_heal_address:#x}")

    # Update existing bed event tiles to point to the new subroutine
    for map_id, x, y, description in FREE_BED_LOCATIONS:
        event = maps.get_event(map_id, x, y)
        if event is not None:
            event.event_address = new_bed_heal_address - EVENT_CODE_START
            if args.debug:
                print(f"Updated bed heal at {description} (map {map_id}, {x}, {y})")
        else:
            if args.debug:
                print(f"Warning: No event found at {description} (map {map_id}, {x}, {y})")


# Recovery Spring Effect Types
class SpringEffect:
    FULL_RECOVERY = 0    # HP + MP + Status
    RECOVER_HP = 1       # HP only
    RECOVER_MP = 2       # MP only
    RECOVER_STATUS = 3   # Status only
    POISON = 4           # Add poison to random party members
    IMP = 5              # Add imp to random party members
    ZOMBIE = 6           # Add zombie to random party members
    STONE = 7            # Add petrify to random party members
    REDUCE_TO_1_HP = 8   # Reduce all party members to 1 HP

# Recovery spring locations grouped by area
# Each area will have the same effect for all its tiles
SPRING_LOCATIONS = {
    'phantom_forest': [
        (133, 9, 10),   # Phantom Forest Healing Pool
        (133, 8, 10),
        (133, 7, 10),
        (133, 6, 10),
        (133, 5, 9),
    ],
    'cave_south_figaro': [
        (70, 47, 29),   # Cave to South Figaro (WoB)
        (73, 47, 29),   # Cave to South Figaro (WoB variant)
    ],
}

# Flash colors for each effect type
SPRING_FLASH_COLORS = {
    SpringEffect.FULL_RECOVERY: field.Flash.BLUE,
    SpringEffect.RECOVER_HP: field.Flash.BLUE,
    SpringEffect.RECOVER_MP: field.Flash.BLUE,
    SpringEffect.RECOVER_STATUS: field.Flash.BLUE,
    SpringEffect.POISON: field.Flash.GREEN,
    SpringEffect.IMP: field.Flash.GREEN,
    SpringEffect.ZOMBIE: field.Flash.RED | field.Flash.BLUE,  # Purple
    SpringEffect.STONE: field.Flash.WHITE,  # Grey-ish
    SpringEffect.REDUCE_TO_1_HP: field.Flash.RED,
}

# Dialog IDs for spring messages (range 1480-1495 reserved). Sits in the vanilla
# Maduin/Madonna esper-world conversation block — see ARCHIVE.md
# "Ruination Mode — Dialog ID Reservations" before claiming new IDs nearby.
SPRING_DIALOG_BASE = 1480


def modify_recovery_springs(maps, rom, dialogs, args):
    """
    Modifies recovery spring events for ruination mode.

    Each spring location gets a randomly assigned effect at compile time.
    Effects can be beneficial (healing) or harmful (status ailments).
    Player is asked before drinking from the pool.

    Args:
        maps: The Maps object to modify event tiles
        rom: The ROM object
        dialogs: The Dialogs object for setting dialog text
        args: Command line arguments (for debug flag)
    """
    # Status effects for healing
    HEAL_STATUS = (field.Status.DEATH | field.Status.PETRIFY | field.Status.IMP |
                   field.Status.VANISH | field.Status.POISON | field.Status.ZOMBIE |
                   field.Status.DARKNESS)

    PARTY = [field_entity.PARTY0, field_entity.PARTY1, field_entity.PARTY2, field_entity.PARTY3]

    # All possible effects
    ALL_EFFECTS = [
        SpringEffect.FULL_RECOVERY,
        SpringEffect.RECOVER_HP,
        SpringEffect.RECOVER_MP,
        SpringEffect.RECOVER_STATUS,
        SpringEffect.POISON,
        SpringEffect.IMP,
        SpringEffect.ZOMBIE,
        SpringEffect.STONE,
        SpringEffect.REDUCE_TO_1_HP,
    ]

    # Result messages for each effect
    EFFECT_MESSAGES = {
        SpringEffect.FULL_RECOVERY: "HP, MP, and status restored!<end>",
        SpringEffect.RECOVER_HP: "HP restored!<end>",
        SpringEffect.RECOVER_MP: "MP restored!<end>",
        SpringEffect.RECOVER_STATUS: "Status ailments cured!<end>",
        SpringEffect.POISON: "The water was poisoned!<end>",
        SpringEffect.IMP: "The water turned you into Imps!<end>",
        SpringEffect.ZOMBIE: "The water was cursed!<end>",
        SpringEffect.STONE: "The water is petrifying!<end>",
        SpringEffect.REDUCE_TO_1_HP: "The water drained your strength!<end>",
    }

    dialog_id = SPRING_DIALOG_BASE

    # Set up the "Drink from the pool?" dialog
    drink_dialog_id = dialog_id
    dialogs.set_text(drink_dialog_id, "Drink from the pool?<line><choice> Yes<line><choice> No<end>")
    dialog_id += 1

    # Process each spring location area
    for area_name, locations in SPRING_LOCATIONS.items():
        # Randomly choose an effect for this area
        effect = random.choice(ALL_EFFECTS)

        # Set up result message dialog
        result_dialog_id = dialog_id
        dialogs.set_text(result_dialog_id, EFFECT_MESSAGES[effect])
        dialog_id += 1

        # Get flash color for this effect
        flash_color = SPRING_FLASH_COLORS[effect]

        # Build the effect instructions
        effect_instructions = []

        if effect == SpringEffect.FULL_RECOVERY:
            for p in PARTY:
                effect_instructions.append(field.RemoveStatusEffects(p, HEAL_STATUS))
            for p in PARTY:
                effect_instructions.append(field.RestoreHp(p, 0x7f))
            for p in PARTY:
                effect_instructions.append(field.RestoreMp(p, 0x7f))

        elif effect == SpringEffect.RECOVER_HP:
            for p in PARTY:
                effect_instructions.append(field.RestoreHp(p, 0x7f))

        elif effect == SpringEffect.RECOVER_MP:
            for p in PARTY:
                effect_instructions.append(field.RestoreMp(p, 0x7f))

        elif effect == SpringEffect.RECOVER_STATUS:
            for p in PARTY:
                effect_instructions.append(field.RemoveStatusEffects(p, HEAL_STATUS))

        elif effect in [SpringEffect.POISON, SpringEffect.IMP, SpringEffect.ZOMBIE, SpringEffect.STONE]:
            # Determine which status to apply
            status_map = {
                SpringEffect.POISON: field.Status.POISON,
                SpringEffect.IMP: field.Status.IMP,
                SpringEffect.ZOMBIE: field.Status.ZOMBIE,
                SpringEffect.STONE: field.Status.PETRIFY,
            }
            status = status_map[effect]

            # Always affect party leader
            effect_instructions.append(field.AddStatusEffects(field_entity.PARTY0, status))
            # 50% chance to affect each other party member (at runtime)
            effect_instructions.extend([
                field.BranchRandomly("SKIP_P1"),
                field.AddStatusEffects(field_entity.PARTY1, status),
                "SKIP_P1",
                field.BranchRandomly("SKIP_P2"),
                field.AddStatusEffects(field_entity.PARTY2, status),
                "SKIP_P2",
                field.BranchRandomly("SKIP_P3"),
                field.AddStatusEffects(field_entity.PARTY3, status),
                "SKIP_P3",
            ])

        elif effect == SpringEffect.REDUCE_TO_1_HP:
            # Subtract 2^14 HP (16384), which reduces to 1 HP minimum
            for p in PARTY:
                effect_instructions.append(field.RestoreHp(p, 0x80 | 0x0e))

        # Build the full event code
        src = [
            # Require pressing the "A" button to activate
            field.BranchIfEventBitClear(event_bit=event_bit.PRESSING_A, destination="RETURN"),

            # Ask player if they want to drink
            field.DialogBranch(drink_dialog_id, "DRINK", "RETURN"),

            "DRINK",
            # Flash screen with appropriate color
            field.FlashScreen(flash_color),
            field.PlaySoundEffect(233),  # Spring sound
            field.PauseUnits(30),

            # Apply the effect
            *effect_instructions,

            # Show result message
            field.Dialog(result_dialog_id),

            # Enable movement and return
            field.FreeMovement(),
            field.Return(),

            "RETURN",
            field.Return(),
        ]

        space = Write(Bank.CC, src, f"ruination spring event {area_name}")
        spring_event_address = space.start_address

        if args.debug:
            effect_name = [k for k, v in vars(SpringEffect).items() if v == effect and not k.startswith('_')][0]
            print(f"Spring {area_name}: effect={effect_name}, address={spring_event_address:#x}")

        # Update all event tiles for this area to use the new event
        for map_id, x, y in locations:
            event = maps.get_event(map_id, x, y)
            if event is not None:
                event.event_address = spring_event_address - EVENT_CODE_START
                if args.debug:
                    print(f"  Updated spring tile at map {map_id} ({x}, {y})")
            else:
                if args.debug:
                    print(f"  Warning: No event at map {map_id} ({x}, {y})")
