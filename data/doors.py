from openpyxl import load_workbook
from random import randrange
from data.rooms import room_data, forced_connections, shared_exits
from data.map_exit_extra import exit_data, doors_WOB_WOR  # for door descriptions, WOR/WOB equivalent doors

# DOORDATAFILE = 'LocationRandomizer-WC.xlsm'
ROOM_SETS = {
    'Umaro': [364, 365, 366, '367a', '367b', '367c', 368, '368a'],
    'UpperNarshe_WoB': [19, 20, '21a', 22, 23, 53, 54, 55, 59, 60],
    'UpperNarshe_WoR': [37, 38, '39a', 40, 41, 42, 43, 44, 46, 47],
    'EsperMountain': ['487a', 488, '489a', 490, '491a', 492, 493, 494, 495, 496, 497, 498, 499, 500, 501],
    'OwzerBasement' : [277, 278, 279, 280, 281, 282, 283, 284, '285a'],
    'All': [364, 365, 366, '367a', '367b', '367c', 368, # Umaro's cave
            19, 20, '21a', 22, 23, 53, 54, 55, 59, 60,  # Upper Narshe WoB
            '37a', 38, '39a', 40, '41a', 42, 43, 44, 46, 47,  # Upper Narshe WoR
            '487a', 488, '489a', 490, '491a', 492, 493, 494, 495, 496, 497, 498, 499, 500, 501,  # Esper Mountain
            277, 278, 279, 280, 281, 282, 283, 284, '285a'  # Owzer's Basement
            ]
}


class Doors():
    def __init__(self, args):
        # self.rom = rom
        self.args = args

        self.doors = []
        self.door_rooms = {}
        self.door_descr = {}
        # self.door_maps = {}
        self.door_types = {}
        self.rooms = []
        self.room_doors = {}
        self.room_counts = {}
        self.forcing = {}
        self.zones = []
        self.zone_counts = []
        self.map = []

        self.match_WOB_WOR = False
        self.verbose = False

        # Read in the doors to be randomized.
        room_sets = []
        if self.args.door_randomize_all:  # -dra
            # Prioritize randomizing all doors
            room_sets.append(ROOM_SETS['All'])
        else:
            # Randomize separately
            if self.args.door_randomize_umaro:  # -dru
                room_sets.append(ROOM_SETS['Umaro'])

            if self.args.door_randomize_upper_narshe:  # -drun
                room_sets.append(ROOM_SETS['UpperNarshe_WoB'])
                self.match_WOB_WOR = True
            else:
                if self.args.door_randomize_upper_narshe_wob:  # -drunb
                    room_sets.append(ROOM_SETS['UpperNarshe_WoB'])
                if self.args.door_randomize_upper_narshe_wor:  # -drunr
                    room_sets.append(ROOM_SETS['UpperNarshe_WoR'])

            if self.args.door_randomize_esper_mountain:  # -drem
                room_sets.append(ROOM_SETS['EsperMountain'])

            if self.args.door_randomize_owzer_basement:  # -drob
                room_sets.append(ROOM_SETS['OwzerBasement'])

        self.read(room_sets)

    def read(self, whichRooms=[]):
        # Collect & organize data on rooms and doors
        for area in whichRooms:
            self.doors.append([])
            self.rooms.append(area)
            for room in area:
                # Collect room info:
                self.room_doors[room] = room_data[room]
                self.room_counts[room] = [len(s) for s in room_data[room][:-1]]
                # Extract door info
                for i in range(3):
                    self.doors[-1].extend(room_data[room][i])
                    for d in room_data[room][i]:
                        self.door_types[d] = i
                        self.door_rooms[d] = room
                        if i < 2:
                            self.door_descr[d] = exit_data[d][1]
                            if d in shared_exits.keys():
                                for sd in shared_exits[d]:
                                    self.door_descr[sd] = exit_data[sd][1]
                            if self.match_WOB_WOR and d in doors_WOB_WOR.keys():
                                # Also grab the description for the matching WOR door
                                self.door_descr[doors_WOB_WOR[d]] = exit_data[doors_WOB_WOR[d]][1]
                        else:
                            self.door_descr[d] = exit_data[d-1000][1] + " DESTINATION"

            for d in self.doors[-1]:
                if d in forced_connections.keys():
                    self.forcing[d] = forced_connections[d]

    def mod(self):
        # Create list of randomized connections
        # Connect rooms together to produce zones
        map1 = self.map_doors()
        if self.match_WOB_WOR:
            # Make the WOR map match the WOB map in relevant areas
            if self.verbose:
                print('Mapping WoR to match WoB ...')
            d = [m for m in map1 if m[0] in doors_WOB_WOR.keys()]
            map1.extend([[doors_WOB_WOR[m[0]], doors_WOB_WOR[m[1]]] for m in d])


        flag = True
        failures = 0
        while flag:
            try:
                map2 = self.map_oneways()
                flag = False
            except Exception:
                failures += 1
                print('Error in mapping one-ways; trying again (' + str(failures) + ' errors)')
                if failures > 4:
                    raise Exception('Major Error: something is seriously wrong.')
        self.map = [map1, map2]


    def map_doors(self):
        # Generate list of valid (i.e. 2-way) doors & reverse door-->room lookup
        map = []
        error_ctr = 0
        for a in range(len(self.rooms)):
            zones = []
            zone_counts = []
            for R in self.rooms[a]:
                # Each zone is a list of rooms in that zone.  Initially, each zone contains only one room
                zones.append([R])
                zone_counts.append([c for c in self.room_counts[R]])
            door_zones = {}
            for zi in range(len(zones)):
                for d in self.room_doors[zones[zi][0]][0]:
                    door_zones[d] = zi

            doors = [d for d in self.doors[a] if self.door_types[d] == 0]
            to_force = [d for d in self.forcing.keys() if d in doors]

            if self.verbose:
                print('Mapping area', a, ':', len(doors), ' doors... ')
                counter = 1
            # Connect all valid doors, creating zones in the process
            while len(doors) > 0:
                if self.verbose:
                    print('\n[', counter, '] Zone state: ')
                    counter += 1
                    for z in range(len(zones)):
                        print(z, ':', zones[z], ', ', zone_counts[z])

                # Certain special cases are liable to end up isolated and should always be connected first.
                # Identify the dead end zones
                deadEnds = [zi for zi in range(len(zones)) if zone_counts[zi] == [1, 0, 0]]
                # Identify hallway zones
                hallways = [zi for zi in range(len(zones)) if zone_counts[zi] == [2, 0, 0]]
                # Identify single-exit zones
                one_exits = [zi for zi in range(len(zones)) if zone_counts[zi] == [1, 1, 0]]
                # Identify single-entry zones
                one_entrs = [zi for zi in range(len(zones)) if zone_counts[zi] == [1, 0, 1]]
                if len(to_force) > 0:
                    door1 = to_force.pop(0)
                    valid = self.forcing[door1]
                    if self.verbose:
                        print('Connecting ', door1, ' [rm ', self.door_rooms[door1], '] (forced):')

                elif len(deadEnds) > 0:
                    # First, always connect any dead-end zones (those with only one door)
                    # Select a door in a dead end zone
                    if self.verbose:
                        for d in doors:
                            print(d, door_zones[d])
                    deadEndDoors = [d for d in doors if door_zones[d] in deadEnds]

                    # Choose a random door
                    door1 = deadEndDoors.pop(randrange(len(deadEndDoors)))
                    doors.remove(door1)  # clean up
                    zone1 = [i for i in range(len(zones)) if self.door_rooms[door1] in zones[i]][0]

                    if len(doors) == 1:
                        # Case if there are only two dead-end zones left: connect them.
                        valid = [d for d in doors]
                    else:
                        # Construct a list of valid zone connections:  Any zone that is not [1, 0, 0]; [1, n, 0]; [1, 0, n]
                        valid_zone2 = [zi for zi in range(len(zones)) if
                                       zone_counts[zi] != [1, 0, 0] and
                                       not (zone_counts[zi][0] == 1 and zone_counts[zi][1] == 0) and
                                       not (zone_counts[zi][0] == 1 and zone_counts[zi][2] == 0)]
                        valid = [d for d in doors if door_zones[d] in valid_zone2]
                    if self.verbose:
                        print('Connecting ', door1, ' [rm ', self.door_rooms[door1], '] (dead end):')

                elif len(hallways) > 0:
                    # Second, always connect any hallway zones (those with only two doors)
                    # Select a door in a dead end zone
                    hallwayDoors = [d for d in doors if door_zones[d] in hallways]

                    # Choose a random door
                    door1 = hallwayDoors.pop(randrange(len(hallwayDoors)))
                    doors.remove(door1)  # clean up
                    zone1 = [i for i in range(len(zones)) if self.door_rooms[door1] in zones[i]][0]

                    # Construct a list of valid zone connections:  Any zone that is not itself.
                    # Dead end zones would also be taboo but are impossible.
                    valid_zone2 = [zi for zi in range(len(zones)) if zi != zone1]
                    valid = [d for d in doors if door_zones[d] in valid_zone2]
                    if self.verbose:
                        print('Connecting ', door1, ' [rm ', self.door_rooms[door1], '] (hallway):')

                else:
                    # All dead-end and hallway zones have been connected.
                    # Connect all remaining doors, following the rules:
                    #   - (unless only 2 doors are left) each zone must have at least 1 entry and 1 exit.
                    #   - Once connected, the sum of all other zones has at least one exit and one entrance per zone (?)

                    # Choose a random door
                    if len(one_exits) > 0:
                        # Third, always connect any rooms with a single exit
                        oneexitDoors = [d for d in doors if door_zones[d] in one_exits]

                        # Choose a random door
                        door1 = oneexitDoors.pop(randrange(len(oneexitDoors)))
                        doors.remove(door1)  # clean up
                        zone1 = [i for i in range(len(zones)) if self.door_rooms[door1] in zones[i]][0]

                        if self.verbose:
                            print('Connecting ', door1, ' [rm ', self.door_rooms[door1], '] (single exit):')

                    elif len(one_entrs) > 0:
                        # Fourth, always connect any rooms with a single entrance
                        oneentryDoors = [d for d in doors if door_zones[d] in one_entrs]

                        # Choose a random door
                        door1 = oneentryDoors.pop(randrange(len(oneentryDoors)))
                        doors.remove(door1)  # clean up
                        zone1 = [i for i in range(len(zones)) if self.door_rooms[door1] in zones[i]][0]

                        if self.verbose:
                            print('Connecting ', door1, ' [rm ', self.door_rooms[door1], '] (single entry):')

                    else:
                        door1 = doors.pop(randrange(len(doors)))
                        zone1 = [i for i in range(len(zones)) if self.door_rooms[door1] in zones[i]][0]
                        if self.verbose:
                            print('Connecting ', door1, ' [rm ', self.door_rooms[door1], ']:')

                    # Construct list of valid doors: start with all doors, then remove invalid ones
                    valid = [d for d in doors]
                    invalid = []
                    if len(doors) > 2:
                        # Remove doors that would create a zone with zero exits or zero entrances
                        # i.e. a zone with [0, n, 0], or [0, 0, n].
                        z1_exits = zone_counts[zone1][0] + zone_counts[zone1][1]
                        z1_enter = zone_counts[zone1][0] + zone_counts[zone1][2]

                        for d in valid:
                            z2 = door_zones[d]

                            outside_zones = [zi for zi in range(len(zones)) if zi != zone1 and zi != z2
                                             and zone_counts[zi][0] > 0]
                            if len(outside_zones) > 0:
                                # Remove connections that would leave outside zones with insufficient exits or entrances
                                outside_counts = [sum([zone_counts[i][0] for i in outside_zones]),
                                                  sum([zone_counts[i][1] for i in outside_zones]),
                                                  sum([zone_counts[i][2] for i in outside_zones])]
                                # Tally doors in the combined zone
                                inside_counts = [i for i in zone_counts[zone1]]
                                if z2 != zone1:
                                    for i in range(3):
                                        inside_counts[i] += zone_counts[z2][i]
                                inside_counts[0] -= 2   # remove connected doors
                                if (inside_counts[0] == 0 or outside_counts[0] == 0) and \
                                        (outside_counts[1] == 0 or outside_counts[2] == 0):
                                    # Will force an outside zone with no exit or no entrance
                                    invalid.append(d)
                                    if self.verbose:
                                        print('\t\t', d, '(', self.door_rooms[d], ') invalid from outside rule: ', outside_zones, ' --> ', outside_counts)

                            if zone1 == z2:
                                # Self connection will remove two entrances and two exits from the zone
                                if (z1_exits - 2 < 1) or (z1_enter - 2 < 1):
                                    # Creates a zone with no exit or no entrance
                                    invalid.append(d)
                                    if self.verbose:
                                        print('\t\t', d, '(', self.door_rooms[d], ') invalid from self rule: ', zone1, ' --> ', z1_exits, z1_enter)
                            else:
                                z2_exits = zone_counts[z2][0] + zone_counts[z2][1]
                                z2_enter = zone_counts[z2][0] + zone_counts[z2][2]
                                # Note that the connection will remove 1 door (=1 exit + 1 entrance) from each zone
                                if ((z1_exits + z2_exits) - 2 < 1) or ((z1_enter + z2_enter) - 2 < 1):
                                    # Creates a zone with no exit or no entrance
                                    invalid.append(d)
                                    if self.verbose:
                                        print('\t\t', d, '(', self.door_rooms[d], ') invalid: ', zone1, ' --> ', z1_exits, z1_enter, ', ', z2,
                                              ' --> ', z2_exits, z2_enter)

                    invalid = list(set(invalid))  # remove duplicates, if any.
                    for i in invalid:
                        valid.remove(i)

                if self.verbose:
                    print('\tValid connections: ')
                    for v in valid:
                        print('\t\t', v, ' (rm ', self.door_rooms[v], ')')

                # Select a connecting door
                if len(valid) == 0:
                    # No valid doors; try to self-correct by connecting something else.
                    # It may be too late, so break if you fail too many times.
                    if self.verbose:
                        print('ERROR: no valid doors!')
                        doors.append(door1)
                        error_ctr += 1
                        if error_ctr > 3:
                            raise Exception('ERROR: too many errors.')
                else:
                    door2 = valid.pop(randrange(len(valid)))
                    zone2 = [i for i in range(len(zones)) if self.door_rooms[door2] in zones[i]][0]
                    doors.remove(door2)
                    if self.verbose:
                        print('\tSelected:', door2)

                    # Write the connection
                    map.append([door1, door2])

                    # Modify the zones if necessary
                    if zone1 != zone2:
                        # Add zone2 to zone1
                        zones[zone2].extend(zones[zone1])
                        zones[zone1] = []

                        # Adjust counts
                        for i in range(len(zone_counts[zone2])):
                            zone_counts[zone2][i] += zone_counts[zone1][i]
                            zone_counts[zone1][i] = 0

                        # Update door_zone listing
                        for d in self.room_doors[self.door_rooms[door1]][0]:
                            door_zones[d] = zone2
                        # door_zones[door2] = zone2  # shouldn't be necessary

                    # Decrement these two doors from the zone
                    zone_counts[zone2][0] += -2

            # Clean up
            keep = [i for i in range(len(zones)) if zones[i] != []]
            zones = [zones[k] for k in keep]
            zone_counts = [zone_counts[k] for k in keep]

            self.zones.append(zones)
            self.zone_counts.append(zone_counts)

        if self.verbose:
            print('\nDoor mapping complete!')
            print(error_ctr, ' errors occurred.')
            for a in range(len(self.zones)):
                print('Area',a,'Final zones: ')
                for z in range(len(self.zones[a])):
                    print(z,': ', self.zones[a][z], ', ', self.zone_counts[a][z])

        # Append shared doors to the map
        for m in map:
            if m[0] in shared_exits.keys():
                for se in shared_exits[m[0]]:
                    # Send shared exits to the same destination
                    map.append([se, m[1]])
            if m[1] in shared_exits.keys():
                for se in shared_exits[m[1]]:
                    # Send shared exits to the same destination
                    map.append([m[0], se])

        return map

    def map_oneways(self):
        # Generate lists of 1-way gates & reverse gate-->zone lookups
        map = []
        for a in range(len(self.rooms)):
            nobs = []  # "outs" one-way exits
            nibs = []  # "ins" one-way entrances
            nob_rooms = {}
            nib_rooms = {}
            for R in self.rooms[a]:
                nobs.extend([n for n in self.room_doors[R][1]])
                for nob in self.room_doors[R][1]:
                    nob_rooms[nob] = R
                nibs.extend([n for n in self.room_doors[R][2]])
                for nib in self.room_doors[R][2]:
                    nib_rooms[nib] = R

            zones = [z for z in self.zones[a]]
            zone_counts = [[c[0], c[1], c[2]] for c in self.zone_counts[a]]

            nob_zones = {}
            nib_zones = {}
            zone_nobs = {}
            zone_nibs = {}
            for zi in range(len(zones)):
                zone_nobs[zi] = []
                zone_nibs[zi] = []
                for R in zones[zi]:
                    for nob in self.room_doors[R][1]:
                        nob_zones[nob] = zi
                        zone_nobs[zi].append(nob)
                    for nib in self.room_doors[R][2]:
                        nib_zones[nib] = zi
                        zone_nibs[zi].append(nib)

            to_force = [n for n in self.forcing.keys() if n in nobs]
            forced_nibs = []
            for n in to_force:
                # Disallow forced nibs, except for the forcing nob
                if self.forcing[n] in nibs:
                    forced_nibs.extend(self.forcing[n])

            # Walk through all valid one-ways, connecting all zones and returning to the starting point
            walk = []
            if self.verbose:
                print('\nMapping Area',a,'one-way exits ... ')
            if len(nobs) > 0:
                if len(to_force) > 0:
                    # Start with a forced nob (reduces errors)
                    nob = to_force[0]
                    nobs.remove(nob)
                else:
                    # Choose a random trap door to begin
                    nob = nobs.pop(randrange(len(nobs)))

                zone1 = nob_zones[nob]
                walk.append(zone1)  # record the path of the walk

                while len(nibs) > 0:
                    if self.verbose:
                        print('\nZone state: ')
                        for z in range(len(zones)):
                            print(z, ': ', zones[z], ', ', zone_counts[z])
                        print('Walk state: ', walk)
                        print('Connecting: ', nob, '(', self.door_rooms[nob], ')')

                    # Construct list of valid entrances: start with all nibs, then remove invalid ones
                    valid = [n for n in nibs]
                    invalid = []

                    is_forced = nob in self.forcing.keys()
                    if is_forced:
                        # This is a forced connection.  There are two uses of this:
                        # 1. forcing[nob] = [forced nibs]   # Only the entrances (nibs) in forcing[nob] are valid.
                        # 2. forcing[nob] = [forced nobs]   # Force one exit to equal another exit (e.g. Umaro's cave #2 trapdoors)
                        # We check whether forcing[nob] is entrances (nib) or exits (nob);
                        #   If it's a list of entrances, connect one of them;
                        #   if it's a list of exits, look to see if one of them is already connected;
                        #       if so, connect this one to that same entrance (don't decrement entrances in zone 2)
                        #       if not, just connect this one as normal.
                        to_force.remove(nob)  # clean up
                        forced = self.forcing[nob]
                        these_nibs = [n for n in forced if n in nibs]
                        if len(these_nibs) > 0:
                            # this is a list of entrances that are valid for this exit
                            valid = these_nibs
                            if self.verbose:
                                print('\tForced entrance connection: ', valid)
                        else:
                            # forced is a list of exits that must match.
                            # Look to see if any have been assigned.
                            assigned = [n for n in forced if n not in nobs]
                            if len(assigned) > 0:
                                # Find the previously-assigned connection in the map; take the nib
                                mapped_nib = [m for m in map if assigned[0] == m[0]][0][1]
                                valid = [mapped_nib]
                                if self.verbose:
                                    print('\tForced exit connection: ', valid)
                            else:
                                # Assign this one normally
                                is_forced = False
                                if self.verbose:
                                    print('\tExit not forced.')

                    if len(nibs) > 1 and not is_forced:
                        # Remove doors that would create a zone with zero exits or zero entrances
                        # i.e. a zone with [0, n, 0], or [0, 0, n].
                        z1_exits = zone_counts[zone1][1]
                        z1_enter = zone_counts[zone1][2]
                        invalid.extend(forced_nibs)  # don't allow connections to forced entrances

                        for n in valid:
                            z2 = nib_zones[n]

                            # We need to remove loops into the walk that have no downstream exits
                            if zone1 == z2:
                                if self.verbose:
                                    print('\t\tTesting', n, '... ', '(', self.door_rooms[n], ') (same zone)')
                                # Connection will remove an exit and an entrance from the zone
                                if (z1_exits - 1) < 1 or (z1_enter - 1) < 1:
                                    # Connection would create a walk with no exits or no entrances
                                    invalid.append(n)
                                    if self.verbose:
                                        print('\tRemoving ', n, ' (same zone: ', zone_counts[zone1], ')')

                            elif z2 in walk:
                                if self.verbose:
                                    print('\t\tTesting', n, '... ', '(', self.door_rooms[n], ') in walk)')
                                # Search for a remaining downstream exit
                                z2i = walk.index(z2)
                                flag = 0
                                for wi in range(z2i, len(walk)):
                                    if walk[wi] == zone1 and z1_exits > 1:
                                        if self.verbose:
                                            print('\t\t\tenough exits in the present zone!')
                                        flag = 1
                                        break
                                    elif walk[wi] != zone1 and zone_counts[walk[wi]][1] > 0:
                                        if self.verbose:
                                            print('\t\t\tenough exits in zone', walk[wi])
                                        flag = 1
                                        break
                                if flag == 0:
                                    # If no remaining downstream exit, remove this entrance
                                    invalid.append(n)
                                    if self.verbose:
                                        print('\tRemoving ', n, ' (zone ', z2, 'in walk, count: ', zone_counts[z2], ')')

                            else:
                                # z2 isn't in the walk yet.  Verify that the connection would still have exits.
                                z2_exits = zone_counts[z2][1]
                                z2_enter = zone_counts[z2][2]
                                # Connection will remove 1 exit from zone1 and 1 entrance from zone2
                                if z2_exits < 1:
                                    # Connection would create a walk with no exits
                                    invalid.append(n)
                                    if self.verbose:
                                        print('\tRemoving ', n, ' (zone ', z2, 'not in walk, count: ', zone_counts[z2], ')')

                    for i in invalid:
                        valid.remove(i)

                    # Select an entrance to connect:
                    nib = valid.pop(randrange(len(valid)))
                    zone2 = nib_zones[nib]
                    if nib in nibs:
                        nibs.remove(nib)
                        zone_counts[zone2][2] -= 1  # decrement entrances (nibs) in zone2
                    if nib in forced_nibs:
                        forced_nibs.remove(nib)
                    if self.verbose:
                        print('Selected entrance: ', nib)

                    # Write the connection
                    map.append([nob, nib])
                    zone_counts[zone1][1] -= 1  # decrement exits (nobs) in zone1

                    # Update the walk and zone counts
                    walk.append(zone2)

                    # If we created a loop, combine all zones in the loop into a new zone
                    # A loop is created when a zone appears a second time in the walk, and is always bookended by zone2.
                    if walk.count(zone2) > 1:
                        loop = walk[walk.index(zone2):-1]
                        if len(loop) == 1:
                            # Self loop only, skip it.
                            walk = walk[:-1]
                            if self.verbose:
                                print('\tSelf loop found (ignored)')
                        else:
                            # Create a new zone with the properties of all the zones in the loop
                            # Gather information on the new zone
                            if self.verbose:
                                print('\tLoop found: ', zone2, ': ', walk,' - Compressing')
                            newzone = []
                            newzone_count = [0, 0, 0]
                            newzone_nobs = []
                            newzone_nibs = []
                            for zi in loop:
                                newzone.extend(zones[zi])
                                for j in range(3):
                                    newzone_count[j] += zone_counts[zi][j]
                                newzone_nobs.extend(zone_nobs[zi])
                                newzone_nibs.extend(zone_nibs[zi])
                                # Delete old zone information
                                zones[zi] = []
                                zone_counts[zi] = [0, 0, 0]
                                zone_nobs[zi] = []
                                zone_nibs[zi] = []
                            nzi = len(zones)  # new zone index
                            # Create the new zone
                            zones.append(newzone)
                            zone_counts.append(newzone_count)
                            zone_nobs[nzi] = newzone_nobs
                            # Update dictionaries for nob zones & nib zones
                            for n in zone_nobs[nzi]:
                                nob_zones[n] = nzi
                            zone_nibs[nzi] = newzone_nibs
                            for n in zone_nibs[nzi]:
                                nib_zones[n] = nzi
                            # Update walk to replace the loop with the new zone ID
                            walk = walk[:walk.index(zone2)]
                            walk.append(nzi)
                            zone2 = nzi

                    # Construct the list of all downstream exits...
                    z2i = walk.index(zone2)
                    available = []
                    for wi in range(z2i, len(walk)):
                        available.extend([nob for nob in zone_nobs[walk[wi]] if nob in nobs])
                    # ... And randomly select one to connect:
                    available = list(set(available))  # just unique values
                    if self.verbose:
                        print('Available exits: ', available)
                    if len(nibs) > 0:
                        # prepare for the next loop
                        if len(available) > 0:
                            # If any available are forced, do them first.
                            available_forced = list(set(available).intersection(to_force))
                            if len(available_forced) > 0:
                                nob = available_forced.pop(randrange(len(available_forced)))
                            else:
                                nob = available.pop(randrange(len(available)))
                            nobs.remove(nob)
                            zone1 = nob_zones[nob]
                        else:
                            if len(nobs) > 0:
                                print(zones, zone_counts)
                                print(map)
                                print(available)
                                raise Exception('ERROR: remaining exits cannot be reached!')

            # Clean up
            if len(nobs) > 0:
                # There's probably a forced nob(s) that hasn't been connected.
                for nob in nobs:
                    print('Found a disconnected nob!', nob, '(to_force = ', to_force, ')')
                    if nob in to_force:
                        to_force.remove(nob)  # clean up
                        # Look for forced exits that have been assigned.
                        forced = self.forcing[nob]
                        assigned = [n for n in forced if n not in nobs]
                        if len(assigned) > 0:
                            # Find the previously-assigned connection in the map; take the nib
                            mapped_nib = [m for m in map if assigned[0] == m[0]][0][1]
                            map.append([nob, mapped_nib])
                            if self.verbose:
                                print('\tCleanup: forced exit connection: ', nob, ' --> ', mapped_nib)
        return map

    def print(self):
        # Print state of the Doors object
        for a in range(len(self.rooms)):
            print('Area',a,':')
            print('\tDoors:')
            for d in self.doors[a]:
                print('\t\t', d, ': Room = ', self.door_rooms[d], '. ', self.door_descr[d])  # ', Map = ', self.door_maps[d],
            print('\tRooms:')
            for r in self.rooms[a]:
                print('\t\t', r, ': door count = ', self.room_counts[r], '\n\t\tdoors: ', self.room_doors[r][0],
                      '\n\t\tone-way exits: ', self.room_doors[r][1], '\n\t\t one-way entrances: ', self.room_doors[r][2])
        print('Forced connections:')
        for d in self.forcing.keys():
            print('\t', d, ' --> ', self.forcing[d])
        if len(self.map) > 0:
            print('Map:')
            for m in self.map[0]:
                print('\t', m[0], ' --> ', m[1], '(', self.door_descr[m[0]], ' --> ', self.door_descr[m[1]], ')')
            for m in self.map[1]:
                print('\t', m[0], ' --> ', m[1], '(', self.door_descr[m[0]], ' --> ', self.door_descr[m[1]], ')')
