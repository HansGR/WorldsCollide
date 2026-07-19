from memory.space import Bank, Allocate
from event.event_reward import CHARACTER_ESPER_ONLY_REWARDS, RewardType, choose_reward, weighted_reward_choice
from event.free_heals import modify_inn_costs, modify_free_bed_heals, modify_recovery_springs, remove_coliseum_heal, modify_vector_inn
import instruction.field as field
from data.map_exit_extra import exit_data, door_to_eventname
from data.warps import Warps, WarpPoints
from event.ruination import *
from log.verbose import vprint

class Events():
    def __init__(self, rom, args, data):
        self.rom = rom
        self.args = args
        # Verbose diagnostics: enabled by -debug (stdout) or -debug-verbose
        # (temp file appended to spoiler log).
        self.verbose = bool(getattr(args, "debug", False) or getattr(args, "debug_verbose", False))

        self.dialogs = data.dialogs
        self.characters = data.characters
        self.items = data.items
        self.maps = data.maps
        self.enemies = data.enemies
        self.espers = data.espers
        self.shops = data.shops
        self.warps = Warps()
        if self.args.ruination_mode:
            self.warp_points = WarpPoints()

        events = self.mod()

        self.validate(events)


    def mod(self):
        # generate list of events from files
        import os, importlib, inspect
        from event.event import Event
        events = []
        name_event = {}
        for event_file in sorted(os.listdir(os.path.dirname(__file__))):
            if event_file[-3:] != '.py' or event_file == 'events.py' or event_file == 'event.py':
                continue

            module_name = event_file[:-3]
            event_module = importlib.import_module('event.' + module_name)

            for event_name, event_class in inspect.getmembers(event_module, inspect.isclass):
                if event_name.lower() != module_name.replace('_', '').lower():
                    continue
                event = event_class(name_event, self.rom, self.args, self.dialogs, self.characters, self.items, self.maps, self.enemies, self.espers, self.shops, self.warps)
                events.append(event)
                name_event[event.name()] = event

        # Extra gating from map shuffle
        extra_gating = {}
        if self.args.map_shuffle:
            ac_id = 1558
            if ac_id in self.maps.door_map.keys():
                conn_id = exit_data[self.maps.door_map[ac_id]][0]
                if conn_id in door_to_eventname.keys():
                    location_list = door_to_eventname[conn_id]
                    for loc in location_list:
                        extra_gating[loc] = self.characters.EDGAR
            if self.verbose:
                vprint('Added extra gating logic:', extra_gating)

        if self.args.ruination_mode:
            self.warp_points.mod(self.dialogs, self.maps)
            # Share warp out animation code
            self.warps.warp_out_animation_addr = self.warp_points.warp_out_animation_addr

        # select event rewards
        if self.args.ruination_mode:
            self.ruination_mod(events, name_event)
        elif self.args.character_gating:
            self.character_gating_mod(events, name_event, extra_gating)
        else:
            self.open_world_mod(events)

        # Create party interaction scripts before event mod loop so addresses
        # are available for ChangeNPCEventAddress in individual event mods.
        if self.args.ruination_mode:
            create_party_interaction_scripts(self.dialogs)
            # Shared y-party-switch save/disable and restore subroutines, Call'd by
            # the several events that must suppress party switching mid-scene.
            create_y_party_switch_subroutines()

        # Apply -nfh (no free heals) modifications.
        if self.args.no_free_heals:
            self.no_free_heals_mod()

        # initialize event bits, mod events, log rewards
        log_strings = []
        # Ruination mode adds extra init_event_bits writes (e.g. burning house
        # fireball NPC visibility bits), so reserve a bit more room.
        init_bits_size = 450 if self.args.ruination_mode else 400
        space = Allocate(Bank.CC, init_bits_size, "event/npc bit initialization", field.NOP())
        for event in events:
            event.init_event_bits(space)
            ran = self._instrument_hooks(event)
            event.mod()
            self._dispatch_hooks(event, ran)

            if self.args.spoiler_log and (event.rewards_log or event.changes_log):
                log_strings.append(event.log_string())
        space.write(field.Return())

        if self.args.spoiler_log:
            from log import section
            section("Events", log_strings, [])

        # Write modified warps
        self.warps.mod()

        return events

    # Lifecycle hooks (plan section 3.7 item 2). Documented order:
    # mod() (vanilla + generic), then door_rando_mod() when the event's doors
    # are rewired, then the mode hook (dungeon_crawl_mod / ruination_mod)
    # when the mode is active. Events may still invoke a hook inline where
    # the variant code is genuinely interleaved mid-sequence (space
    # allocation order, attributes consumed later in mod()); the dispatcher
    # detects that and only fires hooks mod() did NOT run itself, so
    # defining a hook and forgetting to wire it is no longer possible.
    _HOOK_NAMES = ('door_rando_mod', 'dungeon_crawl_mod', 'ruination_mod')

    def _instrument_hooks(self, event):
        """Wrap the event's defined hooks so inline invocations from mod()
        are recorded; returns the (live) set of hook names that ran."""
        ran = set()
        for name in self._HOOK_NAMES:
            if not hasattr(type(event), name):
                continue
            bound = getattr(event, name)

            def wrapper(*a, _bound=bound, _name=name, **kw):
                ran.add(_name)
                return _bound(*a, **kw)

            setattr(event, name, wrapper)
        return ran

    def _dispatch_hooks(self, event, ran):
        """Fire any defined-but-not-yet-run hook, in documented order."""
        guards = {
            'door_rando_mod': getattr(event, 'DOOR_RANDOMIZE', False),
            'dungeon_crawl_mod': self.args.door_randomize_dungeon_crawl,
            'ruination_mod': self.args.ruination_mode,
        }
        for name in self._HOOK_NAMES:
            if name in ran or not hasattr(type(event), name):
                continue
            if guards[name]:
                getattr(event, name)()

    def init_reward_slots(self, events):
        import random
        reward_slots = []
        for event in events:
            event.init_rewards()
            for reward in event.rewards:
                if reward.id is None:
                    reward_slots.append(reward)

        random.shuffle(reward_slots)
        return reward_slots

    def choose_single_possible_type_rewards(self, reward_slots):
        for slot in reward_slots:
            if slot.single_possible_type():
                slot.id, slot.type = choose_reward(slot.possible_types, self.characters, self.espers, self.items)

    def choose_char_esper_possible_rewards(self, reward_slots):
        for slot in reward_slots:
            if slot.possible_types == (RewardType.CHARACTER | RewardType.ESPER):
                slot.id, slot.type = choose_reward(slot.possible_types, self.characters, self.espers, self.items)

    def choose_item_possible_rewards(self, reward_slots):
        for slot in reward_slots:
            slot.id, slot.type = choose_reward(slot.possible_types, self.characters, self.espers, self.items)

    def character_gating_mod(self, events, name_event, extra_gate={}):
        import random
        reward_slots = self.init_reward_slots(events)

        # for every event with only one reward type possible, assign random rewards
        # note: this includes start, which can get up to 4 characters
        self.choose_single_possible_type_rewards(reward_slots)

        # find characters that were assigned to start
        characters_available = [reward.id for reward in name_event["Start"].rewards]
        #for c in characters_available:
        #    self.characters.character_location[c] = 'Start'

        # find all the rewards that can be a character
        character_slots = []
        for event in events:
            for reward in event.rewards:
                if reward.possible_types & RewardType.CHARACTER:
                    character_slots.append(reward)

        iteration = 0
        slot_iterations = {} # keep track of how many iterations each slot has been available
        while self.characters.get_available_count():

            # build list of which slots are available and how many iterations those slots have already had
            unlocked_slots = []
            unlocked_slot_iterations = []
            for slot in character_slots:
                slot_empty = slot.id is None

                # Extra gating logic from map shuffle:
                extra_gate_flag = True
                if slot.event.name() in extra_gate.keys():
                    if extra_gate[slot.event.name()] not in characters_available:
                        extra_gate_flag = False
                        if self.verbose:
                            vprint('Extra gate flag FALSE!: ', slot.event.name(), self.characters.get_available_count())

                gate_char_available = (slot.event.character_gate() in characters_available or slot.event.character_gate() is None) \
                                      and extra_gate_flag

                enough_chars_available = len(characters_available) >= slot.event.characters_required()
                if slot_empty and gate_char_available and enough_chars_available:
                    if slot in slot_iterations:
                        slot_iterations[slot] += 1
                    else:
                        slot_iterations[slot] = 0
                    unlocked_slots.append(slot)
                    unlocked_slot_iterations.append(slot_iterations[slot])

            # pick slot for the next character weighted by number of iterations each slot has been available
            slot_index = weighted_reward_choice(unlocked_slot_iterations, iteration)
            slot = unlocked_slots[slot_index]
            slot.id = self.characters.get_random_available()
            slot.type = RewardType.CHARACTER
            characters_available.append(slot.id)
            self.characters.set_character_path(slot.id, slot.event.character_gate())
            #self.characters.character_location[slot.id] = slot.event.name()   # store where the character was found for map shuffle
            iteration += 1

        # get all reward slots still available
        reward_slots = [reward for event in events for reward in event.rewards if reward.id is None]
        random.shuffle(reward_slots) # shuffle to prevent picking them in alphabetical order

        # for every event with only char/esper rewards possible, assign random rewards
        self.choose_char_esper_possible_rewards(reward_slots)

        reward_slots = [slot for slot in reward_slots if slot.id is None]

        # assign rest of rewards where item is possible
        self.choose_item_possible_rewards(reward_slots)
        return

    def open_world_mod(self, events):
        import random
        reward_slots = self.init_reward_slots(events)

        # first choose all the rewards that only have a single type possible
        # this way we don't run out of that reward type before getting to the event
        self.choose_single_possible_type_rewards(reward_slots)

        reward_slots = [slot for slot in reward_slots if not slot.single_possible_type()]

        # next choose all the rewards where only character/esper types possible
        # this way we don't run out of characters/espers before getting to these events
        self.choose_char_esper_possible_rewards(reward_slots)

        reward_slots = [slot for slot in reward_slots if slot.id is None]

        # choose the rest of the rewards, items given to events after all characters/events assigned
        self.choose_item_possible_rewards(reward_slots)

    def ruination_mod(self, events, name_event):
        reward_slots = self.init_reward_slots(events)

        # Verbose output for map generation diagnostics is enabled by either
        # -debug (prints to stdout) or -debug-verbose (prints to a temp file
        # that is appended to the spoiler log at the end of the compile).
        ruin_verbose = bool(self.args.debug or getattr(self.args, "debug_verbose", False))

        # The plan was constructed (and the door map applied and
        # postprocessed) in the Data phase -- Doors.mod, one planning site;
        # look it up and bind the live Reward objects. No snapshot/retry
        # machinery exists here -- a failed plan never reaches Events.
        from event.ruination_bind import bind_ruin_plan
        plan = self.maps.doors.plan
        ruin_map = bind_ruin_plan(plan, self.characters, self.espers,
                                  self.items, events, verbose=ruin_verbose)

        # Store area-to-branch mapping so NPC clue scripts can reference it.
        # Use the rooms actually placed in each branch (not ruin_map.AreasUsed),
        # because distribution can tag an area with a branch whose rooms already
        # lived elsewhere — which would produce clues for areas that aren't
        # really on that branch.
        self.args.ruination_areas_used = ruin_map.compute_actual_areas_used()

        # Handle dried meat for Gau: ensure it's available in non-Veldt-gated shops
        # This ensures dried meat is accessible BEFORE Gau is obtained (needed for Veldt recruitment)
        if self.args.shop_dried_meat > 0:
            all_game_chars = set(ruin_map.PARTY) | set(ruin_map.planned_characters)
            if self.args.debug and 'GAU' in all_game_chars:
                print(f'Gau is in game characters, ensuring dried meat in {self.args.shop_dried_meat} non-Veldt-gated shops')
            non_veldt_shops = ruin_map.get_non_veldt_gated_shops(self.characters)
            self.shops.assign_dried_meats_ruination(non_veldt_shops)

        # Enable limited inventory for ruination shops if flag is set.
        # compute_pack_sizes must run here (after dried meat assignment) so that
        # replaced items get the correct pack size for dried meat.
        # Apply to all shops (not just accessible_shops) so any shop reachable
        # via door rando — including ones not tracked in accessible_shops, like
        # the phantom train shop — runs with limited inventory.
        if self.args.shop_limited_inventory:
            self.shops.compute_pack_sizes()
            all_shop_ids = [shop.id for shop in self.shops.shops]  # don't use shops.all_shops, some are inaccessible
            self.shops.enable_limited_shops(all_shop_ids)
            if self.args.debug:
                print(f'Limited inventory enabled for {len(all_shop_ids)} shops')

        # Check state of reward_slots
        if self.args.debug:
            print('REWARD STATE AFTER RUIN MAPPING:')
            for slot in reward_slots:
                print(slot.event.name(), slot.id, slot.type)

        # For safety (?) distribute any remaining rewards
        reward_slots = [slot for slot in reward_slots if slot.id is None]
        self.choose_single_possible_type_rewards(reward_slots)
        reward_slots = [slot for slot in reward_slots if not slot.single_possible_type()]
        self.choose_char_esper_possible_rewards(reward_slots)
        reward_slots = [slot for slot in reward_slots if slot.id is None]
        self.choose_item_possible_rewards(reward_slots)

        if self.args.debug:
            print('REWARD STATE FINAL:')
            for slot in reward_slots:
                print(slot.event.name(), slot.id, slot.type)

        # Generate ruination spoiler log if -sl flag is set
        if self.args.spoiler_log:
            from log import section
            log_lines = ruin_map.generate_spoiler_log(self.characters, self.espers, self.items)
            section("Ruination Rewards", log_lines, [])

        # Disable in-town chocobo stables for ruination mode
        disable_chocobo_stables(self.rom, self.dialogs, self.args)

        # Wire up SF / Nikeah / Albrook ferry network based on which ports are mapped
        # Reuse Kefka @ Narshe boss for the possible sea boss attack
        sea_boss_id = self.enemies.get_event_boss("Kefka (Narshe)")
        fix_ferry_connections(self.rom, self.dialogs, self.maps, ruin_map, self.args, sea_boss_id)

    def no_free_heals_mod(self):
        """Apply -nfh changes that wrap up free-heal removals/restrictions.

        Modifies inn costs (and converts free inns to paid), turns existing
        free bed heals into HP-only heals with an ambush chance, randomises
        recovery spring effects, removes the free full-heal the Coliseum
        applies to the selected fighter, and reworks Vector's free inn (entry
        gate plus scaled thief). Per-event heal removals (Doma WoB Leader,
        Magitek 3 pre-crane, Vector heal hut, Phantom Train restaurant, Narshe
        school pot, Thamasa inn pricing) are gated locally in their respective
        event files via ``args.no_free_heals``.
        """
        # Modify inn costs (includes converting free inns Returners Hideout
        # and Figaro Castle into paid inns).
        modify_inn_costs(self.maps, self.rom, self.dialogs, self.args)

        # Modify existing free bed heals (HP-only heal with 3/8 monster attack chance)
        modify_free_bed_heals(self.maps, self.dialogs, self.enemies, self.args)

        # Modify recovery springs with random effects
        modify_recovery_springs(self.maps, self.rom, self.dialogs, self.args)

        # Remove the free full-heal applied to the selected Coliseum fighter
        remove_coliseum_heal(self.args)

        # Rework Vector's free inn (entry gate + scaled thief)
        modify_vector_inn(self.dialogs, self.args)

    def validate(self, events):
        char_esper_checks = []
        for event in events:
            char_esper_checks += [r for r in event.rewards if r.possible_types == (RewardType.CHARACTER | RewardType.ESPER)]

        assert len(char_esper_checks) == CHARACTER_ESPER_ONLY_REWARDS, f"Number of char/esper only checks changed - Check usages of CHARACTER_ESPER_ONLY_REWARDS and ensure no breaking changes. Expected: {CHARACTER_ESPER_ONLY_REWARDS}, Actual: {len(char_esper_checks)}"
