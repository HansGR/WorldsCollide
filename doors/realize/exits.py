"""connect_exits and the exit-event writers.

The entrance/exit door patches applied here are
unified transition logic: their job is making transitions work with
randomized doors (character gating, where present, is a line inside
them, not a separate mechanism)."""

from log.verbose import vprint
from memory.space import Bank, Free, Reserve, Write
import data.direction as direction
from instruction import field, world
from instruction.event import EVENT_CODE_START
import data.event_bit as event_bit
from data.map_event import MapEvent, LongMapEvent
from data.map_exit_extra import exit_data, exit_make_explicit, \
    map_shuffle_airship_warp, map_shuffle_force_explicit
from data.event_exit_data import event_exit_info, event_return_map
from data.event_exit_patches import entrance_door_patch, exit_door_patch, \
    require_event_bit
from doors.realize.transitions import Transitions
from event.switchyard import SWITCHYARD_MAP, AddSwitchyardEvent, \
    GoToSwitchyard, SummonAirship


def connect_exits(maps):
    # For every door in door_map, find its exit and change where it leads.
    # (The map construction itself lives in postprocess_door_map.)
    door_map = maps.door_map

    # Need to add modified world map exits if they weren't randomized (to print exit events)
    # Skip for ruination mode - exit_data has been modified by dungeon_crawl override
    if maps.args.door_randomize and not maps.args.ruination_mode:
        # Only do this if door_randomize, not map_shuffle
        for m in exit_make_explicit.keys():
            if m not in door_map.keys():
                door_map[m] = exit_data[m][0]

    # Build dictionary of maps with entrance events that will need to be called
    maps.exit_event_data_to_include = {}
    # Must be referenced in:
    # (A) create_exit_event(maps, m, door_map[m])     # for normal doors, m < 1500
    # (B) dt = Transitions(new_map, ...)        # for event tiles acting as doors, 1500 <= m < 4000
    # (C) shared_map_exit_event(maps, m, door_map[m]) # for logical WOR exits

    # In ruination mode, disable the entrance_door_patch for door 1558
    if maps.args.ruination_mode:
        entrance_door_patch.pop(1558, None)

        # Disable require_event_bit for Figaro Castle entrance doors.
        # Rooms 68 (WoB) and 'FIGr01' (WoR) propagate bits to doors 197/1156
        # and 4197/5156 via room_require_event_bit. These are only needed
        # for classic door randomization.
        for door in [197, 1156, 4197, 5156]:
            require_event_bit.pop(door, None)

    # Bundle exit_door_patch and entrance_door_patch data for transitions
    for m in exit_door_patch.keys():
        if m in door_map.keys():
            # Select event tiles acting as doors
            if 1500 <= m < 4000:
                info = exit_door_patch[m]
                # Pass the script data to exit_event_data_to_include
                maps.exit_event_data_to_include[m] = [info, 1]  # always include before transition
                if maps.doors.verbose:
                    vprint('Passed exit door patch for ', str(m), ' --> ', str(door_map[m]))
                    # print([a.__str__() for a in info[0]])

    for m in entrance_door_patch.keys():
        if m in door_map.keys():
            # select connections acting as doors
            if 1500 <= door_map[m] < 4000:
                if isinstance(entrance_door_patch[m][0], list):
                    info = entrance_door_patch[m]
                else:
                    info = [entrance_door_patch[m][0](maps.args), entrance_door_patch[m][1]]
                # Pass the script data to exit_event_data_to_include
                maps.exit_event_data_to_include[door_map[m]] = info
                if maps.doors.verbose:
                    vprint('Passed entrance door patch for ', str(door_map[m]), ' --> ', str(m))
                    # print([a.__str__() for a in info[0]])

    # Generate a final list of all exits that need to be connected
    all_exits = list(door_map.keys())
    all_exits.sort()  # apply the doors in order.
    # if maps.doors.verbose:
    # print(all_exits)

    # Connect real doors:  m < 1500
    door_exits = [m for m in all_exits if m < 1500]
    for m in door_exits:
        if maps.doors.verbose:
            vprint('Connecting: ' + str(m) + ' to ' + str(door_map[m]))
            #  + ": " + str(exit_data[m][1]) + ' to ' + str(exit_data[door_map[m]][1])

        # Get exits associated with doors m and m_conn
        exitA = maps.get_exit(m)

        # Attach exits:
        # Copy original properties of exitB_pair to exitA & vice versa.
        exitB_pairID = exit_data[door_map[m]][0]  # Original connecting exit to B...
        if exitB_pairID not in maps.exits.exit_original_data.keys():
            if 1500 <= exitB_pairID < 4000:
                # Event exit behaving as a door.
                pass
            elif exitB_pairID >= 4000:
                # Logical WOR exit hasn't been updated in exit_original_data.  Just use basic door ID.
                exitB_pairID = exitB_pairID - 4000

        maps.exits.copy_exit_info(exitA, exitB_pairID)  # ... copied to exit A

        # For a very few exits, must force explicit
        if m in map_shuffle_force_explicit:
            #if maps.doors.verbose:
            #    print('Checking if ', m, 'must be forced explicit...', hex(exitA.dest_map))
            if exitA.dest_map == 0x1ff:
                exitA.dest_map = maps.exits.exit_original_data[door_map[m]][-1]  #exit_world[exitB_pairID]
                if maps.doors.verbose:
                    vprint('Updated destination door_map for ', m,': 0x1ff --> ', hex(exitA.dest_map) )

        # Write events on the exits to handle required conditions:
        create_exit_event(maps, m, door_map[m])

    # Connect event tiles that are acting as doors: 1500 <= m < 4000.  Treat them as transitions.
    transition_map = []
    transition_exits = [m for m in all_exits if 1500 <= m < 4000]
    for m in transition_exits:
        # We want to accumulate them first, then write them all together to avoid conflicts.
        if maps.doors.verbose:
            vprint('Connecting: ' + str(m) + ' to ' + str(door_map[m]))
        transition_map.append([m, door_map[m]])
    dt = Transitions(transition_map, maps.rom, maps.exits.exit_original_data, event_exit_info,
                     maps.exit_event_data_to_include, args=maps.args)
    dt.write(maps=maps)

    # Connect logical WOR exits: 4000 <= m,  m_WOB = (m - 4000).
    wor_exits = [m for m in all_exits if m >= 4000]
    for m in wor_exits:
        # The WOB exit & exit event (if necessary) are handled by the previous door code.
        shared_map_exit_event(maps, m, door_map[m])

def create_exit_event(maps, d, d_ref):
    # Write an event on top of exit d to set the correct properties (world, parent map) for exit d_ref.
    # Logical WOR exits (id >= 4000) are handled by maps.shared_map_exit_event(d, d_ref).
    SOUND_EFFECT = None  # [None, 0x00 = Lore, 0x15 = Bolt3]

    # Collect information about the properties for the exit
    this_exit = maps.get_exit(d)
    map_id = maps.exit_maps[d]
    this_world = maps.exit_world[d]

    # Collect information about the properties of the connecting exit
    that_world = maps.exit_world[d_ref]
    that_map = maps.exit_maps[d_ref]
    if that_map == SWITCHYARD_MAP and d_ref in event_return_map.keys():
        that_map = event_return_map[d_ref]  # verify the switchyard tile leads to the world map

    is_map_already_loaded = False

    # Check to make sure an exit event is required:
    # (1) the connection is in the other world
    # (2) the connection requires special code (in entrance_door_patch) or event bits (in require_event_bit)
    # (3) the door requires special code (in exit_door_patch[d])
    # (4) the connection has an event script that should be run upon entry (in exit_event_data_to_include)
    # (5) the connection is a world map.  Move the airship to the player's location on the worldmap.
    require_event_flags = [
        (this_world != that_world),
        d_ref in entrance_door_patch.keys() or d_ref in require_event_bit.keys(),
        d in exit_door_patch.keys(),
        d in maps.exit_event_data_to_include.keys(),
        that_map in [0x000, 0x001]
    ]
    if maps.args.map_shuffle and not maps.args.door_randomize:
        # Don't summon the airship by default
        if d not in map_shuffle_airship_warp:
            require_event_flags[4] = False

    # In ruination mode, never warp the airship to the player's location
    if maps.args.ruination_mode:
        require_event_flags[4] = False

    if require_event_flags.count(True) > 0:
        # Need to use different commands for world maps vs field maps.
        # Look for an existing event on this exit tile
        try:
            if maps.doors.verbose:
                vprint('looking for event at: ', hex(map_id), this_exit.x, this_exit.y, '(type ', maps.exits.exit_type[d], ')')
            existing_event = maps.get_event(map_id, this_exit.x, this_exit.y)
            # An event already exists.  It will need to be modified.

            # Add Call to existing event code
            src = [field.Call(existing_event.event_address + EVENT_CODE_START), field.Return()]

            if maps.doors.verbose:
                vprint('WARNING: found an existing event: ', str(hex(map_id)), ' (', str(this_exit.x), ', ',
                      str(this_exit.y),
                      '): ')
                vprint('\t(', str(existing_event.x), ', ', str(existing_event.y), '):  ',
                      str(hex(existing_event.event_address)))

            # delete existing event
            maps.delete_event(map_id, this_exit.x, this_exit.y)
            # existing_event_length = len(src) - 1

        except IndexError:
            # event does not exist.  Make a new one.
            src = [field.Return()]
            # existing_event_length = False

        this_address = 0x05eb3  # Default address to fail gracefully: event at $CA/5EB3 is just 0xfe (return)

        # If it's a new event that is just forcing the world, just directly call the "force world" event:
        e_length = len(src)
        if e_length == 1 and not require_event_flags[1:].count(True) > 0 and map_id > 2:
            if that_world == 0:
                this_address = maps.GO_WOB_EVENT_ADDR - EVENT_CODE_START
            elif that_world == 1:
                this_address = maps.GO_WOR_EVENT_ADDR - EVENT_CODE_START

            if maps.doors.verbose:
                vprint('Writing exit event:', d, '(pair =', d_ref, ') @ ', hex(this_address))
                vprint('\tReason: ', require_event_flags)

        else:
            #  (5) <code required when leaving room>
            #  (4) <code required when entering connection>
            #  (3) <required world-bit setting when entering WOB connection>
            #  (2) <call any required entrance script>
            #  (1) If going to the world map, summon the airship as well.
            #  (0) Return();  # Connection is handled by the door.

            # (1) If going to world map, also summon the airship
            if require_event_flags[4]:
                # Note, in this case we don't need the terminal field.Return(), but it doesn't hurt and makes this
                # more robust to errors.
                # Get [x,y] location of the destination for the exit.
                d_ref_pairID = exit_data[d_ref][0]  # Original connecting exit to d_ref..
                if d_ref_pairID in maps.exits.exit_original_data.keys():
                    conn_data = maps.exits.exit_original_data[d_ref_pairID]  # [dest_map, dest_x, dest_y, ...]
                elif d_ref_pairID >= 4000:  # Do we actually need this?
                    # Logical WOR exit hasn't been updated in exit_original_data.  Just use basic door ID.
                    conn_data = maps.exits.exit_original_data[d_ref_pairID - 4000]
                src = SummonAirship(that_world, conn_data[1], conn_data[2]) + src

            # (2) Add call to entrance script, if any
            if require_event_flags[3]:
                # Entrance event scripts are handled by entrance_door_patch; nothing should reach here.
                print("WARNING: THIS SHOULD NOT OCCUR.  Check entrance_door_patch!", d, d_ref)

            # (3) Prepend call to force world bit event, if required
            if require_event_flags[0]:
                if that_world == 0:
                    src = [field.ClearEventBit(event_bit.IN_WOR)] + src
                elif that_world == 1:
                    src = [field.SetEventBit(event_bit.IN_WOR)] + src

            # (4) Prepend any data required by the connection
            if require_event_flags[1]:
                if d_ref in entrance_door_patch.keys():
                    # Check whether this is BEFORE (True) or AFTER (False) loading the map.
                    if entrance_door_patch[d_ref][1]:
                        load_map_src = []
                    else:
                        # Generate map load code for this door; the door itself will not be used.
                        load_map_src = _get_load_map_code(maps, d_ref)
                        is_map_already_loaded = True

                    if isinstance(entrance_door_patch[d_ref][0], list):
                        edp = entrance_door_patch[d_ref][0]
                    else:
                        # patch requires knowledge of arguments
                        edp = entrance_door_patch[d_ref][0](maps.args)
                    src = src[:-1] + load_map_src + edp + src[-1:]

                if d_ref in require_event_bit.keys():
                    entr_bits = require_event_bit[d_ref]
                    for k in entr_bits:
                        if entr_bits[k]:
                            src = [field.SetEventBit(k)] + src
                        else:
                            src = [field.ClearEventBit(k)] + src

            # (5) Prepend any data required by the door
            if require_event_flags[2]:
                src = exit_door_patch[d] + src

            if map_id <= 2:
                # This event is on the world map, where the event -> exit passthru trick doesn't work
                # Solution: send the player to a dummy map, directly onto an event tile that does the necessary
                # modifications and then sends them on to the destination.  A switchyard, if you will.
                # dummy_map = 0x005   # mog's black map, 128 x 128
                # dummy_x = d % 128   # unique ID in [x,y]
                # dummy_y = d // 128
                # [dummy_x, dummy_y] = switchyard_xy(d)

                # (a) add a SetParentMap and LoadMap command for the destination; write it to a dummy event
                d_pairID = exit_data[d][0]  # Original connecting exit to d
                if d_pairID in maps.exits.exit_original_data.keys():
                    conn_data = maps.exits.exit_original_data[d_pairID]  # [dest_map, dest_x, dest_y, ...]
                elif d_pairID >= 4000:  # Do we actually need this?
                    # Logical WOR exit hasn't been updated in exit_original_data.  Just use basic door ID.
                    conn_data = maps.exits.exit_original_data[d_pairID - 4000]
                pm_dir = conn_data[6]
                pm_x = conn_data[1] + direction.xy_shift_parent_map(pm_dir)[0]
                pm_y = conn_data[2] + direction.xy_shift_parent_map(pm_dir)[1]
                update_parent_map_src = [
                    field.SetParentMap(map_id=map_id, x=pm_x, y=pm_y, direction=pm_dir),
                ]
                if is_map_already_loaded:
                    load_destination_src = []
                else:
                    load_destination_src = [
                        field.LoadMap(this_exit.dest_map, direction=this_exit.facing, default_music=True,
                                      x=this_exit.dest_x, y=this_exit.dest_y, fade_in=True, entrance_event=True)
                    ]

                src_dummy = update_parent_map_src + src[:-1] + load_destination_src + src[-1:]
                if maps.doors.verbose:
                    vprint('source code at switchyard: ', [a.__str__() for a in src_dummy])
                AddSwitchyardEvent(d, maps, src=src_dummy)
                # space = Write(Bank.CC, src_dummy, "Door Dummy Event " + str(d))
                # dummy_address = space.start_address - EVENT_CODE_START
                # (b) make a new event tile on the dummy map
                # dummy_event = MapEvent()
                # dummy_event.x = dummy_x
                # dummy_event.y = dummy_y
                # dummy_event.event_address = dummy_address
                # maps.add_event(dummy_map, dummy_event)

                # (c) make a new src that loads the dummy map and places the character on the dummy tile.
                if map_id > 0x002:
                    maptype = 'field'
                else:
                    maptype = 'world'
                src = GoToSwitchyard(d, map=maptype)
                # src = [world.LoadMap(dummy_map, direction=direction.UP, default_music=False,
                #                     x=dummy_x, y=dummy_y,
                #                     fade_in=False, entrance_event=False), field.Return()]

            if SOUND_EFFECT is not None:
                # Note this kills the direct "force world" event.
                src = [field.PlaySoundEffect(SOUND_EFFECT)] + src

            # Write data to a new event & add it
            space = Write(Bank.CC, src, "Door Event " + str(d))
            this_address = space.start_address - EVENT_CODE_START

            if maps.doors.verbose:
                vprint('Writing exit event:', d, '(pair =', d_ref, ') @ ', hex(this_address))
                vprint('\tReason: ', require_event_flags)
                vprint([str(s) for s in src])

        # Write the new event on the exit
        if maps.exits.exit_type[d] == 'short':
            # Write the event on the short exit tile
            new_event = MapEvent()
            new_event.x = this_exit.x
            new_event.y = this_exit.y
            new_event.event_address = this_address
            maps.add_event(map_id, new_event)
        elif maps.exits.exit_type[d] == 'long':
            # Write the long event on the long exit tile
            new_event = LongMapEvent()
            new_event.x = this_exit.x
            new_event.y = this_exit.y
            new_event.direction = this_exit.direction
            new_event.size = this_exit.size
            new_event.event_address = this_address
            maps.add_long_event(map_id, new_event)

        if map_id <= 2:
            # This event is on the world map, where the event -> exit passthru trick doesn't work.
            # (a) eventually, just delete the exit. but for now:
            # (b) move the exit it is replacing to somewhere else ('dummy' it)
            this_exit.x = d
            this_exit.y = 0
            # DO WE NEED to move the exit, though?  Does it matter?
            # I forget - on the world map, does the exit take effect before the event?  Is that why we did this?

def shared_map_exit_event(maps, d, d_ref):
    SOUND_EFFECT = None  # [None, 0x00 = Lore, 0x15 = Bolt3]
    # THIS IS A SHARED ROOM (i.e. the exit d is one of a (WOB, WOR) pair: (d-4000, d).
    # SINCE THE WOB CONNECTION IS ALWAYS DONE FIRST, WHEN THE WOR CONNECTION IS WRITTEN WE CAN DO:
    #   if IS_WOR:
    #       <code required when leaving WOR room>
    #       <code required when entering WOR connection>
    #       <required world-bit setting when entering WOR connection>
    #       <Call (or Branch to?) entrance_script code, if any>
    #       <Load Map call for WOR connection>
    #   else:
    #       BranchTo(existing_event_code)
    # IN FF6 EVENT CODE, THIS IS:
    #   src = [field.BranchIfEventBitSet(IN_WOR, <address for WOR stuff>),
    #          field.Branch(<address for WOB stuff>),
    #          field.Return()]
    # So we should:
    #   (1) Find the address for WOB script
    #   (2) Write a script for the WOR branch
    #   (3) Write a script that chooses between them based on IN_WOR
    #   (4) make an event tile for the final script in (3)

    # Collect information about the properties for the exit
    this_exit = maps.get_exit(d - 4000)
    map_id = maps.exit_maps[d - 4000]
    this_world = maps.exit_world[d]  # note: virtual exits should always be WoR

    # Collect information about the properties of the connecting exit
    that_world = maps.exit_world[d_ref]
    that_map = maps.exit_maps[d_ref]
    if that_map == SWITCHYARD_MAP and d_ref in event_return_map.keys():
        that_map = event_return_map[d_ref]  # verify the switchyard tile leads to the world map

    # (1) the connection requires a specific world that is not this world
    # (2) the connection requires special code (in entrance_door_patch) or event bits (in require_event_bit)
    # (3) the door requires special code (in exit_door_patch[d])
    # (4) the door needs to run an entrance event script (in exit_event_data_to_include)
    # (5) the connection is a world map: also summon the airship.
    require_event_flags = [
        ((this_world != that_world)),
        d_ref in entrance_door_patch.keys() or d_ref in require_event_bit.keys(),
        d in exit_door_patch.keys(),
        d in maps.exit_event_data_to_include.keys(),  # SHOULD NOT HAPPEN -- see (0) below
        that_map in [0x0, 0x1]
    ]

    if maps.args.map_shuffle and not maps.args.door_randomize:
        # Don't airship warp if only doing map shuffle
        if d not in map_shuffle_airship_warp:
            require_event_flags[4] = False

    # In ruination mode, never warp the airship to the player's location
    if maps.args.ruination_mode:
        require_event_flags[4] = False

    # if maps.doors.verbose:
    #    print('Writing shared event at ' + str(d) + ' (ref = ' + str(d_ref) + ')')
    # Look for an existing event on this exit tile
    try:
        if maps.doors.verbose:
            vprint('looking for event at: ', hex(map_id), this_exit.x, this_exit.y)
        existing_event = maps.get_event(map_id, this_exit.x, this_exit.y)
        # An event already exists.
        if maps.doors.verbose:
            vprint('shared map: found an existing event at ', map_id, this_exit.x, this_exit.y,
                  hex(existing_event.event_address))

        # Add Call to existing event code
        src = [field.Call(existing_event.event_address + EVENT_CODE_START), field.Return()]

        # delete existing event
        maps.delete_event(map_id, this_exit.x, this_exit.y)

    except IndexError:
        # event does not exist.  Make a new one.
        src = [field.Return()]

    this_address = 0xa5eb3  # Default address to fail gracefully: event at $CA/5EB3 is just 0xfe (return)

    # Send the player to the location that the connection's vanilla partner sends you to
    # [dest_x, dest_y, dest_map, refreshparentmap, enterlowZlevel, displaylocationname, facing, unknown, ...]
    d_ref_partner = exit_data[d_ref][0]
    if d_ref_partner in maps.exits.exit_original_data.keys():
        conn_data = maps.exits.exit_original_data[d_ref_partner]
    else:
        # This is a logical exit without tweaks.  Can use vanilla connection info.
        conn_data = maps.exits.exit_original_data[d_ref_partner - 4000]
    if d in map_shuffle_force_explicit:
        # Update conn_data to not return to parent map
        if conn_data[0] in [0x1ff, 0x1fe]:
            conn_data[0] = maps.exits.exit_original_data[d_ref][-1]

    if require_event_flags[4]:
        wor_src = SummonAirship(that_world, conn_data[1], conn_data[2])
        # print(d, d_ref, d_ref_partner, conn_data)
    else:
        wor_src = [field.FadeLoadMap(conn_data[0], conn_data[6], True, conn_data[1], conn_data[2], fade_in=True,
                                     entrance_event=True)]
        if conn_data[0] in [0, 1, 2, 511]:
            # Include End command when loading world maps.  Parent Map (511) should always be a world map
            wor_src += [world.End()]
        else:
            wor_src += [field.Return()]

    if SOUND_EFFECT is not None:
        wor_src = [field.PlaySoundEffect(SOUND_EFFECT)] + wor_src

    # (0) Entrance event scripts are handled by entrance_door_patch; nothing should reach here.
    if require_event_flags[3]:
        print('WARNING: THIS SHOULD NOT OCCUR.  Check entrance_door_patch! ', d, d_ref)

    # (1) Prepend call to force world bit event, if required
    if require_event_flags[0]:
        if that_world == 0:
            wor_src = [field.ClearEventBit(event_bit.IN_WOR)] + wor_src
        elif that_world == 1:
            wor_src = [field.SetEventBit(event_bit.IN_WOR)] + wor_src

    # (2) Prepend any data required by the connection
    if require_event_flags[1]:
        if d_ref in entrance_door_patch.keys():
            # Check whether this is BEFORE (True) or AFTER (False) loading the map.
            if isinstance(entrance_door_patch[d_ref][0], list):
                edp = entrance_door_patch[d_ref][0]
            else:
                # patch requires knowledge of arguments
                edp = entrance_door_patch[d_ref][0](maps.args)

            world_map_override = (conn_data[0] in [0, 1, 2, 511])
            if entrance_door_patch[d_ref][1] or world_map_override:
                # Put code before map load
                wor_src = edp + wor_src
            else:
                # Put code after map load
                wor_src = wor_src[:-1] + edp + wor_src[-1:]

        if d_ref in require_event_bit.keys():
            entr_bits = require_event_bit[d_ref]
            for k in entr_bits:
                if entr_bits[k]:
                    wor_src = [field.SetEventBit(k)] + wor_src
                else:
                    wor_src = [field.ClearEventBit(k)] + wor_src

    # (3) Prepend any data required by the door
    if require_event_flags[2]:
        wor_src = exit_door_patch[d] + wor_src

    # Write WOR data to a new event script
    if len(wor_src) > 0:
        space = Write(Bank.CC, wor_src, "WOR door Event " + str(d))
        this_address = space.start_address
        if maps.doors.verbose:
            vprint('Writing WOR door event:', d, ' @ ', hex(this_address))
            vprint('\t', [str(s) for s in wor_src])

    src = [field.BranchIfEventBitSet(event_bit.IN_WOR, this_address)] + src

    # Write data to a new event & add it
    space = Write(Bank.CC, src, "Event tile for shared WOB/WOR door " + str(d))
    tile_address = space.start_address - EVENT_CODE_START

    if maps.doors.verbose:
        vprint('Writing exit event:', d, '(pair =', d_ref, ') @ ', hex(tile_address))
        vprint('\tReason: ', require_event_flags)
        vprint([str(s) for s in src])

    # Write the new event on the exit
    if maps.exits.exit_type[d - 4000] == 'short':
        # Write the event on the short exit tile
        new_event = MapEvent()
        new_event.x = this_exit.x
        new_event.y = this_exit.y
        new_event.event_address = tile_address
        maps.add_event(map_id, new_event)
    elif maps.exits.exit_type[d - 4000] == 'long':
        # Write the event on the long exit tile
        new_long_event = LongMapEvent()
        new_long_event.x = this_exit.x
        new_long_event.y = this_exit.y
        new_long_event.size = this_exit.size
        new_long_event.direction = this_exit.direction
        new_long_event.event_address = tile_address
        maps.add_long_event(map_id, new_long_event)

def _get_load_map_code(maps, entr_id):
    # Generate load map code for a given door
    partner_id = exit_data[entr_id][0]  # vanilla partner of door
    partner_data = maps.exits.exit_original_data[partner_id]  # connection data for vanilla partner
    map_id = partner_data[0]  # destination map
    x = partner_data[1]  # destination x
    y = partner_data[2]  # destination y
    direction = partner_data[6]  # facing after transit
    src = [field.LoadMap(map_id=map_id, direction=direction, x=x, y=y,
                         default_music=True, fade_in=True, entrance_event=True)]
    return src

def move_event_trigger_data(maps):
    # Rewrite the ROM bits that look for event trigger data
    new_bank = 0xf1

    # Patch Field Program
    # C0 / BCAE: BF0200C4       LDA $C40002, X
    maps.rom.set_byte(0x0bcb1, new_bank)
    # C0 / BCB4: BF0000C4       LDA $C40000, X
    maps.rom.set_byte(0x0bcb7, new_bank)
    # C0 / BCBD: BF0000C4       LDA $C40000, X
    maps.rom.set_byte(0x0bcc0, new_bank)
    # C0 / BCD3: BF0200C4       LDA $C40002, X
    maps.rom.set_byte(0x0bcd6, new_bank)
    # C0 / BCED: BF0400C4       LDA $C40004, X
    maps.rom.set_byte(0x0bcf0, new_bank)

    # Patch World Program
    # EE / 2176: BF0000C4   LDA $C40000, X
    maps.rom.set_byte(0x2e2179, new_bank)
    # EE / 217C: BF0200C4   LDA $C40002, X
    maps.rom.set_byte(0x2e217f, new_bank)
    # EE / 218B: BF0000C4   LDA $C40000, X
    maps.rom.set_byte(0x2e218e, new_bank)
    # EE / 2193: BF0100C4   LDA $C40001, X
    maps.rom.set_byte(0x2e2196, new_bank)
    # EE / 219B: BF0200C4   LDA $C40002, X
    maps.rom.set_byte(0x2e219e, new_bank)
    # EE / 21A4: BF0300C4   LDA $C40003, X
    maps.rom.set_byte(0x2e21a7, new_bank)
    # EE / 21AC: BF0400C4   LDA $C40004, X
    maps.rom.set_byte(0x2e21af, new_bank)

    # Repoint event pointers & event tile data to the expanded ROM
    new_ref = (new_bank << 16) - 0xC00000
    maps.events.DATA_START_ADDR = new_ref + (maps.events.DATA_START_ADDR - maps.EVENT_PTR_START)
    maps.EVENT_PTR_START = new_ref

    space = Reserve(new_ref, new_ref + 0xffff, "Door Rando map event pointers")
    space = Reserve(0x040000, 0x041A0F, "Original map event pointer data", field.NOP())

    if maps.doors.verbose:
        vprint('Moved Event Trigger data to ' + str(hex(new_bank)) + ': ' + str(
            hex(maps.EVENT_PTR_START)) + ', ' + str(hex(maps.events.DATA_START_ADDR)))
        # for e in range(14):
        #    print('\t' + str(e) + ' (' + str(maps.events.events[e].x) + ', ' + str(maps.events.events[e].y) + '): ' + str(hex(maps.events.events[e].event_address)))

def door_rando_cleanup(maps):
    # Perform cleanup actions, if we are doing door rando

    ### THAMASA WOR (0x158): replace manual long-event tiles with a real long_event
    # We don't need these events: they just check bits 0x196, 0x19E, 0x19F to see if Relm/Shadow story can progress.
    # Let's just delete them and free space (CB/7D69 - CB/7D82)
    THA_WR = 0x158

    # South Exit tiles
    for x in range(20, 26):
        maps.delete_event(THA_WR, x, 48)

    # West Exit tiles
    for y in range(28, 32):
        maps.delete_event(THA_WR, 0, y)

    # Move unused Nikeah exits (54, 55) out of the way
    for e_id in [54, 55]:
        nikeah = maps.get_exit(e_id)
        nikeah.x = e_id
        nikeah.y = 0

    # Move unused Zozo Tower exits (638, 639, 640, 641) out of the way.
    # These duplicate the live exits 634-637 on the same tiles (see rooms.py).
    # They are never referenced by any room, so today they are only safe because
    # they have higher indices than the live exits (the live exit wins the runtime
    # first-match). Relocate them to (0, 0) so they can never shadow a randomized
    # destination if exit ordering ever changes.
    for e_id in [638, 639, 640, 641]:
        zozo_tower = maps.get_exit(e_id)
        zozo_tower.x = 0
        zozo_tower.y = 0

    # Note: This line caused SwdTech to break the game - because I forgot the EVENT_CODE_START offset!
    Free(0x17d69 + EVENT_CODE_START, 0x17d82 + EVENT_CODE_START)


