"""ROM-dependent event-exit patch machinery: the realization-time edit
tables (exit_event_patch, entrance_door_patch, require_event_bit, ...)
and the patch-source functions they reference. The pure connection
tables (event_exit_info, event_return_map) live in
data/event_exit_data.py, importable without a ROM."""
from data.event_exit_data import event_exit_info, event_return_map

from instruction.event import EVENT_CODE_START
from instruction import field
import instruction.field.entity as field_entity
import data.event_bit as event_bit

### locomotive switches now handled in phantom_train.py:
### event_bit.SET_PHANTOM_TRAIN_SWITCHES is set or cleared when the switch event is called.
# def set_locomotive_switches(bytes=True):
#     # Set single event bit 0x03E to check when initiating smokestack event
#     # CB/B9DC: C2    If ($1E80($185) [$1EB0, bit 5] is set) or ($1E80($186) [$1EB0, bit 6] is clear) or ($1E80($184) [$1EB0, bit 4] is clear), branch to $CBB9D0
#     # CB/B9D0: <smokestack doesn't work>
#     from memory.space import Write, Bank
#     pt_switches_bit = [
#         field.BranchIfAny([0x184, False, 0x185, True, 0x186, False], "CLEAR_SWITCHES"),
#         field.SetEventBit(event_bit.SET_PHANTOM_TRAIN_SWITCHES),
#         field.Return(),
#         "CLEAR_SWITCHES",
#         field.ClearEventBit(event_bit.SET_PHANTOM_TRAIN_SWITCHES),
#         field.Return()
#     ]
#     space = Write(Bank.CB, pt_switches_bit, "Set or Clear PT switches bit")
#
#     set_switches = [field.Call(space.start_address)]
#
#     if bytes:
#         set_switches_bytes = []
#         for f in set_switches:
#             set_switches_bytes += [f.opcode] + f.args
#         return set_switches_bytes
#     else:
#         return set_switches


def add_mtek_armor(bytes=False):
    src = [
        field.Call(field.ADD_PARTY_MAGITEK),
        field.SetVehicle(field_entity.PARTY0, field.Vehicle.MAGITEK_AND_RIDER)
    ]
    if bytes:
        src_bit = []
        for s in src:
            src_bit += [s.opcode] + s.args
        return src_bit
    else:
        return src

def remove_mtek_armor(bytes=False):
    src = [
        field.Call(field.REMOVE_PARTY_MAGITEK),
        field.SetVehicle(field_entity.PARTY0, field.Vehicle.NONE)
    ]
    if bytes:
        src_bit = []
        for s in src:
            src_bit += [s.opcode] + s.args
        return src_bit
    else:
        return src


def tentacles_bit_check(bytes=False):
    src = [
        field.SetEventBit(event_bit.PRISON_DOOR_OPEN_FIGARO_CASTLE),
        field.ClearEventBit(npc_bit.LONE_WOLF_FIGARO_CASTLE),
        field.ClearEventBit(npc_bit.PRISONERS_FIGARO_CASTLE),
        field.SetEventBit(event_bit.GOT_FALCON),  # Needed to go to AC afterward
        field.ReturnIfEventBitSet(event_bit.DEFEATED_TENTACLES_FIGARO),
        field.SetEventBit(npc_bit.BLOCK_INSIDE_DOORS_FIGARO_CASTLE),
        field.SetEventBit(npc_bit.DEAD_SOLDIERS_FIGARO_CASTLE),
        field.ClearEventBit(npc_bit.PRISON_GUARD_FIGARO_CASTLE),
        field.Return()
    ]
    if bytes:
        src_bit = []
        for s in src:
            src_bit += [s.opcode] + s.args
        return src_bit
    else:
        return src

def opera_disruption_bit_check(bytes=False, skip_to=None):
    # skip_to: label to branch to (instead of returning) when the disruption is already finished.
    # A label is required when this code runs BEFORE the map load: an early Return there would
    # short-circuit the load that follows (see the note in MtZozo.entrance_door_patch).
    if skip_to is None:
        guard = field.ReturnIfEventBitSet(event_bit.FINISHED_OPERA_DISRUPTION)
    else:
        guard = field.BranchIfEventBitSet(event_bit.FINISHED_OPERA_DISRUPTION, skip_to)
    src = [
        guard,
        field.ClearEventBit(event_bit.BEGAN_OPERA_DISRUPTION),
        field.SetEventBit(npc_bit.ULTROS_OPERA_CEILING),
        field.SetEventBit(npc_bit.RAT1_OPERA_CEILING),
        field.SetEventBit(npc_bit.RAT2_OPERA_CEILING),
        field.SetEventBit(npc_bit.RAT3_OPERA_CEILING),
        field.SetEventBit(npc_bit.RAT4_OPERA_CEILING),
        field.SetEventBit(npc_bit.RAT5_OPERA_CEILING),
        field.SetEventBit(npc_bit.CEILING_DOOR_OPERA_HOUSE),
        field.SetEventBit(npc_bit.DANCING_COUPLE1_OPERA),
        field.SetEventBit(npc_bit.DANCING_COUPLE2_OPERA),
        field.SetEventBit(npc_bit.FIGHTING_SOLDIERS_OPERA_CEILING)
    ]
    if bytes:
        src_bit = []
        for s in src:
            src_bit += [s.opcode] + s.args
        return src_bit
    else:
        return src

def opera_dragon_bit_check(bytes=False, skip_to=None):
    # skip_to: label to branch to (instead of returning) when the dragon is already defeated.
    # A label is required when this code runs BEFORE the map load: an early Return there would
    # short-circuit the load that follows (see the note in MtZozo.entrance_door_patch).
    # NOTE: this runs before map load, so clearing IMPRESARIO_OPERA_LOBBY is enough to keep the
    # lobby Impresario from being created (no after-load HideEntity fixup needed).
    if skip_to is None:
        guard = field.ReturnIfEventBitSet(event_bit.DEFEATED_OPERA_HOUSE_DRAGON)
    else:
        guard = field.BranchIfEventBitSet(event_bit.DEFEATED_OPERA_HOUSE_DRAGON, skip_to)
    src = [
        guard,
        field.ClearEventBit(npc_bit.IMPRESARIO_OPERA_LOBBY),
        field.SetEventBit(npc_bit.IMPRESARIO_OPERA_PANICKING),
        field.SetEventBit(npc_bit.DRAGON_OPERA_HOUSE),
    ]
    if bytes:
        src_bit = []
        for s in src:
            src_bit += [s.opcode] + s.args
        return src_bit
    else:
        return src


def opera_entrance_bit_check(args):
    # In ruination mode the Opera House uses the single WoB entrance (658, room 'MAPb-OPE')
    # for both phases: the disruption (WoB bits) and the dragon fight afterward (WoR bits).
    # require_event_bit applies room 'OPEb06's WoB baseline on entry (clearing DRAGON_OPERA_HOUSE
    # etc.), so once FINISHED_OPERA_DISRUPTION is set we must instead apply the WoR bit set
    # (room 'OPEr06' baseline + opera_dragon_bit_check, i.e. the door 4658 entrance logic).
    # NOTE: NPC bits only take effect when their map loads, and the lobby (0xED) contains NPCs
    # gated by MAN_AT_COUNTER_OPERA, IMPRESARIO_OPERA_LOBBY and the ceiling door (0x355).  This
    # patch is therefore registered to run BEFORE map load (entrance_door_patch[658][1] = True),
    # and all guards use label skips so the fragment always falls through to the load that follows.
    if not args.ruination_mode:
        return opera_disruption_bit_check(skip_to="OPERA_ENTRANCE_END") + ["OPERA_ENTRANCE_END"]

    # WoB bits, with the "already finished" guard branching to the WoR section
    src = opera_disruption_bit_check(skip_to="OPERA_ENTRANCE_WOR")
    src += [
        field.Branch("OPERA_ENTRANCE_END"),
        "OPERA_ENTRANCE_WOR",
    ]
    # WoR baseline (room 'OPEr06'), then the dragon bits
    for bit, is_set in room_require_event_bit['OPEr06'].items():
        src.append(field.SetEventBit(bit) if is_set else field.ClearEventBit(bit))
    src += opera_dragon_bit_check(skip_to="OPERA_ENTRANCE_END")
    src += ["OPERA_ENTRANCE_END"]
    return src


# from instruction.field.functions import ORIGINAL_CHECK_GAME_OVER
exit_event_patch = {
    # Jump into Umaro's Cave:  Reproduce AtmaTek's changes to the event in data/umaro_cave.add_gating_condition()
    ### Not used when using JMP method ###
    #2010: lambda src, src_end: tritoch_event_mod(src, src_end),

    # Trapdoors in Esper Mountain: remove the check to see if the boss has been defeated yet.
    # e.g. "CB/EE8F: C0    If ($1E80($097) [$1E92, bit 7] is clear), branch to $CA5EB3 (simply returns)
    # When using JMP method, this should be handled in events.esper_mountain.py
    #2014: lambda src, src_end: [src[6:], src_end],
    #2015: lambda src, src_end: [src[6:], src_end],
    #2016: lambda src, src_end: [src[6:], src_end],

    # Switching door events in Owzer's Mansion: turn off the door timer before transitioning
    # Call subroutine $CB/2CAA (resets all timers).
    # # May also be necessary to clear event bits $1FC, $1FD, $1FE: [0xd3, 0xfc, 0xd3, 0xfd, 0xd3, 0xfe], but
    # # supposedly these are cleared on map load.
    2017: lambda src, src_end: [[0xb2, 0xaa, 0x2c, 0x01] + src, src_end],
    2018: lambda src, src_end: [[0xb2, 0xaa, 0x2c, 0x01] + src, src_end],

    # Zone eater: fade back in music after exit animation
    2041: lambda src, src_end: [src[:-1] + [0xf3, 0x20] + src[-1:], src_end],

    # Phantom Train set correct "switches" bit if leaving locomotive
    # Now handled at switches in locomotive: no need to check on entrance/exit
    #1545: lambda src, src_end: [src[:-1] + set_locomotive_switches(bytes=True) + src[-1:], src_end],

    # Doma Cave one-way doors: remove MTek armor
    859: lambda src, src_end: [src, src_end[:5] + remove_mtek_armor(bytes=True) + src_end[5:]],
    862: lambda src, src_end: [src, src_end[:5] + remove_mtek_armor(bytes=True) + src_end[5:]],
}

from event.phantom_train import *
phantom_train_initiate = PhantomTrain.initiation_script

from event.sealed_gate import SET_PARTY_LAYER0, SET_PARTY_LAYER2

exit_door_patch = {
    # For use with maps.create_exit_event() and maps.shared_map_exit_event()

    # Owzer's Mansion doors
    586: [field.Call(0xb2caa)],  # [0xb2, 0xaa, 0x2c, 0x01],  # South door.
    587: [field.Call(0xb2caa)],  # [0xb2, 0xaa, 0x2c, 0x01],  # North door.

    # Cave to the sealed gate: force reset timers when leaving lava room
    1075: [field.Call(0xb2caa)],  # [0xb2, 0xaa, 0x2c, 0x01],  # North door.
    1077: [field.Call(0xb2caa)],  # [0xb2, 0xaa, 0x2c, 0x01],  # South door.

    # Phantom Train set correct "switches" bit if leaving locomotive
    # Now handled in the switch events.  No need to set on entranec/exits
    #1545: set_locomotive_switches(bytes=False),
    #5545: set_locomotive_switches(bytes=False),  Dream train?? is actually 2072!

    # Doma Cave doors: remove MTek armor
    858: remove_mtek_armor(),
    860: remove_mtek_armor(),
    861: remove_mtek_armor(),
    863: remove_mtek_armor(),
    864: remove_mtek_armor(),

    # Phantom Train: initiate PT event if Sabin is recruited
    465: phantom_train_initiate(),

    # Baren Falls: for some reason, it doesn't auto update the parent map
    15: [field.SetParentMap(0x0, direction.DOWN, 185, 93)],

    # Door from FC prison towards Ancient Castle: try setting warp stones to return here
    # No good: Return To Parent Map freezes character if not on world map? why?
    #1558: [field.SetParentMap(0x03d, direction.UP, 35, 39)],  # tile at [0x03d, 35, 35]
    1558: [field.SetEventBit(event_bit.ANCIENT_CASTLE_WARP_OPTION)],  # Set custom event bit to handle warping in this situation

    # Sealed Gate:  party needs to be on Layer 2 on this map.  Reset to Layer0 on exit.
    1079: [field.Call(SET_PARTY_LAYER0)],
}

entrance_event_patch = {
    # For use by transitions.mod()

    # Jump back to Narshe from Umaro's cave: force "clear $1EB9 bit 4" (song override) before transition
    # Now handled in map_events.mod() with common patches
    # 3009: lambda src, src_end: [src[:-1] + [0xd3, 0xcc] + src[-1:], src_end],

    # Jump from Narshe into Umaro's cave: Remove extra falling sound effect (src_end[5:6])
    # Can't do this with JMP method.
    #3010: lambda src, src_end: [src, src_end[:5] + src_end[7:]],

    # Jump into Esper Mountain room 2, North trapdoor: patch in "hold screen" (0x38) after map transition
    # The other trapdoors have this, maybe it's just a typo?
    2015: lambda src, src_end: [src, src_end[:5] + [0x38] + src_end[5:]],

    # Cid's Elevator Ride: remove move-party-down after elevator.
    # space = Reserve(0xc8014, 0xc801a, "magitek factory move party down after elevator", field.NOP())
    # NOTE: should now be handled in Events(), no need to repeat.
    # 3027: lambda src, src_end: [ src, src_end[:-8] + src_end[-1:]]

    # Minecart Ride: if Cranes are defeated, instead go to normal Vector
    2028: lambda src, src_end: minecart_event_mod(src, src_end),    # JMP code
    #3028: lambda src, src_end: minecart_event_mod(src, src_end),   # rewrite code

    # Lete River: Hide the Raft NPCs ($10, $11) when entering the cave rooms
    # see e.g. CB/052F -- CB/0533 (Delete object $10, Refresh Objects, Hide Object $10)
    2035: lambda src, src_end: [src, src_end[:5] + [0x3e, 0x10, 0x45, 0x42, 0x10] + src_end[5:]], # Cave 1 entry, object $10
    2037: lambda src, src_end: [src, src_end[:5] + [0x3e, 0x11, 0x45, 0x42, 0x11] + src_end[5:]], # Cave 2 entry, object $11

    # Daryl's Tomb: Move the turtles to the appropriate side.
    ### MOVED TO require_event_bit

    # Doma Cave one-way doors: add MTek armor.  Redundant if in map.
    6859: lambda src, src_end: [src, src_end[:5] + add_mtek_armor(bytes=True) + src_end[5:]],
    6862: lambda src, src_end: [src, src_end[:5] + add_mtek_armor(bytes=True) + src_end[5:]],
}

from event.doma_wob import *
doma_siege_patch = DomaWOB.entrance_door_patch

from event.mt_zozo import *
mt_zozo_cliff_check = MtZozo.entrance_door_patch

from event.phoenix_cave import *
phoenix_cave_animation = PhoenixCave.entrance_door_patch()

from event.floating_continent import *
floating_continent_logic = FloatingContinent.entrance_door_patch()
floating_continent_return = FloatingContinent.return_door_patch()

from event.ancient_castle import *
figaro_castle_underground_state = AncientCastle.entrance_door_patch()

entrance_door_patch = {
    # For use by maps.create_exit_event() and maps.shared_map_exit_event()
    # door_id: [Code that must be run upon entering a door, Before (True) or After (False) map load]
    # If you are just setting or clearing event bits, use require_event_bit instead.

    # Doma Cave doors: add MTek armor.  Redundant if in map.
    858: [add_mtek_armor(), False],
    860: [add_mtek_armor(), False],
    861: [add_mtek_armor(), False],
    863: [add_mtek_armor(), False],
    864: [add_mtek_armor(), False],

    # Doma siege entrance patch
    1240: [doma_siege_patch, True],
    744: [lambda args: doma_siege_patch(args, exit_event_x=28, exit_event_y=33), True],  # Doma siege via inside door (ruination)

    # Figaro Castle WoR tentacles bit check patch (on entering SF Cave for map shuffle)
    262: [tentacles_bit_check(), False],

    # Opera House WoB completed opera bit check patch
    # (callable: in ruination mode the single entrance also handles the post-disruption WoR/dragon state)
    # Run BEFORE map load: the lobby (0xED) has NPCs gated by these bits (see opera_entrance_bit_check)
    658: [opera_entrance_bit_check, True],

    # Opera House WoR defeated dragon bit check patch
    # Run BEFORE map load: IMPRESARIO_OPERA_LOBBY gates an NPC on the lobby map (0xED) itself
    4658: [opera_dragon_bit_check(skip_to="OPERA_DRAGON_END") + ["OPERA_DRAGON_END"], True],

    # Mt Zozo cliff entrance patch
    1204: [mt_zozo_cliff_check, True],

    # Phoenix cave animation & party split
    1555: [phoenix_cave_animation, True],

    # Floating continent choice, animation, boss call
    1557: [floating_continent_logic, True],

    # Return to Blackjack after FC connection, animation
    1556: [floating_continent_return, True],

    # Return to Figaro Castle after AC connection, clear custom warp bit
    #1558: [[field.ClearEventBit(event_bit.ANCIENT_CASTLE_WARP_OPTION)], False],  # Clear custom event bit to handle warping in this situation
    1558: [figaro_castle_underground_state, True],  # force status depending on DEFEATED_TENTACLES

    # Sealed Gate:  Party must be Layer2 on this map
    1079: [[field.Call(SET_PARTY_LAYER2)], False],
}
#for j in entrance_door_patch.keys():
#    print(j, entrance_door_patch[j])

# Automatically set required event bits BEFORE loading the map
require_event_bit = {
    # Lete River: hide raft NPC before entering caves
    2035: {0x4FC: False},   # Cave #1
    2037: {0x4FD: False},   # Cave #2

    # Daryl's Tomb: move turtles to the appropriate side
    1512: {event_bit.DARYL_TOMB_TURTLE1_MOVED: True},
    782: {event_bit.DARYL_TOMB_TURTLE1_MOVED: False},
    793: {event_bit.DARYL_TOMB_TURTLE2_MOVED: False},
    794: {event_bit.DARYL_TOMB_TURTLE2_MOVED: False},
    795: {event_bit.DARYL_TOMB_TURTLE2_MOVED: True, event_bit.DARYL_TOMB_DOOR_SWITCH: True},

    # Phantom Train, Outside rear section: turn off ghosts
    474: {0x509: False},
    475: {0x509: False},
    476: {0x509: False},
    1518: {0x509: False},
    1519: {0x509: False},
    1520: {0x509: False},
    1521: {0x509: False},
    1522: {0x509: False},

    # Phantom Train, Car 1
    1515: {0x17e: False, event_bit.PHANTOM_TRAIN_CAR_3: False, 0x506: True, 0x507: False, 0x509: False},
    1516: {0x17e: False, event_bit.PHANTOM_TRAIN_CAR_3: False, 0x506: True, 0x507: False, 0x509: False},
    # Phantom Train, Car 2
    1523: {0x17e: True, event_bit.PHANTOM_TRAIN_CAR_3: False, 0x506: False, 0x507: True, 0x509: False},
    1524: {0x17e: True, event_bit.PHANTOM_TRAIN_CAR_3: False, 0x506: False, 0x507: True, 0x509: False},
    # Phantom Train, Car 3
    1514: {0x17e: False, event_bit.PHANTOM_TRAIN_CAR_3: True, 0x506: False, 0x507: False, 0x509: True},

    # Phantom Train, Car 6
    1533: {0x17e: False, 0x506: True, 0x507: False},  # Phantom Train Car 6 Right Exit
    1534: {0x17e: False, 0x506: True, 0x507: False},  # Phantom Train Car 6 Left Exit
    1535: {0x17e: False, 0x506: True, 0x507: False},  # Phantom Train Car 6 Right Cabin
    1536: {0x17e: False, 0x506: True, 0x507: False},  # Phantom Train Car 6 Left Cabin
    1538: {0x17e: False},  # Phantom Train Car 6 Left Cabin interior

    # Phantom Train, Car 7
    1539: {0x17e: True, 0x506: False, 0x507: True},  # Phantom Train Car 7 Right Exit
    1540: {0x17e: True, 0x506: False, 0x507: True},  # Phantom Train Car 7 Left Exit
    1541: {0x17e: True, 0x506: False, 0x507: True},  # Phantom Train Car 7 Right Cabin
    1542: {0x17e: True, 0x506: False, 0x507: True},  # Phantom Train Car 7 Left Cabin
    1543: {0x17e: True},  # Phantom Train Car 7 Right Cabin interior # 0x17E ON, NOT CLEARED!

    # Cyan Dream, Train (NPCs for jumping animation).  Not needed.
    #478: {0x543: True},
    #479: {0x543: True},
    #480: {0x543: True},
    #481: {0x543: True},

    # Cyan Dream, Caves exit (NPCs for bridge animation)
    860: {0x545: True},
    861: {0x545: True},

    # Cyan Dream, savepoint room (from door, show savepoint; from drop don't)
    2073: {0x548: False},
    443: {0x548: True},

    # Cyan Dream, Wrexsoul room (NPCs)
    456: {0x548: True},

    # Cave on the Veldt, Relm/shadow NPC
    988: {0x552: True},
    991: {0x552: True},

    # Owzer's Basement Chadarnook Room, Owzer & Relm NPCs
    591: {0x488: True, 0x487: True},

    # Phoenix Cave return to Falcon, unset warp bit
    1554: {event_bit.PHOENIX_CAVE_WARP_OPTION: False},

    # Exit from Cave on the Veldt, require Veldt music
    61: {event_bit.VELDT_WORLD_MUSIC: True},

}

room_require_event_bit = {
    # Narshe WoB NPC bits
    'NARb01': {npc_bit.STORES_NARSHE: True, npc_bit.WEAPON_ELDER_NARSHE: False, npc_bit.WEAPON_ROOM_ESPER_NARSHE: False},
    'NARb04': {npc_bit.STORES_NARSHE: True, npc_bit.WEAPON_ELDER_NARSHE: False, npc_bit.WEAPON_ROOM_ESPER_NARSHE: False}, # north entrance from caves

    # Narshe WoR NPC bits
    'NARr01': {npc_bit.STORES_NARSHE: False, npc_bit.WEAPON_ELDER_NARSHE: True, npc_bit.WEAPON_ROOM_ESPER_NARSHE: True},
    'NARr04': {npc_bit.STORES_NARSHE: False, npc_bit.WEAPON_ELDER_NARSHE: True, npc_bit.WEAPON_ROOM_ESPER_NARSHE: True}, # north entrance from caves
    'NARr01-ruin': {npc_bit.STORES_NARSHE: False, npc_bit.WEAPON_ELDER_NARSHE: True, npc_bit.WEAPON_ROOM_ESPER_NARSHE: True}, # ruination mode

    # Mobliz WoB NPC bits
    'MOBb01': {npc_bit.MOBLIZ_CITIZENS: True, npc_bit.MOBLIZ_SOLDIERS_LETTER: True},

    # Mobliz WoR NPC bits
    'MOBr01': {npc_bit.MOBLIZ_CITIZENS: False, npc_bit.MOBLIZ_SOLDIERS_LETTER: False},

    # Figaro Castle WoB NPC & event bits:
    'FIGb01': {event_bit.PRISON_DOOR_OPEN_FIGARO_CASTLE: False,
         npc_bit.DEAD_SOLDIERS_FIGARO_CASTLE: False,
         npc_bit.BLOCK_INSIDE_DOORS_FIGARO_CASTLE: False,
         npc_bit.LONE_WOLF_FIGARO_CASTLE: True,
         npc_bit.PRISONERS_FIGARO_CASTLE: True,
         npc_bit.PRISON_GUARD_FIGARO_CASTLE: True,
         event_bit.GOT_FALCON: False},  # Required to not go to AC in WOB

    # Figaro Castle WoR NPC & event bits:
    'FIGr01': {event_bit.PRISON_DOOR_OPEN_FIGARO_CASTLE: True,
            npc_bit.LONE_WOLF_FIGARO_CASTLE: False,
            npc_bit.PRISONERS_FIGARO_CASTLE: False,
            event_bit.GOT_FALCON: True},  # Required to go to AC
            # Other bits must be set when entering south figaro cave, but only if not TENTACLE_DEFEATED:
            #if not TENTACLE_DEFEATED:
            #   field.SetEventBit(npc_bit.BLOCK_INSIDE_DOORS_FIGARO_CASTLE),
            #   field.SetEventBit(npc_bit.DEAD_SOLDIERS_FIGARO_CASTLE),
            #   field.ClearEventBit(npc_bit.PRISON_GUARD_FIGARO_CASTLE),

    # Opera House WoB NPC & event bits:
    'OPEb06': {npc_bit.MAN_AT_COUNTER_OPERA: False,
          npc_bit.IMPRESARIO_OPERA_PANICKING: False,
          npc_bit.IMPRESARIO_OPERA_LOBBY: False,
          npc_bit.IMPRESARIO_OPERA_SITTING: True,
          npc_bit.DRAGON_OPERA_HOUSE: False},
          # Other bits must be set/cleared depending on FINISHED_OPERA_DISRUPTION:
          #if not FINISHED_OPERA_DISRUPTION:
          #   field.ClearEventBit(event_bit.BEGAN_OPERA_DISRUPTION),
          #   field.SetEventBit(npc_bit.ULTROS_OPERA_CEILING),
          #   field.SetEventBit(npc_bit.RAT1_OPERA_CEILING),
          #   field.SetEventBit(npc_bit.RAT2_OPERA_CEILING),
          #   field.SetEventBit(npc_bit.RAT3_OPERA_CEILING),
          #   field.SetEventBit(npc_bit.RAT4_OPERA_CEILING),
          #   field.SetEventBit(npc_bit.RAT5_OPERA_CEILING),
          #   field.SetEventBit(npc_bit.CEILING_DOOR_OPERA_HOUSE),
          #   field.SetEventBit(npc_bit.DANCING_COUPLE1_OPERA),
          #   field.SetEventBit(npc_bit.DANCING_COUPLE2_OPERA),
          #   field.SetEventBit(npc_bit.FIGHTING_SOLDIERS_OPERA_CEILING),

    'OPEr06': {npc_bit.MAN_AT_COUNTER_OPERA: True,
             npc_bit.IMPRESARIO_OPERA_LOBBY: True,
             npc_bit.IMPRESARIO_OPERA_SITTING: False,
             event_bit.BEGAN_OPERA_DISRUPTION: True,
             npc_bit.ULTROS_OPERA_CEILING: False,
             npc_bit.RAT1_OPERA_CEILING: False,
             npc_bit.RAT2_OPERA_CEILING: False,
             npc_bit.RAT3_OPERA_CEILING: False,
             npc_bit.RAT4_OPERA_CEILING: False,
             npc_bit.RAT5_OPERA_CEILING: False,
             npc_bit.CEILING_DOOR_OPERA_HOUSE: False,
             npc_bit.DANCING_COUPLE1_OPERA: False,
             npc_bit.DANCING_COUPLE2_OPERA: False,
             npc_bit.FIGHTING_SOLDIERS_OPERA: False,
             npc_bit.FIGHTING_SOLDIERS_OPERA_CEILING: False},
             #if not DEFEATED_OPERA_HOUSE_DRAGON:
             #    field.ClearEventBit(npc_bit.IMPRESARIO_OPERA_LOBBY),
             #    field.SetEventBit(npc_bit.IMPRESARIO_OPERA_PANICKING),
             #    field.SetEventBit(npc_bit.DRAGON_OPERA_HOUSE),

    # Thamasa inn NPC bits for Interceptor, Strago
    #447: {npc_bit.ATTACK_GHOSTS_PHANTOM_TRAIN: False},  # Do we need to deconflict this?
    # No, just change entrance event to delete these NPCS.  We don't use them.

    # Albrook make sure General Leo is turned off so you don't trigger the cutscene on the boat
    # 1F2C:5, 1F20:7, 1F21:0, 1F20:6, 1F28:2, 1F22:3, 1F22:1, 1F24:2
    # n, y0x507, n, y0x506, n0x542 (global in albrook.py), n, n, n
    'ALBb01': {0x507: False, 0x506: False},  # World of Balance   # bits shared with phantom train.
    'ALBr01': {0x507: False, 0x506: False},  # World of Ruin

}


def entrance_door_patch_view(args):
    """Per-build entrance_door_patch: ruination suppresses the door-1558
    patch (the Ancient Castle stairs are wired by ruination's own
    entrance logic). The shared table is never mutated."""
    view = dict(entrance_door_patch)
    if args is not None and getattr(args, 'ruination_mode', None):
        view.pop(1558, None)
    return view


def require_event_bit_view(args):
    """Per-build require_event_bit: ruination suppresses the Figaro
    Castle entrance doors (rooms 'FIGb01'/'FIGr01' propagate bits to
    doors 197/1156 and 4197/5156 via room_require_event_bit; those are
    only needed for classic door randomization). The shared table is
    never mutated."""
    view = dict(require_event_bit)
    if args is not None and getattr(args, 'ruination_mode', None):
        for door in (197, 1156, 4197, 5156):
            view.pop(door, None)
    return view


# push room required event bits to door required event bits
from data.rooms import room_data
for rb in room_require_event_bit.keys():
    for db in room_data[rb][0]:
        # door entrances
        require_event_bit[db] = room_require_event_bit[rb]


def minecart_event_mod(src, src_end):
    # Special event for outro of minecart ride: return to Vector if cranes have been defeated.
    # C0    If ($1E80($06B) is set), branch to $(new event) that sends you to Vector map instead
    # C0    If ($1E80($069) is set), branch to $(new event) that sends you to MTek3 Vector map without animation
    from memory.space import Write, Bank
    from event.event import direction
    # These two branches are alternate, fixed destinations (Vector, outdoors) taken
    # AFTER the minecart event has progressed (DEFEATED_CRANES / RODE_MINE_CART set).
    # They build their own LoadMap + Return tail, so they BYPASS the common state
    # patches that Transitions.mod() splices around the default, randomized
    # destination (the branches are inserted into src before ex_patch, so ex_patch
    # lands between the branches and the map load -- the skip paths jump over it).
    # Every exit-side state the common patches compensate must therefore be handled
    # unconditionally here:
    #   - raft: if the randomized destination is an on-raft location (e.g. the Lete
    #     River / Returner's Hideout raft), the party can still be carrying the raft
    #     graphic when they re-ride the cart and get routed here.  Vector is never an
    #     on-raft map, so clear the raft graphic (CB/04AA).  CB/04AA only sets the
    #     party's vehicle to "none" and leaves visibility untouched, so it is safe to
    #     call even when the party is not on a raft.
    #   - visibility: ShowEntity, in case the exit event hid the party (0x42).
    #   - screen hold: the exit event may have held the screen (0x38) -- e.g. the
    #     Esper Mtn trapdoors -- expecting the landing code to free it.  The hold
    #     persists across map loads, so free it (0x39) before loading Vector.
    #   - world bit: Vector is a WoB location; a WoR-side exit would normally get
    #     the world bit compensated in ex_patch, so force WoB here.
    go_to_vector = (
        #field.ClearEventBit(event_bit.TEMP_SONG_OVERRIDE),
        field.FreeScreen(),  # Release any screen hold from the exit event (see note above)
        field.ClearEventBit(event_bit.IN_WOR),  # Vector is WoB (see note above)
        field.LoadMap(0xf2, direction.LEFT, default_music=True, x=62, y=13, entrance_event=True),
        field.Call(0xb04aa),  # Remove raft (see note above)
        field.ShowEntity(field_entity.PARTY0),
        field.RefreshEntities(),
        field.FadeInScreen(),
        field.Return()
    )
    go_to_mtek3_vector = (
        #field.ClearEventBit(event_bit.TEMP_SONG_OVERRIDE),
        field.FreeScreen(),  # Release any screen hold from the exit event (see note above)
        field.ClearEventBit(event_bit.IN_WOR),  # Vector is WoB (see note above)
        field.LoadMap(0xf0, direction.LEFT, default_music=True, x=62, y=13, entrance_event=True),
        field.Call(0xb04aa),  # Remove raft (see note above)
        field.ShowEntity(field_entity.PARTY0),
        field.RefreshEntities(),
        field.FadeInScreen(),
        field.Return()
    )
    space = Write(Bank.CC, go_to_vector, "Return to Vector")
    patch1 = branch_code(space.start_address, 0)
    space = Write(Bank.CC, go_to_mtek3_vector, "Return to MTek3 Vector")
    patch2 = branch_code(space.start_address, 0)
    src = src[:-1] + [0xc0, 0x6b, 0x80] + patch1 + [0xc0, 0x69, 0x80] + patch2 + src[-1:]
    return src, src_end


# def tritoch_event_mod(src, src_end):
#     new_src = [0xc0, 0x9e, 0x2, 0xb3, 0x5e, 0x0]  # field.BranchIfEventBitClear(event_bit.GOT_TRITOCH, 0xa5eb3),
#
#     if src[6] == 0xc0:
#         # Special event for cliff jump behind Tritoch: reproduce the modified WC event for character gating
#         atma_event_addr = code_address(src[10:13]) + EVENT_CODE_START
#         # atma_src = rom.ROM.get_bytes(atma_event_addr, 0xed-0xd8)
#         new_src += [0xc0, 0xed, 0x2] + branch_code(atma_event_addr, 17) # field.BranchIfEventBitClear(0x2ed, 0xc74e9)
#
#     new_src += [0x4b, 0x3b, 0xa] + [  # display text box $a3b
#                 0xb6] + [0x0, 0x0, 0x0] + [0xf8, 0x37, 0x2] + [   # Yes --> branch to (placeholder), No --> branch to step back;
#                 0xfe] + src[23:]  # return; source code for jumping animation
#
#     return new_src, src_end


def branch_code(addr, offset):
    return [(offset + addr) % 0x100, ((offset + addr) >> 8) % 0x100, ((offset + addr - EVENT_CODE_START) >> 16) % 0x100]


def code_address(code):
    return (code[2] << 16) + (code[1] << 8) + code[0]


event_address_patch = {
    # Jump into Umaro's Cave: update branched event address.  Slightly risky search for 1st instance of 0xb6.
    ### Not used with JMP method ###
    #2010: lambda src, addr: src[:src.index(0xb6)+1] + branch_code(addr, 23) + src[src.index(0xb6)+4:],

    # Magitek factory Room 1 conveyor into room 2:
    #   At CC/7658 (+7), branch-if-clear [0xc0, ] to CC/7666 (+21)
    #   Paired event starts at CC/765F (+14).
    ### Not needed if using JMP method ###
    #2022: lambda src, addr: src[:10] + branch_code(addr, 21) + src[13:],

    # Magitek factory Room 2 conveyor into pit room:
    #   At CC/756C (+7), branch-if-clear [0xc0, ] to CC/7588 (+35)
    #   At CC/757A (+21), branch-if-clear [0xc0, ] to CC/7588 (+35)
    #   Paired events start at CC/7573 (+14) and CC/7581 (+28).
    ### Not needed if using JMP method ###
    #2025: lambda src, addr: src[:10] + branch_code(addr, 35) + src[13:24] + branch_code(addr, 35) + src[27:]

}

# Event tiles that are logically the same exit and share code have no
# table here: each such event script branches to the main transition in
# its event file (e.g. lete_river door_rando_mod).

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