"""postprocess_door_map: the plan's pair lists -> the realized door_map /
trap_map dictionaries (+4000 logical WOR destination ids, shared-exit
conflict detection)."""

from log.verbose import vprint
from data.map_exit_extra import exit_data, exit_data_patch, \
    map_shuffle_force_explicit, map_shuffle_partner_explicit, \
    event_door_connection_data, dungeon_crawl_exit_destination_override
from data.event_exit_info import event_return_map
from data.rooms import shared_exits
from event.switchyard import SWITCHYARD_MAP


def find_room_for_door(door_id):
    """Room id owning a door element (first match in room_data)."""
    from data.rooms import room_data
    for room_id, room in room_data.items():
        if door_id in room[0]:
            return room_id
    return None


def postprocess_door_map(maps):
    # Postprocess the door map
    if maps.doors.verbose:
        vprint("=== postprocess_door_map() CALLED ===")
        vprint(f"doors.map length: {len(maps.doors.map)}, doors.map[0] length: {len(maps.doors.map[0]) if len(maps.doors.map) > 0 else 'N/A'}")

    maps.door_map = {}
    maps.trap_map = {}
    if len(maps.doors.map) > 0:
        # Add doors to the spoiler log
        maps.doors.print()

        # Create sorted map, so they are connected in order:
        shared_exits_sets = []
        for se in shared_exits.keys():
            shared_exits_sets.append([se] + shared_exits[se])

        for m in maps.doors.map[0]:
            if m[0] not in maps.door_map.keys():
                maps.door_map[m[0]] = m[1]
            else:
                is_shared = len(
                    [ses for ses in shared_exits_sets if maps.door_map[m[0]] in ses and m[1] in ses]) > 0
                if maps.doors.verbose and not is_shared and not (maps.door_map[m[0]] == m[1]):
                    vprint('CONFLICTING EXITS: ', m[0], '-->', maps.door_map[m[0]], ' vs ', m[1])
            if m[1] not in maps.door_map.keys():
                maps.door_map[m[1]] = m[0]
            else:
                is_shared = len(
                    [ses for ses in shared_exits_sets if maps.door_map[m[1]] in ses and m[0] in ses]) > 0
                if maps.doors.verbose and not is_shared and not (maps.door_map[m[1]] == m[0]):
                    vprint('CONFLICTING EXITS: ', m[1], '-->', maps.door_map[m[1]], ' vs ', m[0])

        # Check reciprocity
        for m in maps.door_map.keys():
            m2 = maps.door_map[m]
            mr = maps.door_map[m2]
            is_reciprocal = (m == mr)
            is_shared = [ses for ses in shared_exits_sets if {m, mr}.issubset(ses)]
            if not is_reciprocal and not is_shared:
                exception_text = 'INVALID DOOR MAP: ' + str(m) + " --> " + str(m2) + '; ' + str(m2) + " --> " + str(
                    mr)
                raise Exception(exception_text)

        temp = [m for m in maps.door_map.keys() if
                m + 4000 in exit_data.keys() and m + 4000 not in maps.door_map.keys()]
        if maps.doors.verbose:
            vprint(f"Adding WoR exits for doors: {temp}")
        for m in temp:
            # Add logical WoR exits to the map (with vanilla connections)
            wor_door = m + 4000
            wor_pair = exit_data[wor_door][0]
            if maps.doors.verbose:
                vprint(f"  WoR door {wor_door}: exit_data[{wor_door}][0] = {wor_pair}")
                if wor_pair >= 1281 and wor_pair <= 1300:
                    vprint(f"  WARNING: WoR pair {wor_pair} is in safe_id range!")
            maps.door_map[wor_door] = wor_pair
            # Don't overwrite the mapping for wor_pair if it is mapped
            if wor_pair not in exit_data.keys():
                maps.door_map[wor_pair] = wor_door

            # Look up the rooms of these exits (including character-locked doors)
            this_room = find_room_for_door(m + 4000)
            if this_room is not None:
                maps.doors.door_rooms[m + 4000] = this_room
            that_room = find_room_for_door(maps.door_map[m + 4000])
            if that_room is not None:
                maps.doors.door_rooms[maps.door_map[m + 4000]] = that_room

        # Check if any safe_id values ended up in door_map
        safe_ids_in_map = [d for d in maps.door_map.keys() if 1281 <= d <= 1300]
        if safe_ids_in_map and maps.doors.verbose:
            vprint(f"WARNING: safe_id values in door_map after WoR exits: {safe_ids_in_map}")

        # Patch all used exits
        # Also patch exits that are logical and have different destinations than their WOB companions ...
        # But only include logical exits (>= 4000) if they're actually used in door_map
        used_exits = set(maps.door_map.keys())
        patch_exits = [e for e in exit_data_patch.keys() if e < 4000 or e in used_exits]
        exits_to_patch = list(set(list(used_exits) + patch_exits)) + \
                         [e for e in event_door_connection_data.keys()]
        force_explicit = False
        if maps.args.ruination_mode:
            if 978 not in exits_to_patch:
                exits_to_patch.append(978)  # Cave in the Veldt must be forced in ruination mode.
            force_explicit = True  # Always force explicit in ruination mode, even if 978 is already in exits_to_patch
        # print(exits_to_patch)
        maps.exits.patch_exits(exits_to_patch, force_explicit=force_explicit)
        for e in maps.exits.exit_original_data.keys():
            if len(maps.exits.exit_original_data[e]) == 12:
                # need to append map_id for event doors
                this_map = maps.exit_maps[e]
                if this_map == SWITCHYARD_MAP and e in event_return_map.keys():
                    maps.exits.exit_original_data[e].append(event_return_map[e])
                else:
                    maps.exits.exit_original_data[e].append(this_map)

        # Add required explicit exits, if required
        for m in map_shuffle_partner_explicit:
            if m in maps.door_map.keys():
                map_shuffle_force_explicit.append(maps.door_map[m])

        # If dungeon crawl mode, add override exits
        if maps.args.door_randomize_dungeon_crawl or maps.args.ruination_mode:
            safe_id = max([d for d in exit_data.keys() if d < 1500])
            if maps.doors.verbose:
                vprint(f"Applying dungeon_crawl override, starting safe_id: {safe_id}")
            for d in dungeon_crawl_exit_destination_override.keys():
                safe_id += 1  # get a new safe door id

                # Update or add an entry for the new match
                if d in exit_data.keys():
                    exit_data[d][0] = safe_id
                else:
                    exit_data[d] = [safe_id, '(override for dungeon crawl)']

                this_data = dungeon_crawl_exit_destination_override[d]
                maps.exits.exit_original_data[safe_id] = this_data
                # print('Added exit data: ', d, '-->', safe_id, ': ', this_data)

        # Create a trapdoor map for reference
        for m in maps.doors.map[1]:
            if m[0] not in maps.trap_map.keys():
                maps.trap_map[m[0]] = m[1]

    # Final debug check
    safe_ids_final = [d for d in maps.door_map.keys() if 1281 <= d <= 1300]
    safe_ids_as_values = [k for k, v in maps.door_map.items() if 1281 <= v <= 1300]
    if maps.doors.verbose:
        vprint(f"=== postprocess_door_map() FINISHED ===")
        vprint(f"door_map has {len(maps.door_map)} entries")
    if safe_ids_final and maps.doors.verbose:
        vprint(f"WARNING: safe_id keys in door_map: {safe_ids_final}")
        for sid in safe_ids_final:
            vprint(f"  door_map[{sid}] = {maps.door_map[sid]}")
    if safe_ids_as_values and maps.doors.verbose:
        vprint(f"WARNING: safe_id VALUES in door_map: {[(k, maps.door_map[k]) for k in safe_ids_as_values]}")

    if maps.doors.verbose:
        vprint('Door connections:')
        for m in maps.doors.map[0]:
            ma = [a for a in m]
            ma.sort()
            # Use door_descr if available, otherwise try exit_data, otherwise show ID
            desc0 = maps.doors.door_descr.get(ma[0], exit_data.get(ma[0], [None, f'ID:{ma[0]}'])[1])
            desc1 = maps.doors.door_descr.get(ma[1], exit_data.get(ma[1], [None, f'ID:{ma[1]}'])[1])
            vprint('\t' + str(ma[0]) + "<-->" + str(ma[1]) + '\t(' + desc0 + '<-->' + desc1 + ')')
        vprint('One-way connections:')
        for m in maps.doors.map[1]:
            vprint('\t', m[0], " -> ", m[1])

