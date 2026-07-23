from event.event import *
from event.switchyard import AddSwitchyardEvent, GoToSwitchyard
from instruction.event import EVENT_CODE_START
from log.verbose import vprint
ENTRY_EVENT_CODE_ADDR = 0xa48e3

# ============================================================================
# Ruination tube-maze randomizer (self-contained; see ruination_tube_maze_mod).
#
# The Floating Continent (map 0x18A) is a maze of "tubes" that warp the party
# between regions of a single map, plus four buttons that open fixed walls (or
# reveal a hidden tube).  In ruination mode the route through the maze is
# randomized:
#   * Tubes 1-10 are re-paired into new bidirectional connections.
#   * The four buttons are randomly assigned which lock they control.
# The player still enters at FC1 (falling in) and leaves via FC8, and every room
# is guaranteed to stay reachable.
#
# Tube9's tile is hidden behind a wall until its assigned button (lock "Ld") is
# pressed.  Travelling toward Tube9 from its partner before it is revealed bounces
# the party straight back to the partner tube; once revealed, the trip completes.
# All four lock bits are "cleared on map load" (event_bit.multipurpose_map), so the
# hidden wall and the bit stay in sync whenever map 0x18A reloads.
#
# Tube11<->Tube12 (the Save Room, which lives on its own map 0x166) is kept
# vanilla so the cross-map save-room round trip stays intact.
# ============================================================================

# Tube endpoints.  Tubes 1-8 and 11 reuse the vanilla "open"/"close" tube-graphic
# subroutines (by ROM address); tubes 9-10 draw their tube graphics inline, so
# their "open"/"close" are captured from ROM at build time (None here).  Tube 12
# is the Save Room hole on map 0x166 - it has no tube graphic of its own and is
# always the cross-map endpoint (its partner becomes the Save Room portal).
#   xy    : tube tile position (also the camera centre while travelling)
#   open  : ROM addr of the subroutine that draws the tube opening at xy (or None)
#   close : ROM addr of the subroutine that restores the closed tube at xy (or None)
#   room  : logical maze room the tube belongs to
#   range : (first, last) byte of the tube's event-tile entry code, repointed
_FC_TUBES = {
    1:  {"xy": (40,  6), "open": 0xad5d5, "close": 0xad5f0, "room": "FC1",  "range": (0xad583, 0xad5ab)},
    2:  {"xy": (32, 16), "open": 0xad602, "close": 0xad61d, "room": "FC2",  "range": (0xad5ac, 0xad5d4)},
    3:  {"xy": (67, 39), "open": 0xad6ce, "close": 0xad6e9, "room": "FC3",  "range": (0xad660, 0xad696)},
    4:  {"xy": (42, 17), "open": 0xad6fb, "close": 0xad716, "room": "FC4",  "range": (0xad697, 0xad6cd)},
    5:  {"xy": (40, 24), "open": 0xad77c, "close": 0xad797, "room": "FC4",  "range": (0xad728, 0xad751)},
    6:  {"xy": (63, 31), "open": 0xad7a9, "close": 0xad7c4, "room": "FC5",  "range": (0xad752, 0xad77b)},
    7:  {"xy": (48, 22), "open": 0xad82e, "close": 0xad849, "room": "FC4",  "range": (0xad7d6, 0xad801)},
    8:  {"xy": (77, 31), "open": 0xad85b, "close": 0xad876, "room": "FC6",  "range": (0xad802, 0xad82d)},
    9:  {"xy": (89, 25), "open": None,    "close": None,    "room": "FC7",  "range": (0xada55, 0xadabf)},
    10: {"xy": (70, 23), "open": None,    "close": None,    "room": "FC8",  "range": (0xadac0, 0xadb2a)},
    11: {"xy": (90, 43), "open": 0xad97a, "close": 0xad995, "room": "FC7",  "range": (0xad916, 0xad93f)},
    12: {"xy": (8,   8), "open": None,    "close": None,    "room": "Save", "range": (0xad940, 0xad979)},
}
# Inline tube-graphic byte ranges for tubes 9-10 (captured via Read at build time).
_FC_INLINE_GFX = {
    9:  {"open": (0xada55, 0xada6e), "close": (0xada73, 0xada83)},
    10: {"open": (0xadac0, 0xadad9), "close": (0xadade, 0xadaee)},
}
# Vanilla Save Room byte ranges, reused verbatim for the cross-map (Tube12) pair:
#   arrival : Tube11's save-arrival tail - pause, LoadMap 0x166, drop party, set $1B5
#   the exit_* ranges are the parts of Tube12's return that don't depend on which
#   0x18A tube the Save Room connects to (the FC-side LoadMap, position, open/close
#   tube graphics are substituted with the partner's; everything else is reused).
_FC_SAVE_ARRIVAL = (0xad922, 0xad93f)
_FC_SAVE_EXIT_HEAD = (0xad940, 0xad950)   # $1B5 guard, hold, sound, jump-out of hole
_FC_SAVE_EXIT_RESTORE = (0xad95d, 0xad95d)  # restore screen from fade
_FC_SAVE_EXIT_TAIL = (0xad971, 0xad978)   # wait, free screen, reset layering
_FC_TUBE_ROOM = {1: "FC1", 2: "FC2", 3: "FC3", 4: "FC4", 5: "FC4", 6: "FC5",
                 7: "FC4", 8: "FC6", 9: "FC7", 10: "FC8", 11: "FC7", 12: "Save"}

# Button tiles.  Each tile stays in its room but is randomly assigned a lock.
#   xy    : button tile position
#   layer : map layer the "pressed" graphic ($A2) is drawn on
#   room  : room the button tile lives in (must be reached to press it)
#   range : (first, last) byte of the button's event-tile entry code
_FC_BUTTONS = {
    "FCa": {"xy": (36, 28), "layer": 2, "room": "FC2", "range": (0xad645, 0xad65f)},
    "FCb": {"xy": (59, 39), "layer": 2, "room": "FC5", "range": (0xad8af, 0xad8d0)},
    "FCc": {"xy": (52, 24), "layer": 2, "room": "FC5", "range": (0xad888, 0xad8ae)},
    "FCd": {"xy": (82, 30), "layer": 1, "room": "FC7", "range": (0xad8d1, 0xad906)},
}
# Locks.  La/Lb/Lc are fixed walls between rooms; Ld reveals/gates Tube9.
#   bit  : "cleared on map load" event bit recording the lock is open
#   cam  : absolute tile to pan the camera to while the wall opens / tube reveals
#   edge : rooms joined by the wall ("TUBE9" for the Tube9 reveal)
_FC_LOCKS = {
    "La": {"bit": event_bit.multipurpose_map(6), "cam": (41, 32), "edge": ("FC2", "FC3")},  # vanilla FCa wall
    "Lb": {"bit": event_bit.multipurpose_map(8), "cam": (57, 47), "edge": ("FC3", "FC7")},  # vanilla FCb wall
    "Lc": {"bit": event_bit.multipurpose_map(7), "cam": (56, 28), "edge": ("FC3", "FC5")},  # vanilla FCc wall
    "Ld": {"bit": event_bit.multipurpose_map(9), "cam": (88, 27), "edge": "TUBE9"},         # reveals Tube9
}
_FC_ROOMS = ["FC1", "FC2", "FC3", "FC4", "FC5", "FC6", "FC7", "FC8", "Save"]


def _fc_reachable(tube_pairs, assignment, start="FC1"):
    """Return the set of rooms reachable from `start` under a candidate layout.

    tube_pairs : list of (a, b) pairs over tubes 1..12
    assignment : dict mapping button name -> lock name (a bijection)
    start      : room the party begins in with all locks closed (FC1 on entry, or
                 the Save Room's partner room when returning from a map reload)

    A keys-and-locks fixed point: a lock opens once the room holding its assigned
    button has been reached.  Most tube edges are always open; the tube edge that
    contains Tube9 is gated by lock Ld (Tube9 must be revealed to traverse it).
    """
    lock_tile_room = {lock: _FC_BUTTONS[btn]["room"] for btn, lock in assignment.items()}

    reached = {start}
    changed = True
    while changed:
        changed = False
        unlocked = {lock for lock, room in lock_tile_room.items() if room in reached}

        def connect(u, v):
            nonlocal changed
            if u in reached and v not in reached:
                reached.add(v); changed = True
            elif v in reached and u not in reached:
                reached.add(u); changed = True

        for a, b in tube_pairs:
            if 9 in (a, b) and "Ld" not in unlocked:
                continue  # Tube9 still hidden -> the party is bounced back
            connect(_FC_TUBE_ROOM[a], _FC_TUBE_ROOM[b])
        for lock in ("La", "Lb", "Lc"):
            if lock in unlocked:
                connect(*_FC_LOCKS[lock]["edge"])
    return reached


def _fc_randomize_maze(rng):
    """Pick a (tube_pairs, assignment) that keeps every room reachable."""
    tube_ids = list(range(1, 13))  # tubes 1..12
    locks = ["La", "Lb", "Lc", "Ld"]
    buttons = ["FCa", "FCb", "FCc", "FCd"]
    for _ in range(20000):
        rng.shuffle(tube_ids)
        pairs = [(tube_ids[i], tube_ids[i + 1]) for i in range(0, 12, 2)]
        if any(_FC_TUBE_ROOM[a] == _FC_TUBE_ROOM[b] for a, b in pairs):
            continue  # don't pair two tubes that live in the same room
        if any({9, 12} == {a, b} for a, b in pairs):
            continue  # avoid the gated-and-cross-map Tube9<->Tube12 combination
        shuffled = locks[:]
        rng.shuffle(shuffled)
        assignment = dict(zip(buttons, shuffled))
        if len(_fc_reachable(pairs, assignment)) != len(_FC_ROOMS):
            continue  # every room must be reachable from the FC1 entry
        # Visiting the Save Room reloads map 0x18A (resetting every lock) and drops
        # the party in the Save Room's partner room, so the exit (FC8) must still be
        # reachable starting fresh from there - otherwise a save detour could strand
        # the player before the boss.
        save_partner = next(a if b == 12 else b for a, b in pairs if 12 in (a, b))
        if "FC8" in _fc_reachable(pairs, assignment, _FC_TUBE_ROOM[save_partner]):
            return pairs, assignment
    # Fallback: vanilla layout (always solvable)
    return ([(1, 2), (3, 4), (5, 6), (7, 8), (9, 10), (11, 12)],
            {"FCa": "La", "FCb": "Lb", "FCc": "Lc", "FCd": "Ld"})

# TODO game can freeze, is this something i did or a bug in emulator/game?
#      go through and when you get to the hole that brings you to three possible holes (including the one you came from)
#      go thruogh left hole, hit both switches and go back through the hole you came from
#      can ignore the right hole since it leads nowhere and now go back through the north hole
#      now run around and take the path you just created back to the hole you came from to reach the two switches
#      going in that hole will freeze

class FloatingContinent(Event):
    def __init__(self, events, rom, args, dialogs, characters, items, maps, enemies, espers, shops, warps):
        super().__init__(events, rom, args, dialogs, characters, items, maps, enemies, espers, shops, warps)
        self.MAP_SHUFFLE = args.map_shuffle or args.door_randomize_dungeon_crawl or args.ruination_mode

    def name(self):
        return "Floating Continent"

    def character_gate(self):
        return self.characters.SHADOW

    def init_rewards(self):
        self.reward1 = self.add_reward(RewardType.CHARACTER | RewardType.ESPER)
        self.reward2 = self.add_reward(RewardType.ESPER | RewardType.ITEM)
        self.reward3 = self.add_reward(RewardType.CHARACTER | RewardType.ESPER)

    def mod(self):
        self.entry_id = 1556
        self.exit_id = 1557

        self.shadow_leaves_mod()
        self.airship_battle_mod()
        if not self.args.fixed_encounters_original:
            self.airship_fixed_battles_mod()
        self.ultros_chupon_battle_mod()
        self.air_force_battle_mod()

        self.ground_shadow_npc_id = 0x1b
        self.ground_shadow_npc = self.maps.get_npc(0x18a, self.ground_shadow_npc_id)

        self.ground_reward_position_mod()
        if self.reward1.type == RewardType.CHARACTER:
            self.ground_character_mod(self.reward1.id)
        elif self.reward1.type == RewardType.ESPER:
            self.ground_esper_mod(self.reward1.id)
        self.finish_ground_check()

        self.save_point_hole_mod()
        self.airship_return_mod()
        self.atma_battle_mod()

        if self.reward2.type == RewardType.ESPER:
            self.atma_esper_mod(self.reward2.id)
        elif self.reward2.type == RewardType.ITEM:
            self.atma_item_mod(self.reward2.id)

        self.statues_scene_mod()
        self.timer_mod()
        self.nerapa_battle_mod()

        if self.reward3.type == RewardType.CHARACTER:
            self.escape_character_mod(self.reward3.id)
        elif self.reward3.type == RewardType.ESPER:
            self.escape_esper_mod(self.reward3.id)

        self.log_reward(self.reward1)
        self.log_reward(self.reward2)
        self.log_reward(self.reward3)

        if self.MAP_SHUFFLE:
            self.map_shuffle_mod()

        if self.args.ruination_mode:
            self.ruination_tube_maze_mod()

    def shadow_leaves_mod(self):
        # remove shadow from party at floating continent (if return to airship or after atma)
        # use this space to add some new functions we need
        space = Reserve(0xad9fc, 0xada2f, "floating continent shadow leaves party", field.NOP())

        # copy some instructions to here so can make room for deleting lights where code originally was
        self.enter_floating_continent_function = space.next_address
        space.copy_from(0xa5a42, 0xa5a4a) # copy loading the map, showing party and holding screen
        space.write(
            field.Return(),
        )

        # also do the same thing for when returning from save point hole
        self.return_from_save_map_function = space.next_address
        space.copy_from(0xad951, 0xad95c) # copy loading the map and positioning the party
        space.write(
            field.Return(),
        )

        # delete the lights around the statues after the map is loaded
        # otherwise airship won't show up when 4 people in party and char (or esper?) still on ground
        # i create the lights again when the statue scene starts
        self.delete_lights_function = space.next_address
        space.write(
            field.DeleteEntity(0x1d),
            field.DeleteEntity(0x1e),
            field.DeleteEntity(0x1f),
            field.DeleteEntity(0x20),
            field.DeleteEntity(0x21),
            field.Return(),
        )

    def airship_battle_mod(self):
        space = Reserve(0xa582a, 0xa5839, "floating continent do not enforce 3 characters in party", field.NOP())
        space = Reserve(0xa592f, 0xa5931, "floating continent skip IAF dialog", field.NOP())

        # skip 3 out of the 6 battles before ultros/chupon battle
        space = Reserve(0xa5978, 0xa597d, "floating continent skip to chupon appearing in sky", field.NOP())
        space.write(
            field.Branch(0xa59bb),
        )

        # small pause to prevent chupon from clipping air force sprite in sky
        space = Reserve(0xa59bb, 0xa59be, "floating continent skip something approaches dialog", field.NOP())
        space.write(
            field.Pause(2.0),
        )

        space = Reserve(0xa5a42, 0xa5a4a, "floating continent enter after defeating air force", field.NOP())
        space.write(
            field.Call(self.enter_floating_continent_function),
            field.Call(self.delete_lights_function), # delete lights so airship shows up
        )

        space = Reserve(0xa5a68, 0xa5a6a, "floating continent skip kefka, gestahl, statues ahead dialog", field.NOP())
        if self.MAP_SHUFFLE:
            space.write(field.SetEventBit(event_bit.DEFEATED_AIR_FORCE))

    def airship_fixed_battles_mod(self):
        # change iaf battles to front attacks, even if the original pack id happens to be the new random one
        # because other random formations in the pack may not work with pincer attacks
        
        # adding an unused pack id (416) to increase variety of encounters
        battle_background = 48 # airship, right

        pack_start_addresses = [
            (382, 0xa5932), #sky armor / spit fire
            (416, 0xa59fc), #unused
            (382, 0xa5a0d)] #sky armor / spit fire
        for pack_start_address in pack_start_addresses:
            pack_id = pack_start_address[0]
            start_address = pack_start_address[1]
            space = Reserve(start_address, start_address + 2, "floating continent iaf invoke fixed battle")
            space.write(
                field.InvokeBattleType(pack_id, field.BattleType.FRONT, battle_background, check_game_over = False),
            )

    def ultros_chupon_battle_mod(self):
        boss_pack_id = self.get_boss("Ultros/Chupon")

        battle_type = field.BattleType.FRONT
        battle_background = 48 # airship, right
        if boss_pack_id == self.enemies.packs.get_id("Cranes"):
            battle_type = field.BattleType.PINCER
            battle_background = 37 # airship, center

        space = Reserve(0xa5a1e, 0xa5a24, "floating continent invoke battle ultros/chupon", field.NOP())
        space.write(
            field.InvokeBattleType(boss_pack_id, battle_type, battle_background),
        )

    def air_force_battle_mod(self):
        if self.args.flashes_remove_most or self.args.flashes_remove_worst:
            # Slow the scrolling background by modifying the ADC command.
            space = Reserve(0x2b1b1, 0x2b1b3, "falling through clouds background movement")
            space.write(
                asm.ADC(0x0001, asm.IMM16) #default: 0x0006
            )

        boss_pack_id = self.get_boss("Air Force")
        battle_background = 7 # sky, falling

        space = Reserve(0xa5a3b, 0xa5a41, "floating continent invoke battle air force", field.NOP())
        self.air_force_battle_src = [field.InvokeBattle(boss_pack_id, battle_background)]
        space.write(
            self.air_force_battle_src
        )
        self.air_force_battle_addr = space.start_address


    def ground_reward_position_mod(self):
        self.ground_shadow_npc.x = 11
        self.ground_shadow_npc.y = 13

        space = Reserve(0xad9a7, 0xad9aa, "floating continent move party above shadow", field.NOP())

    def ground_character_mod(self, character):
        self.ground_shadow_npc.sprite = character
        self.ground_shadow_npc.palette = self.characters.get_palette(character)

        space = Reserve(0xad9b5, 0xad9b7, "floating continent down with the empire dialog", field.NOP())

        if self.args.ruination_mode is not None:
            from event.ruination import PARTY_INTERACTION_SCRIPT_ADDRS
            branch_refresh_src = [
                field.ChangeNPCEventAddress(character, PARTY_INTERACTION_SCRIPT_ADDRS[character]),
                field.SetupBranchRecruit(character),
                field.Call(field.REFRESH_CHARACTERS_AND_SELECT_PARTY),
                field.FinalizeBranchRecruit(),
                field.Return(),
            ]
            branch_refresh = Write(Bank.CA, branch_refresh_src, "floating continent branch-aware refresh")
            refresh_addr = branch_refresh.start_address
        else:
            refresh_addr = field.REFRESH_CHARACTERS_AND_SELECT_PARTY

        space = Reserve(0xad9c0, 0xad9ed, "floating continent add character on ground", field.NOP())
        space.write(
            field.RecruitCharacter(character),

            # i do not know why, but i need to delete the first npcs specifically before the select party screen
            # it prevents a softlock when already recruited 12+ characters
            # seems like after 11 characters they start to overwrite the npcs so i need to delete those first to make room
            field.DeleteEntity(0x10),
            field.DeleteEntity(0x11),
            field.DeleteEntity(0x12),
            field.Call(refresh_addr),

            # loading the map here instead of just fading in the screen prevents a graphics bug with
            # the save point when the player has already acquired around 8+ characters
            # it also reloads the npcs that were deleted before the select party screen was shown
            field.LoadMap(0x18a, direction.RIGHT, default_music = False, x = 10, y = 13, fade_in = False, entrance_event = True),
            field.DeleteEntity(0x1b),
            field.FadeInScreen(),
        )

    def ground_esper_mod(self, esper):
        self.ground_shadow_npc.sprite = 91
        self.ground_shadow_npc.palette = 2
        self.ground_shadow_npc.split_sprite = 1
        self.ground_shadow_npc.direction = direction.UP

        space = Reserve(0xad9b1, 0xad9ed, "floating continent add esper on ground", field.NOP())
        space.write(
            field.AddEsper(esper),
            field.Dialog(self.espers.get_receive_esper_dialog(esper)),
            field.DeleteEntity(self.ground_shadow_npc_id),
            field.Branch(space.end_address + 1),
        )

    def finish_ground_check(self):
        src = [
            Read(0xad9ee, 0xad9f2), # clear ground npc bit, set shadow recruited bit, update party leader
            field.FinishCheck(),
            field.Return(),
        ]
        space = Write(Bank.CA, src, "floating continent ground finish check")
        finish_check = space.start_address

        space = Reserve(0xad9ee, 0xad9f2, "floating continent set bits, update leader after shadow", field.NOP())
        space.write(
            field.Call(finish_check),
        )

    def save_point_hole_mod(self):
        if self.args.ruination_mode:
            # In ruination the Save Room is part of the randomized tube maze:
            # ruination_tube_maze_mod re-points Tube12's event (which spans this
            # region), and folds the equivalent map load + light deletion into its
            # own Save Room -> partner transition.  Leave this region for it.
            return
        space = Reserve(0xad951, 0xad95c, "floating continent return from save point hole", field.NOP())
        space.write(
            field.Call(self.return_from_save_map_function),
            field.Call(self.delete_lights_function), # delete lights so airship shows up
        )

    def airship_return_mod(self):
        self.dialogs.set_text(2135, "Do you wish to return?<line><choice> (No)<line><choice> (Yes)<end>")

        space = Reserve(0xa5a8b, 0xa5a8f, "floating continent do not remove shadow if return to airship", field.NOP())

        # do not set the shadow npc even bit again (otherwise when you return character/esper would be there again)
        space = Reserve(0xa5ab5, 0xa5abc, "floating continent do not put shadow npc back on map", field.NOP())

        # If ruination mode, don't show the airship
        map_id = 0x18a
        airship_npc_id = 0x23
        airship_npc = self.maps.get_npc(map_id, airship_npc_id)
        airship_npc.event_byte = npc_bit.event_byte(npc_bit.ALWAYS_OFF)
        airship_npc.event_bit = npc_bit.event_bit(npc_bit.ALWAYS_OFF)

    def atma_battle_mod(self):
        boss_pack_id = self.get_boss("AtmaWeapon")

        space = Reserve(0xada30, 0xada36, "floating continent invoke battle atmaweapon", field.NOP())
        space.write(
            field.InvokeBattle(boss_pack_id),
        )

    def atma_esper_item_mod(self, esper_item_instructions):
        src = [
            esper_item_instructions,
            field.SetEventBit(event_bit.DEFEATED_ATMAWEAPON),
            field.FinishCheck(),
            field.Return(),
        ]
        space = Write(Bank.CA, src, "floating continent atma weapon finish check")
        finish_check = space.start_address

        space = Reserve(0xada3f, 0xada46, "floating continent do not remove shadow after fighting atma", field.NOP())
        space.write(
            field.Call(finish_check),
        )

    def atma_esper_mod(self, esper):
        self.atma_esper_item_mod([
            field.AddEsper(esper),
            field.Dialog(self.espers.get_receive_esper_dialog(esper)),
        ])

    def atma_item_mod(self, item):
        self.atma_esper_item_mod([
            field.AddItem(item),
            field.Dialog(self.items.get_receive_dialog(item)),
        ])

    def statues_scene_mod(self):
        kefka_npc_id = 0x11
        kefka_npc = self.maps.get_npc(0x18a, kefka_npc_id)
        kefka_npc.x = 60
        kefka_npc.y = 7

        gestahl_npc_id = 0x1c
        gestahl_npc = self.maps.get_npc(0x18a, gestahl_npc_id)
        gestahl_npc.x = 57
        gestahl_npc.y = 7

        space = Reserve(0xadd22, 0xaddb3, "floating continent statues move camera", field.NOP())
        space.write(
            # first create the lights i deleted
            field.CreateEntity(0x1d),
            field.CreateEntity(0x1e),
            field.CreateEntity(0x1f),
            field.CreateEntity(0x20),
            field.CreateEntity(0x21),
            field.ShowEntity(0x1d),
            field.ShowEntity(0x1e),
            field.ShowEntity(0x1f),
            field.ShowEntity(0x20),
            field.ShowEntity(0x21),
            field.RefreshEntities(),

            field.HoldScreen(),
            field.EntityAct(field_entity.CAMERA, True,
                field_entity.SetSpeed(field_entity.Speed.SLOW),
                field_entity.Move(direction.UP, 5),
            ),
        )

        space = Reserve(0xaddf0, 0xade0c, "floating continent statues party approach kefka", field.NOP())
        space.write(
            field.EntityAct(field_entity.CAMERA, False,
                field_entity.Move(direction.DOWN, 3),
            ),
            field.EntityAct(field_entity.PARTY0, True,
                field_entity.Move(direction.UP, 2),
            ),
            field.EntityAct(kefka_npc_id, True,
                field_entity.Turn(direction.DOWN),
            ),
            field.EntityAct(gestahl_npc_id, True,
                field_entity.Turn(direction.DOWN),
            ),
        )

        space = Reserve(0xade0f, 0xade11, "floating continent statues gestahl has goose bumps dialog", field.NOP())

        space = Reserve(0xade24, 0xade24, "floating continent statues kefka raise hand")
        space.write(kefka_npc_id)

        # for some reason the animation gestahl uses does not look right with kefka, change it
        space = Reserve(0xade26, 0xade26, "floating continent statues kefka raise hand animation")
        space.write(field_entity.AnimateFrontHandsUp())

        space = Reserve(0xade28, 0xade2b, "floating continent statues don't move camera down before shooting light", field.NOP())

        space = Reserve(0xade52, 0xade52, "floating continent statues kefka turn down during light")
        space.write(kefka_npc_id)

        begin_escape = 0xae3d6
        src = [
            field.EntityAct(0x21, False,
                field_entity.SetPosition(60, 4),
                field_entity.MoveDiagonal(direction.DOWN, 1, direction.LEFT, 1),
                field_entity.MoveDiagonal(direction.DOWN, 1, direction.LEFT, 1),
                field_entity.MoveDiagonal(direction.DOWN, 1, direction.LEFT, 1),
            ),
            field.EntityAct(0x1f, False,
                field_entity.SetPosition(60, 4),
                field_entity.Move(direction.DOWN, 8),
                field_entity.Move(direction.DOWN, 8),
            ),
            field.EntityAct(field_entity.CAMERA, False,
                field_entity.SetSpeed(field_entity.Speed.FAST),
                field_entity.Move(direction.DOWN, 3),
                field_entity.SetSpeed(field_entity.Speed.SLOW),
            ),
            field.ShakeScreen(1, True, True, True, True, True),
            field.Pause(0.25),
            field.EntityAct(gestahl_npc_id, False,
                field_entity.AnimateKnockedOut2(),
            ),
            field.EntityAct(field_entity.PARTY0, False,
                field_entity.AnimateAttacked(),
                field_entity.DisableWalkingAnimation(),
                field_entity.AnimateKnockedOut(),
                field_entity.SetSpeed(field_entity.Speed.FAST),
                field_entity.MoveDiagonal(direction.DOWN, 1, direction.RIGHT, 1),
                field_entity.MoveDiagonal(direction.DOWN, 1, direction.RIGHT, 1),
                field_entity.MoveDiagonal(direction.DOWN, 1, direction.RIGHT, 1),
                field_entity.MoveDiagonal(direction.DOWN, 1, direction.RIGHT, 1),
                field_entity.MoveDiagonal(direction.DOWN, 1, direction.RIGHT, 1),
                field_entity.MoveDiagonal(direction.DOWN, 1, direction.RIGHT, 1),
                field_entity.MoveDiagonal(direction.DOWN, 1, direction.RIGHT, 1),
            ),
            field.Call(0xad033),
            field.WaitForEntityAct(0x21),
            field.WaitForEntityAct(0x1f),

            field.Branch(begin_escape)
        ]
        space = Write(Bank.CA, src, "floating continent statues shoot light at gestahl and party")
        light_shot = space.start_address

        space = Reserve(0xade5e, 0xade63, "floating continent statues light shot branch", field.NOP())
        space.write(
            field.Branch(light_shot),
        )

    def timer_mod(self):
        if self.args.event_timers_random:
            import random

            # randomize timer between 5 and 8 minutes
            seconds = random.randint(300, 480)

            space = Reserve(0xae3f6, 0xae3f7, "floating continent timer 0")
            space.write(
                (seconds * 60).to_bytes(2, "little"),
            )

            timer_display = f"{seconds // 60}:{seconds % 60:>02}"
            self.log_change(f"Timer 6:00", timer_display)

            # floating continent escape has a second timer which expires 5 seconds before game over timer
            seconds -= 5
            space = Reserve(0xae3fc, 0xae3fd, "floating continent timer 2")
            space.write(
                (seconds * 60).to_bytes(2, "little"),
            )
        elif self.args.event_timers_none:
            space = Reserve(0xae3f5, 0xae400, "floating continent timers", field.NOP())

    def nerapa_battle_mod(self):
        boss_pack_id = self.get_boss("Nerapa")

        space = Reserve(0xada48, 0xada4e, "floating continent invoke battle nerapa", field.NOP())
        space.write(
            field.InvokeBattle(boss_pack_id),
        )

    def escape_mod(self, npc_id, airship_instructions):
        space = Reserve(0xae3ec, 0xae3f0, "floating continent get outta here dialog", field.NOP())

        if self.args.ruination_mode:
            # Don't show airship
            space = Reserve(0xa578e, 0xa579c, "floating continent ruination no airship NPC", field.NOP())
            space.write([
                field.EntityAct(field_entity.PARTY0, True,
                                field_entity.Turn(direction.LEFT),
                                ),
            ])
        space = Reserve(0xa57c0, 0xa57c0, "floating continent update character created at escape")
        space.write(npc_id)
        space = Reserve(0xa57c2, 0xa57c2, "floating continent update character placed on map at escape")
        space.write(npc_id)
        space = Reserve(0xa57cc, 0xa57cc, "floating continent update character shows at escape")
        space.write(npc_id)
        space = Reserve(0xa57cd, 0xa57cd, "floating continent update character animates in at escape")
        space.write(npc_id)
        space = Reserve(0xa57e1, 0xa57e3, "floating continent skip shadow arrives at airship dialog", field.NOP())
        if not (self.MAP_SHUFFLE and self.reward3.type == RewardType.CHARACTER):
            # For map shuffle character reward, use this space to branch to exit animation (see below)
            space = Reserve(0xa57ea, 0xa57ea, "floating continent update character who follows party to escape")
            space.write(npc_id)

        space = Reserve(0xa48cc, 0xa48cf, "floating continent do not clear shadow bits if don't wait at airship", field.NOP())

        # Restore y-party switching when leaving the floating continent via the ending
        # event (the escape sequence after defeating Nerapa).
        src = []
        if self.args.ruination_mode:
            from event.ruination import RESTORE_Y_PARTY_SWITCH
            src += [field.Call(RESTORE_Y_PARTY_SWITCH)]
        src += [
            field.SetEventBit(event_bit.FINISHED_FLOATING_CONTINENT),
            field.StopScreenShake(),
            field.FreeScreen(),
            field.ClearEventBit(event_bit.TEMP_SONG_OVERRIDE),
        ]
        if self.MAP_SHUFFLE:
            src += [
                airship_instructions,  # airship instructions include load map.  FinishCheck is in there.
                field.Return(),
            ]
            # We need to stop the screen from fading down before the reward is given.
            space = Reserve(0xa48d8, 0xa48d9, 'keep screen up for reward map shuffle', field.NOP())
        else:
            src += [
                airship_instructions,
                field.FinishCheck(),
                field.Return(),
            ]
        space = Write(Bank.CA, src, "floating continent return to airship")
        airship_return = space.start_address

        return_addr = [0xa48dd, 0xa48e2]
        if self.MAP_SHUFFLE and self.reward3.type == RewardType.CHARACTER:
            # The objective check must be before we leave the screen. This is fine for espers & items, but...
            # For characters, do it after the 2nd character lands
            # CA/57E6: B2    Call subroutine $CA5806  character jumps off FC after shadow arrives
            # ... shadow jumps off (we'll delete 0x03 after character select & skip this)
            # CA/5801: B2    Call subroutine $CA48D6
            return_addr = [0xa57e6, 0xa57eb]
        space = Reserve(return_addr[0], return_addr[1], "floating continent return to airship", field.NOP())
        space.write(
            field.Branch(airship_return),
        )

    def escape_character_mod(self, character):
        space = Reserve(0xa579d, 0xa57b2, "floating continent wait dialogs", field.NOP())
        if self.MAP_SHUFFLE:
            # CA/57E6: B2    Call subroutine $CA5806  character jumps off FC after shadow arrives
            # ... shadow jumps off (we'll delete npc after character select & skip this)
            # CA/5801: B2    Call subroutine $CA48D6
            escape_src = [
                #field.FadeOutScreen(),
                #field.DeleteEntity(character),  # Maybe we don't need any of this?
                #field.HideEntity(character),
                #field.RefreshEntities(),    # Maybe this prevents the 'recruit an npc' later?
                field.RecruitAndSelectParty(character),
                field.FadeInScreen(),
                field.FinishCheck(),   # Must be done here: might return to the world map!
                field.Call(0xa5806),   # complete jumping animation
                #field.Call(0xa48d6),  Replicate up to map load
                #Read(0xa48d6, 0xa48dc), # clear event bit, fade screen, wait for fade & animation.
                field.ClearEventBit(event_bit.CONTINUE_MUSIC_DURING_BATTLE),
                field.FadeOutScreen(speed=0x08),
                field.WaitForFade(),
                field.WaitForEntityAct(field_entity.PARTY0),
                field.FreeScreen(),
            ] + GoToSwitchyard(self.exit_id, map='field')
        else:
            escape_src = [
                field.LoadMap(0x06, direction.DOWN, default_music = True, x = 16, y = 6, fade_in = False),
                field.RecruitAndSelectParty(character),
                field.FadeInScreen(),
            ]
        self.escape_mod(character, escape_src)

    def escape_esper_mod(self, esper):
        # use guest character to give esper reward
        guest_char_id = 0x0f
        guest_char = self.maps.get_npc(0x189, guest_char_id)

        random_sprite = self.characters.get_random_esper_item_sprite()
        random_sprite_palette = self.characters.get_palette(random_sprite)

        space = Reserve(0xa579d, 0xa57b2, "floating continent wait dialogs", field.NOP())
        space.write(
            field.SetSprite(guest_char_id, random_sprite),
            field.SetPalette(guest_char_id, random_sprite_palette),
            field.RefreshEntities(),
        )

        if self.MAP_SHUFFLE:
            escape_src = [
                field.DeleteEntity(guest_char_id),
                field.RefreshEntities(),
                field.AddEsper(esper),
                field.FinishCheck(),
                field.Dialog(self.espers.get_receive_esper_dialog(esper)),
                field.FadeOutScreen(),
                field.WaitForFade(),
            ] + GoToSwitchyard(self.exit_id, map='field')
        else:
            escape_src = [
                field.DeleteEntity(guest_char_id),
                field.RefreshEntities(),
                field.LoadMap(0x06, direction.DOWN, default_music = True, x = 16, y = 6, fade_in = True, entrance_event = True),
                field.AddEsper(esper),
                field.Dialog(self.espers.get_receive_esper_dialog(esper)),
            ]
        self.escape_mod(guest_char_id, escape_src)

    def ruination_tube_maze_mod(self):
        # Randomize the route through the Floating Continent tube maze.  See the
        # module header above for the model.  All generated event code goes into
        # Bank.CA (same bank as the vanilla open/close/wall subroutines it calls)
        # and the vanilla tube/button event tiles are re-pointed to it.
        import random

        tube_pairs, assignment = _fc_randomize_maze(random)

        # ---- spoiler log ----------------------------------------------------
        vprint("Floating Continent tube maze:")
        for a, b in tube_pairs:
            vprint(f"  Tube{a} <-> Tube{b}   ({_FC_TUBE_ROOM[a]} <-> {_FC_TUBE_ROOM[b]})")
        for btn, lock in assignment.items():
            edge = _FC_LOCKS[lock]["edge"]
            what = "reveals Tube9" if edge == "TUBE9" else f"{edge[0]}<->{edge[1]} wall"
            vprint(f"  Button {btn} -> {lock} ({what})")

        # ---- capture vanilla bytes we reuse (before any re-pointing) ---------
        gfx = {}
        for tube, ranges in _FC_INLINE_GFX.items():
            gfx[tube] = {
                "open": Read(ranges["open"][0], ranges["open"][1]),
                "close": Read(ranges["close"][0], ranges["close"][1]),
            }
        save_arrival = Read(*_FC_SAVE_ARRIVAL)
        save_exit_head = Read(*_FC_SAVE_EXIT_HEAD)
        save_exit_restore = Read(*_FC_SAVE_EXIT_RESTORE)
        save_exit_tail = Read(*_FC_SAVE_EXIT_TAIL)

        # ---- reclaim the superseded vanilla tube/button event code ----------
        # Their open/close, slide-in/out and wall subroutines live outside these
        # ranges and are kept (the new code still calls them by address), but the
        # event bodies themselves are dead now.  Freeing them lets the new, more
        # compact animations be written back into this space first, spilling into
        # ordinary free space only once it runs out.  Must come after the Reads
        # above, which snapshot bytes from inside these ranges.
        for entry in list(_FC_TUBES.values()) + list(_FC_BUTTONS.values()):
            Free(entry["range"][0], entry["range"][1])

        # ---- map + tile position of a tube's event tile (Tube12 is on 0x166) -
        def event_tile(tube):
            return (0x166 if tube == 12 else 0x18a), _FC_TUBES[tube]["xy"]

        # per-tube open / close code: a Call for tubes 1-8, raw bytes for 9-10
        def open_code(tube):
            addr = _FC_TUBES[tube]["open"]
            return [field.Call(addr)] if addr is not None else [gfx[tube]["open"]]

        def close_code(tube):
            addr = _FC_TUBES[tube]["close"]
            return [field.Call(addr)] if addr is not None else [gfx[tube]["close"]]

        # ---- camera/party pan: a near-straight, symmetric path from (0,0) to ---
        # (dx, dy), minimizing distance travelled with 1:1 and 1:2/2:1 diagonal
        # moves plus linear runs.  The diagonal run is split symmetrically around a
        # central run, e.g. (8, 21) -> [4 down-right(1:2), down 5, 4 down-right(1:2)].
        def pan_path(dx, dy):
            ax, ay = abs(dx), abs(dy)
            hdir = direction.RIGHT if dx > 0 else direction.LEFT
            vdir = direction.DOWN if dy > 0 else direction.UP

            def linear(d, n):
                ops = []
                while n > 0:
                    step = min(8, n)
                    ops.append(field_entity.Move(d, step))
                    n -= step
                return ops

            if ax == 0:
                return linear(vdir, ay)
            if ay == 0:
                return linear(hdir, ax)

            if ay >= ax:                       # vertical dominant
                if ay <= 2 * ax:               # slope 1..2: 1:1 and 1:2 diagonals
                    n11, n12 = 2 * ax - ay, ay - ax
                    d11 = [field_entity.MoveDiagonal(hdir, 1, vdir, 1) for _ in range(n11)]
                    d12 = [field_entity.MoveDiagonal(hdir, 1, vdir, 2) for _ in range(n12)]
                    split, middle = (d12, d11) if n12 >= n11 else (d11, d12)
                else:                          # slope > 2: 1:2 diagonal and linear
                    split = [field_entity.MoveDiagonal(hdir, 1, vdir, 2) for _ in range(ax)]
                    middle = linear(vdir, ay - 2 * ax)
            else:                              # horizontal dominant
                if ax <= 2 * ay:               # slope 1/2..1: 1:1 and 2:1 diagonals
                    n11, n21 = 2 * ay - ax, ax - ay
                    d11 = [field_entity.MoveDiagonal(hdir, 1, vdir, 1) for _ in range(n11)]
                    d21 = [field_entity.MoveDiagonal(hdir, 2, vdir, 1) for _ in range(n21)]
                    split, middle = (d21, d11) if n21 >= n11 else (d11, d21)
                else:                          # slope < 1/2: 2:1 diagonal and linear
                    split = [field_entity.MoveDiagonal(hdir, 2, vdir, 1) for _ in range(ay)]
                    middle = linear(hdir, ax - 2 * ay)

            half = len(split) // 2
            return split[:half] + middle + split[half:]

        # ---- write new code (into reclaimed space) and point the tile at it --
        def repoint(map_id, xy, new_src, description):
            new_code = Write(Bank.CA, new_src, description)
            event = self.maps.get_event(map_id, xy[0], xy[1])
            event.event_address = new_code.start_address - EVENT_CODE_START

        # ---- exit animation, tied to the tube being EXITED ------------------
        # Every tube but Tube11 is left by stepping DOWN out of the mouth (the
        # generic vanilla slide-out CAD577, which shows the party, hops in place
        # and faces down at dst+2).  Tube11 alone is left by stepping UP: the party
        # is at dst+2 and jumps up 3 to dst-1 (this reconstructs Tube11's vanilla
        # save-room exit, C2 C6 DD 88, but waits for the hop to finish).
        def exit_sequence(dst):
            if dst == 11:
                return (
                    open_code(11)
                    + [field.ShowEntity(field_entity.PARTY0),
                       field.RefreshEntities(),
                       field.EntityAct(field_entity.PARTY0, True,
                                       field_entity.SetSpeed(field_entity.Speed.NORMAL),
                                       field_entity.EnableWalkingAnimation(),
                                       field_entity.AnimateHighJump(),
                                       field_entity.Move(direction.UP, 3)),
                       field.Pause(0.25)]
                    + close_code(11)
                )
            return open_code(dst) + [field.Call(0xad577)] + close_code(dst)

        # ---- standard tube transition: src tube -> dst tube -----------------
        # The party is hidden, then we pan the CAMERA (which ignores terrain
        # collision) to the destination and teleport the hidden party there.
        # Moving the party itself across the map would let scripted movement jam
        # against walls on a randomized route - stranding the party mid-tile or
        # hard-locking the event - so we never walk the party across the maze.
        def tube_transition(src, dst):
            s = _FC_TUBES[src]; d = _FC_TUBES[dst]
            dx = d["xy"][0] - s["xy"][0]
            dy = d["xy"][1] - s["xy"][1]
            return (
                open_code(src)                                  # open the tube under the party
                + [field.Call(0xad566)]                         # party drops in & is hidden (fast)
                + close_code(src)                               # restore the closed tube graphic
                + [field.HoldScreen()]                          # detach the camera from the party
                + [field.EntityAct(field_entity.CAMERA, True,
                                   field_entity.SetSpeed(field_entity.Speed.FAST),
                                   *pan_path(dx, dy))]          # pan the camera to the destination
                + [field.EntityAct(field_entity.PARTY0, False,
                                   field_entity.SetPosition(d["xy"][0], d["xy"][1] + 2))]  # teleport hidden party
                + [field.FreeScreen()]                          # camera re-locks onto the party
                + exit_sequence(dst)                            # party pops out (up for Tube11, else down)
                + [field.EntityAct(field_entity.PARTY0, True, field_entity.SetSpriteLayer(0)),
                   field.Return()]
            )

        # ---- gated transition: partner -> Tube9 ------------------------------
        # The party always drops in and the camera travels toward Tube9.  Only at
        # the arrival point do we check the reveal: if Tube9 is open, the party
        # pops out there; if not, the camera travels back and the party re-exits
        # the tube it entered (a "bounced" round trip, nicer than a dead stop).
        def gated_transition(partner, ld_bit):
            p = _FC_TUBES[partner]["xy"]
            t9 = _FC_TUBES[9]["xy"]
            dx, dy = t9[0] - p[0], t9[1] - p[1]
            return (
                open_code(partner) + [field.Call(0xad566)] + close_code(partner)
                + [field.HoldScreen()]
                + [field.EntityAct(field_entity.CAMERA, True,
                                   field_entity.SetSpeed(field_entity.Speed.FAST),
                                   *pan_path(dx, dy))]              # travel toward Tube9
                + [field.BranchIfEventBitSet(ld_bit, "TUBE9_OPEN")]
                # Tube9 still hidden: travel back and re-exit the partner tube
                + [field.EntityAct(field_entity.CAMERA, True, *pan_path(-dx, -dy))]
                + [field.EntityAct(field_entity.PARTY0, False,
                                   field_entity.SetPosition(p[0], p[1] + 2))]
                + [field.FreeScreen()]
                + exit_sequence(partner)
                + [field.EntityAct(field_entity.PARTY0, True, field_entity.SetSpriteLayer(0)),
                   field.Return()]
                # Tube9 revealed: arrive and pop out at Tube9
                + ["TUBE9_OPEN"]
                + [field.EntityAct(field_entity.PARTY0, False,
                                   field_entity.SetPosition(t9[0], t9[1] + 2))]
                + [field.FreeScreen()]
                + exit_sequence(9)
                + [field.EntityAct(field_entity.PARTY0, True, field_entity.SetSpriteLayer(0)),
                   field.Return()]
            )

        # ---- cross-map transitions for the Save Room pair (Tube12 <-> X) -----
        # X (on map 0x18A) -> Save Room (map 0x166): play X's tube entry, then the
        # vanilla save-arrival tail (LoadMap 0x166, drop the party, set $1B5).
        def x_to_save(x):
            return (open_code(x) + [field.Call(0xad566)] + close_code(x)
                    + [save_arrival])

        # Save Room (Tube12) -> X: the vanilla save-exit, but the FC-side LoadMap,
        # landing position and tube graphics are X's instead of Tube11's.  The
        # LoadMap/position bytes match vanilla flags exactly (6A .. / 31 04 D5 ..).
        # delete_lights_function mirrors the vanilla save-point-hole return (see
        # save_point_hole_mod) so the statue lights don't reappear on this reload.
        def save_to_x(x):
            xx, xy = _FC_TUBES[x]["xy"]
            # Centre the camera where the party ends: Tube11 hops UP to y-1, every
            # other tube stays put at y+2 after the down slide-out.
            end_y = (xy - 1) if x == 11 else (xy + 2)
            return (
                [save_exit_head]
                + [0x6A, 0x8A, 0x25, xx, end_y & 0xff, 0x00]             # LoadMap 0x18A, camera @ (x, end_y)
                + [0x31, 0x04, 0xD5, xx, (xy + 2) & 0xff, 0xFF]          # set party pos (x, y+2)
                + [field.Call(self.delete_lights_function)]              # delete statue lights
                + [save_exit_restore]
                + exit_sequence(x)                                       # party pops out (up for Tube11, else down)
                + [save_exit_tail]
                + [field.Return()]
            )

        ld_bit = _FC_LOCKS["Ld"]["bit"]
        for a, b in tube_pairs:
            if 12 in (a, b):
                x = a if b == 12 else b
                repoint(*event_tile(x), x_to_save(x), f"FC maze: Tube{x}->Save Room")
                repoint(*event_tile(12), save_to_x(x), f"FC maze: Save Room->Tube{x}")
            elif 9 in (a, b):
                partner = a if b == 9 else b
                # Tube9's own tile is only reachable once revealed -> standard trip
                repoint(*event_tile(9), tube_transition(9, partner), "FC maze: Tube9->partner")
                # the partner gates travel toward the (possibly hidden) Tube9
                repoint(*event_tile(partner), gated_transition(partner, ld_bit),
                        f"FC maze: Tube{partner}->Tube9 (gated)")
            else:
                repoint(*event_tile(a), tube_transition(a, b), f"FC maze: Tube{a}->Tube{b}")
                repoint(*event_tile(b), tube_transition(b, a), f"FC maze: Tube{b}->Tube{a}")

        # ---- button -> lock wiring ------------------------------------------
        # Wall / reveal animations per lock (reuse vanilla subroutines by addr).
        # Lock La's first vanilla sub bundles the FCa button press, so its first
        # frame is rebuilt here (wall tiles only) before reusing the rest.
        lock_open = {
            "La": [
                field.PlaySoundEffect(25),
                field.SetMapTiles(2, 38, 31, 6, 3, [
                    0x61, 0x85, 0x00, 0x14, 0x61, 0xAF,
                    0x14, 0x30, 0x2B, 0x14, 0x66, 0x3B,
                    0x84, 0x4A, 0x4B, 0xE4, 0xE5, 0xE1]),
                field.Pause(0.25),
                field.Call(0xadbec),
                field.Pause(0.25),
                field.PlaySoundEffect(25),
                field.Call(0xadc05),
            ],
            "Lb": [
                field.PlaySoundEffect(25),
                field.Call(0xadc66),
            ],
            "Lc": [
                field.PlaySoundEffect(25),
                field.Call(0xadc26),
                field.Pause(0.25),
                field.PlaySoundEffect(25),
                field.Call(0xadc42),
            ],
            "Ld": [  # reveal Tube9
                field.PlaySoundEffect(25),
                field.Call(0xadcc8),
                field.PauseUnits(10),
                field.Call(0xadcde),
                field.PauseUnits(10),
                field.PlaySoundEffect(25),
                field.Call(0xadcf4),
                field.PauseUnits(10),
                field.Call(0xadd04),
            ],
        }

        for btn, lock in assignment.items():
            b = _FC_BUTTONS[btn]; L = _FC_LOCKS[lock]
            bx, by = b["xy"]; cx, cy = L["cam"]
            dx, dy = cx - bx, cy - by
            src = [
                field.BranchIfEventBitSet(L["bit"], "ALREADY_OPEN"),
                field.SetEventBit(L["bit"]),
                field.PlaySoundEffect(44),                            # button click
                field.SetMapTiles(b["layer"], bx, by, 1, 1, [0xA2]),  # pressed graphic
            ]
            if dx or dy:
                src += [
                    field.HoldScreen(),
                    field.EntityAct(field_entity.CAMERA, True,
                                    field_entity.SetSpeed(field_entity.Speed.FAST),
                                    *pan_path(dx, dy)),
                ]
                src += lock_open[lock]
                src += [
                    field.EntityAct(field_entity.CAMERA, True, *pan_path(-dx, -dy)),
                    field.FreeScreen(),
                ]
            else:
                src += lock_open[lock]
            src += ["ALREADY_OPEN", field.Return()]
            repoint(0x18a, b["xy"], src, f"FC maze: button {btn} -> {lock}")

    def map_shuffle_mod(self):
        # Modify entrance event to split between Boss #1 and Boss #2
        src_after_boss1 = [
            field.EntityAct(field_entity.PARTY0, True,
                            field_entity.SetSpriteLayer(2),
                            field_entity.AnimateSurprised(),
                            field_entity.DisableWalkingAnimation(),
                            field_entity.SetSpeed(field_entity.Speed.NORMAL),
                            field_entity.AnimateHighJump(),
                            field_entity.Move(direction=direction.DOWN, distance=2),
                            field_entity.SetSpeed(field_entity.Speed.FAST),
                            field_entity.Move(direction=direction.DOWN, distance=8),
                            field_entity.SetSpriteLayer(0)
                            ),
            field.ClearEventBit(event_bit.TEMP_SONG_OVERRIDE),
            field.SetEventBit(event_bit.FLOATING_CONTINENT_WARP_OPTION),
            field.Call(field.HEAL_PARTY_HP_MP_STATUS),
        ] + GoToSwitchyard(self.entry_id, map='field')
        space = Write(Bank.CA, src_after_boss1, "Map Shuffle Split after FC boss 1")
        self.boss_1_split_addr = space.start_address

        space = Reserve(0xa5a27, 0xa5a35, "Animation fall off airship after ultros/chupon", field.NOP())
        space.write(field.Branch(self.boss_1_split_addr))

        # Write switchyard tile.  The event needs to be a straight LoadMap call.
        # We will write one on the assumption that it is overwritten correctly.
        # src = [field.Branch(ENTRY_EVENT_CODE_ADDR)]
        src = [
            field.LoadMap(0x18a, x=4, y=12, direction=direction.DOWN,
                          default_music=True, fade_in=True, entrance_event=True),  # Failsafe
            field.Return()
        ]
        AddSwitchyardEvent(self.entry_id, self.maps, src=src)

        # Write the Floating Continent entry code:
        # Get the connecting exit
        self.parent_map = [0x000, 117, 162]
        if self.exit_id in self.maps.door_map.keys():
            if self.maps.door_map[1557] != 1556:  # Hack, don't update if connection is vanilla
                self.parent_map = self.maps.get_connection_location(self.exit_id)
        # Force update the parent map here
        #src_addl = [field.SetParentMap(self.parent_map[0], direction.DOWN, self.parent_map[1], self.parent_map[2] - 1)]
        src_addl = []
        if self.parent_map[0] == 1:
            # Update world
            src_addl += [field.ClearEventBit(event_bit.IN_WOR)]

        self.need_shadow_dialog = 0x0873
        self.dialogs.set_text(self.need_shadow_dialog, "Gotta wait for SHADOW...<end>")

        self.go_to_FC_dialog = 0x0851  # use "Kefka, Gestahl, and the Statues..."
        self.dialogs.set_text(self.go_to_FC_dialog,
                              "Land on the Floating Continent?<line><choice> Yes<line><choice> No<end>")

        self.enter_fc_address = self.air_force_battle_addr + 29
        # 0xa5a42 is modified earlier to:
        # field.Call(self.enter_floating_continent_function),
        # field.Call(self.delete_lights_function), # delete lights so airship shows up
        # We need to replicate this & the character animation to avoid fading up the screen again.
        # 0xa5a42 + 4 (Call takes 4 bits)
        self.something_curious_dialog = 0x0850

        # First, don't allow repeating the FC.  Show the "On That Day..." event instead & return to map.
        src = [
            field.BranchIfEventBitClear(event_bit.FINISHED_FLOATING_CONTINENT, "FC_OK"),   # No repeat FC
            field.LoadMap(0x003, x=8, y=16, direction=direction.DOWN, default_music=True, fade_in=False, entrance_event=True),
            field.FadeOutSong(0x1d),
            field.Dialog(0x0877, wait_for_input=False, inside_text_box=False, top_of_screen=False),  # On that day...
            field.Pause(seconds=2),
            field.FadeInScreen(speed=0x08),
            field.Pause(seconds=4),
            field.FadeOutScreen(speed=0x10),
            field.WaitForFade(),
            field.FadeSongVolume(fade_time=0x1d, volume=0xC0), # [0xf3, 0x1d],    # fade in previous song
        ] + GoToSwitchyard(self.exit_id, map='field') + [
            "FC_OK",
            field.LoadMap(0x18a, x=4, y=8, direction=direction.DOWN,
                          default_music=True, fade_in=False, entrance_event=True),  # Read(0xa041c, 0xa0421)
        ]
        src += src_addl  # add parent map update, world bit update if necessary.
        # Write the entrance animation & logic
        src += [
            field.HideEntity(field_entity.PARTY0),
            field.EntityAct(field_entity.PARTY0, False,
                            field_entity.SetPosition(x=0, y=0)),
            field.FadeInScreen(),
            field.WaitForFade(),
        ]
        if self.args.character_gating:
            src += [
                field.BranchIfEventBitSet(event_bit.character_recruited(self.events["Floating Continent"].character_gate()),
                                            "HAVE_SHADOW"),
                field.Dialog(self.need_shadow_dialog, wait_for_input=True),
                field.Branch("LEAVE_FC"),
                "HAVE_SHADOW",
            ]
        # Disable y-party switching as soon as the player commits to landing.  GO_TO_FC
        # is the common point for both landing cases (fighting boss #2 and, on a return
        # visit, skipping it via SKIP_FC_BOSS2), so a single call covers both.
        if self.args.ruination_mode:
            from event.ruination import DISABLE_Y_PARTY_SWITCH
            disable_y_switch = [field.Call(DISABLE_Y_PARTY_SWITCH)]
        else:
            disable_y_switch = []
        src += [
            field.DialogBranch(self.go_to_FC_dialog, "GO_TO_FC", "LEAVE_FC"),
            "GO_TO_FC",
        ] + disable_y_switch + [
            # If already defeated Boss #2, just go to FC
            field.BranchIfEventBitSet(event_bit.DEFEATED_AIR_FORCE, "SKIP_FC_BOSS2"),  # custom event bit
            field.Dialog(self.something_curious_dialog, wait_for_input=True),
            field.Branch(self.air_force_battle_addr),
            "SKIP_FC_BOSS2",
            field.HoldScreen(),
            field.Call(self.delete_lights_function),  # Need to rewrite this to avoid blinking
            field.ShowEntity(field_entity.PARTY0),
            field.EntityAct(field_entity.PARTY0, False,
                            field_entity.SetPosition(x=4, y=0),
                            field_entity.AnimateFrontHandsUp(),
                            field_entity.DisableWalkingAnimation(),
                            field_entity.SetSpeed(field_entity.Speed.FAST),
                            field_entity.Move(direction=direction.DOWN, distance=8),
                            field_entity.Move(direction=direction.DOWN, distance=4),
                            field_entity.AnimateKneeling()
                            ),
            field.Branch(self.enter_fc_address),
            "LEAVE_FC",
            field.HoldScreen(),
            field.ShowEntity(field_entity.PARTY0),
            field.PlaySoundEffect(186),  # falling
            field.EntityAct(field_entity.PARTY0, False,
                            field_entity.SetSpeed(field_entity.Speed.FAST),
                            field_entity.DisableWalkingAnimation(),
                            field_entity.AnimateFrontHandsUp(),
                            field_entity.Move(direction=direction.DOWN, distance=8),
                            field_entity.SetSpeed(field_entity.Speed.FASTEST),
                            field_entity.Move(direction=direction.DOWN, distance=8),
                            field_entity.SetSpeed(field_entity.Speed.NORMAL)
                            ),
            field.EntityAct(field_entity.CAMERA, False,
                           field_entity.SetSpeed(field_entity.Speed.NORMAL),
                           field_entity.Move(direction=direction.DOWN, distance=4),
                           ),
            field.WaitForEntityAct(field_entity.CAMERA),
            field.WaitForEntityAct(field_entity.PARTY0),
            #field.HideEntity(field_entity.PARTY0),
            field.FreeScreen(),
        ] + GoToSwitchyard(self.exit_id, map='field')
        # We need a fixed location to put this.  Bit length ~ 60 bits?
        # look at 0xa48e3 (end of escape sequence)
        space = Reserve(ENTRY_EVENT_CODE_ADDR, ENTRY_EVENT_CODE_ADDR + 153, "Floating Continent entry code modified")
        space.write(src)
        #print('FC entrance event length: ', space.end_address - space.start_address)

        # Write switchyard to handle return
        # (2b) Add the switchyard tile that handles exit to the Falcon
        # Note we will have to receive the reward before returning!  in escape_mod().
        src = [
            field.LoadMap(0x006, direction.DOWN, default_music = True, x = 16, y = 6, fade_in=True, entrance_event=True),
            field.Return()
        ]
        AddSwitchyardEvent(self.exit_id, self.maps, src=src)

        # (2c) Need to set DEFEATED_AIR_FORCE after first entry.
        # handled in airship_battle_mod().

        # (3) Update post-IAF entry: use switchyard.
        # CA/5986: B2    Call subroutine $CA5ABE (jump off airship animation)
        # CA/598A: B2    Call subroutine $CA5A42 (land on FC, right after boss #2: 0xa5a3b).
        iaf_skip_src = [
            field.FreeScreen(),
            field.SetEventBit(event_bit.FLOATING_CONTINENT_WARP_OPTION),
        ] + GoToSwitchyard(self.entry_id, map='field')
        space_iaf_skip = Write(Bank.CA, iaf_skip_src, 'IAF skip mod')
        space = Reserve(0xa598a, 0xa598d, "Call load FC after boss 2 mod")
        space.write(field.Call(space_iaf_skip.start_address))

        # (4) Update airship return before atma wpn
        # CA/5A96: 6B    Load map $0006 (Blackjack, upper deck (general use / "The world is groaning in pain")) instantly, (upper bits $0400), place party at (16, 6), facing up
        # This includes the animation.
        if self.exit_id in self.maps.door_map and self.maps.door_map[self.exit_id] == self.entry_id:
            # Keep the animation if returning to the airship
            pass
        else:
            # Use the switchyard exit.  In ruination, restore y-party switching
            # first: this "do you wish to return?" airship-return tile otherwise
            # leaves the floating continent with y-switching still disabled.
            return_src = []
            if self.args.ruination_mode:
                from event.ruination import RESTORE_Y_PARTY_SWITCH
                return_src += [field.Call(RESTORE_Y_PARTY_SWITCH)]
            return_src += GoToSwitchyard(self.exit_id, map='field')
            return_block = Write(Bank.CA, return_src, "FC airship return restore y-switch")
            space = Reserve(0xa5a96, 0xa5a9c, "return to airship mid FC edit")
            space.write(field.Branch(return_block.start_address))

        # (5) Modify warp behavior
        # We will add a new event bit to track special warp to Blackjack
        # Restore y-party switching when leaving the floating continent via the early
        # path (warping back to the airship before completing the event).
        src_warp = []
        if self.args.ruination_mode:
            from event.ruination import RESTORE_Y_PARTY_SWITCH
            src_warp += [field.Call(RESTORE_Y_PARTY_SWITCH)]
        src_warp += [
            field.ClearEventBit(event_bit.FLOATING_CONTINENT_WARP_OPTION),
            field.ClearEventBit(event_bit.IN_WOR),
            field.LoadMap(map_id=0x006, x=16, y=6, direction=direction.LEFT,
                          default_music=True, fade_in=True, entrance_event=True),
            field.Return()
        ]
        space = Write(Bank.CC, src_warp, "New FC warp code")
        fc_warp_addr = space.start_address
        self.warps.add_warp(event_bit.FLOATING_CONTINENT_WARP_OPTION, fc_warp_addr)


    @staticmethod
    def entrance_door_patch():
        # self-contained code to be called in door rando after entering Floating Continent (1557)
        # to be used in event_exit_info.entrance_door_patch()
        return [field.Branch(ENTRY_EVENT_CODE_ADDR)]

    @staticmethod
    def return_door_patch():
        # self-contained code to be called in door rando upon returning to airship (1556)
        # to be used in event_exit_info.entrance_door_patch()
        src = [
            field.LoadMap(0x006, x=16, y=6, direction=direction.DOWN, default_music=True, fade_in=False, entrance_event=True),
            field.ClearEventBit(event_bit.FLOATING_CONTINENT_WARP_OPTION),
            field.ShowEntity(field_entity.PARTY0),
            field.HoldScreen(),
            field.Branch(0xa5a9d),  # complete animation
        ]
        return src