#from openpyxl import load_workbook
from random import randrange, choices
from data.rooms import room_data, forced_connections, shared_oneways, shared_exits, invalid_connections
from data.map_exit_extra import exit_data, doors_WOB_WOR  # for door descriptions, WOR/WOB equivalent doors

ROOM_SETS = {
    'Umaro': [364, 365, 366, '367a', '367b', '367c', 368, 'root-u'],
    'UpperNarshe_WoB': [19, 20, 22, 23, 53, 54, 55, 59, 60, 'root-unb'],
    'UpperNarshe_WoR': [37, 38, 40, 41, 42, 43, 44, 46, 47, 'root-unr'],
    'EsperMountain': [488, 489, 490, 491, 492, 493, 494, 495, 496, 497, 498, 499, 500, 501, 'root-em'],
    'OwzerBasement' : [277, 278, 279, 280, 281, 282, 283, 284, 'root-ob'],
    'MagitekFactory' : [345, 346, 347, 349, 351, 352, 353, 354, 355, '355a', 'root-mf'],
    'SealedGate' : [503, 504, '504a', 505, 506, 507, 508, 509, 510, 511, 512, 513, 514, 'root-sg'],
    'Zozo' : [294, 295, 296, 297, 298, 299, 300, 301, 302, '303a', '303b', 304, 305, 306, '307a', 309, 310, 311, 312, 313, 'root-zb'],
    'Zozo-WOR' : ['294r', '295r', '296r', '301r', '305r', '306r', '307r', '309r', 'root-zr', 'branch-mz'],
    'MtZozo' : [250, 251, 252, 253, 254, 255, 256, 'root-mz'],
    'All': [
            364, 365, 366, '367a', '367b', '367c', 368,  # Umaro's cave
            19, 20, 22, 23, 53, 54, 55, 59, 60, 'root-unb',  # Upper Narshe WoB
            '37a', 38, 40, '41a', 42, 43, 44, 46, 47, 'root-unr',  # Upper Narshe WoR
            488, 489, 490, 491, 492, 493, 494, 495, 496, 497, 498, 499, 500, 501, 'root-em',  # Esper Mountain
            277, 278, 279, 280, 281, 282, 283, 284, 'root-ob',  # Owzer's Basement
            345, 346, 347, 349, 351, 352, 353, 354, 355, '355a', 'root-mf',  # Magitek Factory
            503, 504, '504a', 505, 506, 507, 508, 509, 510, 511, 512, 513, 514, 'root-sg',  # Cave to the Sealed Gate
            294, 295, 296, 297, 298, 299, 300, 301, 302, '303a', '303b', 304, 305, 306, '307a', 309, 310, 311, 312, 313, 'root-zb', # Zozo-WoB
            '294r', '295r', '296r', '301r', '305r', '306r', '307r', '309r', 'root-zr', # Zozo-WoR
            250, 251, 252, 253, 254, 255, 256  # Mt. Zozo
             ],
    'test': [8, 284]  # for testing only
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
        self.sharing = {}
        self.invalid = {}
        self.zones = []
        self.zone_counts = []
        self.map = []

        self.use_shared_exits = True
        self.match_WOB_WOR = False
        self.verbose = True

        self._all_rooms = []

        # Read in the doors to be randomized.
        room_sets = []
        if self.args.door_randomize_all or self.args.door_randomize_dungeon_crawl:  # -dra, -drdc
            # Prioritize randomizing all doors.
            # Both options the same room list.  -dra uses drafting; -drdc does not.
            room_sets.append(ROOM_SETS['All'])

        elif self.args.door_randomize_each:  # -dre
            # Randomize all areas separately
            for key in ROOM_SETS.keys():
                if key != 'All':
                    room_sets.append(ROOM_SETS[key])

        else:
            # Randomize separately
            if self.args.door_randomize_umaro:  # -dru
                room_sets.append(ROOM_SETS['Umaro'])

            if self.args.door_randomize_upper_narshe:  # -drun
                room_sets.append(ROOM_SETS['UpperNarshe_WoB'])
                room_sets.append(ROOM_SETS['UpperNarshe_WoR'])  # this randomization will be overwritten
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

            if self.args.door_randomize_magitek_factory:  # -drmf
                room_sets.append(ROOM_SETS['MagitekFactory'])

            if self.args.door_randomize_sealed_gate:  # -drsg
                room_sets.append(ROOM_SETS['SealedGate'])

            if self.args.door_randomize_zozo_wob:  # -drzb
                room_sets.append(ROOM_SETS['Zozo'])

            if self.args.door_randomize_zozo_wor:  # -drzr
                room_sets.append(ROOM_SETS['Zozo-WOR'])

            if self.args.door_randomize_mt_zozo:  # -drmz
                room_sets.append(ROOM_SETS['MtZozo'])

            room_sets.append(ROOM_SETS['test'])

        self.read(room_sets)

    def read(self, whichRooms=[]):
        # Collect & organize data on rooms and doors
        for area in whichRooms:
            self.doors.append([])
            self.rooms.append(area)
            for room in area:
                # Collect room info:
                self.room_doors[room] = room_data[room][:-1]
                self.room_counts[room] = [len(s) for s in room_data[room][:-1]]

                if self.use_shared_exits:
                    # Look for shared exits & remove them from the
                    d_shared = [d for d in self.room_doors[room][0] if d in shared_exits.keys()]
                    for d in d_shared:
                        for s in shared_exits[d]:
                            if s in self.room_doors[room][0]:
                                self.room_doors[room][0].remove(s)
                                self.room_counts[room][0] -= 1

                # Extract door info
                for i in range(3):
                    self.doors[-1].extend(room_data[room][i])
                    for d in room_data[room][i]:
                        self.door_types[d] = i
                        self.door_rooms[d] = room
                        if i < 2:
                            if d in exit_data.keys():
                                self.door_descr[d] = exit_data[d][1]
                            else:
                                self.door_descr[d] = 'virtual door'
                            if d in shared_exits.keys():
                                for sd in shared_exits[d]:
                                    self.door_descr[sd] = exit_data[sd][1]
                            #if self.match_WOB_WOR and d in doors_WOB_WOR.keys():
                            #    # Also grab the description for the matching WOR door
                            #    self.door_descr[doors_WOB_WOR[d]] = exit_data[doors_WOB_WOR[d]][1]
                        else:
                            if (d-1000) in exit_data.keys():
                                self.door_descr[d] = exit_data[d-1000][1] + " DESTINATION"
                            else:
                                self.door_descr[d] = "virtual door DESTINATION"
                        # Capture information for shared exits
                        if d in shared_exits.keys():
                            for ds in shared_exits[d]:
                                self.door_types[ds] = i
                                self.door_rooms[ds] = room
                                self.door_descr[ds] = exit_data[ds][1]

            for d in self.doors[-1]:
                if d in forced_connections.keys():
                    self.forcing[d] = forced_connections[d]
                if d in shared_oneways.keys():
                    self.sharing[d] = shared_oneways[d]
                if d in invalid_connections.keys():
                    self.invalid[d] = invalid_connections[d]

    def mod(self):
        # Create list of randomized connections
        # Maybe re-write this to loop on each area separately (instead of all together) to increase success rate?
        flag_a = True
        failures_a = 0
        while flag_a:
            try:
                if self.args.door_randomize_all:
                    # Draft rooms to create areas for randomization
                    self.draft_areas()

                # Clear any previous attempts
                self.zones = []
                self.zone_counts = []

                map1 = []
                map2 = []
                for a in range(len(self.doors)):
                    flag_b = True
                    failures_b = 0
                    while flag_b:
                        try:
                            # Connect rooms together to produce zones
                            this_map = self.map_doors([a])

                            if self.match_WOB_WOR:
                                # Make the WOR map match the WOB map in relevant areas
                                if self.verbose:
                                    print('Mapping WoR to match WoB ...')
                                newmap = [m for m in this_map if m[0] in doors_WOB_WOR.keys()]
                                newmap.extend([[doors_WOB_WOR[m[0]], doors_WOB_WOR[m[1]]] for m in newmap])
                                this_map = [m for m in newmap]
                                #print(this_map)
                                #map1.extend([[doors_WOB_WOR[m[0]], doors_WOB_WOR[m[1]]] for m in d])

                            # Connect one-way exits together to produce a fully-connected map
                            that_map = self.map_oneways([a])

                            map1.extend(this_map)
                            map2.extend(that_map)

                            flag_b = False

                        except Exception:
                            failures_b += 1
                            print('Error in mapping doors in area' + str(a) + '; trying again (' + str(failures_b) + ' errors)')
                            if failures_b > 10:
                                raise Exception('Error: something is wrong in doors.mod()')

                flag_a = False

            except Exception:
                failures_a += 1
                print('Error in drafting areas; trying again (' + str(failures_a) + ' errors)')
                if failures_a > 10:
                    raise Exception('Major Error: something is seriously wrong in doors.mod()')

        self.map = [map1, map2]

    def draft_areas(self):
        DRAFT_PROBABILITY = 0.25
        is_even = lambda x: (x % 2) == 0

        if len(self._all_rooms) == 0:
            # Create backup in case of multiple drafting runs
            # All rooms are currently in area 0.
            self._all_rooms = [r for r in self.rooms[0]]

        rooms = [r for r in self._all_rooms]

        # Create an area for each 'root'
        roots = [r for r in rooms if str(r).find('root') >= 0]  # root entrances
        areas = []
        area_counts = []
        for root in roots:
            areas.append([root])
            area_counts.append([c for c in self.room_counts[root]])
            rooms.remove(root)  # clean up

        # HOW TO DEAL WITH FORCED CONNECTIONS?
        # HOW TO DEAL WITH SHARED ONEWAYS?
        # In both cases, if you find one, immediately append the shared/forced room to the same area?
        forcing = {}
        sharing = {}
        for f in forced_connections.keys():
            # find those in the current areas
            if f in self.door_rooms.keys():
                rf = self.door_rooms[f]  # the room with the forced connection
                rc = self.door_rooms[forced_connections[f][0]]  # room that is forced connected to
                if rf in forcing.keys():
                    # There's already another forced connection into rf, add this one to it
                    forcing[rf].append(rc)
                else:
                    forcing[rf] = [rc]  # Set the room --> room forcing
                if rc in forcing.keys():
                    # There's already another forced connection into rc, add this one to it
                    forcing[rc].append(rf)
                else:
                    forcing[rc] = [rf]  # include the reciprocal forcing

        for s in shared_oneways.keys():
            rs = self.door_rooms[s]
            rc = self.door_rooms[shared_oneways[s][0]]
            if rs in sharing.keys():
                if rc not in sharing[rs]:
                    sharing[rs].append(rc)
            else:
                sharing[rs] = [rc]
            if rc in sharing.keys():
                if rs not in sharing[rc]:
                    sharing[rc].append(rs)
            else:
                sharing[rc] = [rs]

        if self.verbose:
            print('Found forcing:', forcing)
            print('Found sharing:', sharing)

        # Have areas draft from the existing rooms
        ai_active = [i for i in range(len(areas))]
        while len(rooms) > 0:
            # Choose an area to draft
            ai = ai_active[randrange(len(ai_active))]
            count = area_counts[ai]
            if self.verbose:
                print(len(rooms),': drafting', ai, '(', count, ')')

            # Calculate room weights for this area
            if self.verbose:
                print('Rooms & weights:')
            room_weight = [1 for i in range(len(rooms))]
            for i in range(len(room_weight)):
                rc = self.room_counts[rooms[i]]

                # even # doors: slight benefit
                #if is_even(count[0] + rc[0]):
                #    room_weight[i] += 1

                # exits = entrances: larger benefit
                diff = count[1] - count[2]
                rdiff = rc[1] - rc[2]
                if abs(diff + rdiff) < abs(diff):
                    room_weight[i] += abs(diff) - abs(diff + rdiff)

                if self.verbose:
                    print('\t', rooms[i], '(', self.room_counts[rooms[i]], '):', room_weight[i])

            # Draft a room (weighted)
            room = choices(rooms, room_weight)[0]
            rooms.remove(room) # clean up
            if self.verbose:
                print('Selected:', room)

            # Add it to the area
            areas[ai].append(room)
            for i in range(3):
                count[i] += self.room_counts[room][i]

            # Look for forced connections
            if room in forcing.keys():
                rf = forcing.pop(room)
                if self.verbose:
                    print('\tForced connection found:', rf)
                for r in rf:
                    # Add the forced connection to the area
                    rooms.remove(r)
                    areas[ai].append(r)
                    for i in range(3):
                        count[i] += self.room_counts[r][i]
                    # Add reciprocal forced connections as well
                    if r in forcing.keys():
                        rfrf = forcing.pop(r)
                        for recip in rfrf:
                            if recip not in areas[ai]:
                                if self.verbose:
                                    print('\t\talso added reciprocal connection:', recip)
                                rooms.remove(recip)
                                areas[ai].append(recip)
                                for i in range(3):
                                    count[i] += self.room_counts[recip][i]
            # Look for shared one-way exits:
            if room in sharing.keys():
                # add the shared connection
                rs = sharing.pop(room)
                if self.verbose:
                    print('\tShared one-way found:', rs)
                for r in rs:
                    if r != room:
                        # Shared one-ways are not in the same room.  Add the other room too.
                        if r in sharing.keys():
                            rss = sharing.pop(r)  # remove reciprocal
                            reciprocals = [a for a in rss if a != room and a not in areas[ai]]
                            if self.verbose:
                                print('\t\tfound reciprocals:',r,'-->', reciprocals)
                            rs.extend(reciprocals)
                        if r in rooms:
                            rooms.remove(r)  # clean up
                        if r not in areas[ai]:
                            areas[ai].append(r)
                            for i in range(3):
                                count[i] += self.room_counts[r][i]
                            # Shared one-ways shouldn't count as an extra exit
                            count[1] -= 1
                            if self.verbose:
                                print('\t\tadded shared one-way', r, '& decremented')
                    else:
                        # Shared one-ways shouldn't count as an extra exit
                        count[1] -= 1
                        if self.verbose:
                            print('\t\tsame room, decremented.')

            # Determine if the area is closeable
            if len(ai_active) > 1 and is_even(count[0]) and (count[1] == count[2]):
                # if so, decide whether to close the area
                if choices([True, False], [6/(len(rooms)+1), 1 - 6/(len(rooms)+1)])[0]:
                    # Close the area
                    ai_active.remove(ai)
                    if self.verbose:
                        print('Closed area: ', ai, area_counts[ai])

        if self.verbose:
            print('Draft complete: ')
            for ai in range(len(areas)):
                print(ai,':',area_counts[ai],'\t',areas[ai])

        # Once drafting is complete, connect remaining areas if necessary.
        while len(ai_active) > 1:
            if self.verbose:
                print('Active areas:', ai_active)

            # Choose a starter
            ai = choices(ai_active)[0]
            if self.verbose:
                print(len(ai_active), ': merging', ai)

            # Search for a partner
            count = area_counts[ai]
            matches = []
            metric = {}
            for ai2 in [a for a in ai_active if a != ai]:
                count2 = area_counts[ai2]
                metric[ai2] = (count[1] + count2[1]) - (count[2] + count2[2])
                if is_even(count[0] + count2[0]) and metric[ai2] == 0:
                    # found a match
                    matches.append(ai2)

            if len(matches) > 0:
                # Select a partner
                ai2 = choices(matches)[0]
                if self.verbose:
                    print('\tFound a pair!', ai2, area_counts[ai2])
            else:
                # Choose whichever has the smallest metric
                min_val = min(metric.values())
                for ai2 in metric.keys():
                    if metric[ai2] == min_val:
                        matches.append(ai2)
                ai2 = choices(matches)[0]
                if self.verbose:
                    print('\tBest match:', ai2, area_counts[ai2])

            # Combine areas
            areas[ai].extend(areas[ai2])
            for i in range(3):
                area_counts[ai][i] += area_counts[ai2][i]
            areas[ai2] = []  # clean up
            area_counts[ai2] = [0, 0, 0]
            ai_active.remove(ai2)
            # Deactivate area if conditions are met
            if is_even(count[0]) and (count[1] == count[2]):
                ai_active.remove(ai)
                if self.verbose:
                    print('\t',ai,'now complete!')

            if self.verbose:
                print('\tMerged areas: new distribution')
                for ai in range(len(areas)):
                    print(ai, ':', area_counts[ai], '\t', areas[ai])

        if self.verbose:
            print('Drafting complete:')
            for ai in range(len(areas)):
                print(ai,':',area_counts[ai])
                for r in areas[ai]:
                    print('\t',r,'\t',self.room_counts[r])

        # Clean up & update the rooms lists & doors lists
        areas = [a for a in areas if len(a) > 0]
        self.rooms = areas
        self.doors = []
        for a in self.rooms:
            self.doors.append([])
            for r in a:
                for i in range(3):
                    # Read in the doors associated with each room
                    self.doors[-1].extend(room_data[r][i])


    def map_doors(self, areas='all'):
        # Generate list of valid (i.e. 2-way) doors & reverse door-->room lookup
        if areas == 'all':
            areas = [a for a in range(len(self.rooms))]

        map = []
        error_ctr = 0
        for a in areas:
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
                #for d in to_force:
                #    print('Forced: ', d, '-->', self.forcing[d])
                counter = 1

            # Connect all valid doors, creating zones in the process
            while len(doors) > 0:
                if self.verbose:
                    print('\n[', counter, '] Zone state: ')
                    counter += 1
                    for z in range(len(zones)):
                        if len(zones[z]) > 0:
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
                    doors.remove(door1)  # clean up
                    zone1 = door_zones[door1]
                    valid = [v for v in self.forcing[door1]]
                    if self.verbose:
                        print('Connecting ', door1, ' [rm ', self.door_rooms[door1], '] (forced):', valid)

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
                    zone1 = door_zones[door1]

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
                        print('Connecting ', door1, '[', zone1, ': ', self.door_rooms[door1], '] (dead end):')

                elif len(hallways) > 0:
                    # Second, always connect any hallway zones (those with only two doors)
                    # Select a door in a dead end zone
                    hallwayDoors = [d for d in doors if door_zones[d] in hallways]

                    # Choose a random door
                    door1 = hallwayDoors.pop(randrange(len(hallwayDoors)))
                    doors.remove(door1)  # clean up
                    zone1 = door_zones[door1]

                    # Construct a list of valid zone connections:  Any zone that is not itself.
                    # Dead end zones would also be taboo but are impossible.
                    if len(doors) == 1:
                        # Edge case: connect the last two doors in the zone
                        valid = [d for d in doors]
                    else:
                        valid_zone2 = [zi for zi in range(len(zones)) if zi != zone1]
                        valid = [d for d in doors if door_zones[d] in valid_zone2]
                    if self.verbose:
                        print('Connecting ', door1, '[', zone1, ': ', self.door_rooms[door1], '] (hallway):')

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
                        zone1 = door_zones[door1]

                        if self.verbose:
                            print('Connecting ', door1, '[', zone1, ': ', self.door_rooms[door1], '] (single exit):')

                    elif len(one_entrs) > 0:
                        # Fourth, always connect any rooms with a single entrance
                        oneentryDoors = [d for d in doors if door_zones[d] in one_entrs]

                        # Choose a random door
                        door1 = oneentryDoors.pop(randrange(len(oneentryDoors)))
                        doors.remove(door1)  # clean up
                        zone1 = door_zones[door1]

                        if self.verbose:
                            print('Connecting ', door1, '[', zone1, ': ', self.door_rooms[door1], '] (single entry):')

                    else:
                        door1 = doors.pop(randrange(len(doors)))
                        zone1 = door_zones[door1]
                        if self.verbose:
                            print('Connecting ', door1, '[', zone1, ': ', self.door_rooms[door1], ']:')

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
                                        print('\t\t', d, '(', z2, ':', self.door_rooms[d], ') invalid from outside rule: ', outside_zones, ' --> ', outside_counts)

                            if zone1 == z2:
                                # Self connection will remove two entrances and two exits from the zone
                                if (z1_exits - 2 < 1) or (z1_enter - 2 < 1):
                                    # Creates a zone with no exit or no entrance
                                    invalid.append(d)
                                    if self.verbose:
                                        print('\t\t', d, '(', z2, ':', self.door_rooms[d], ') invalid from self rule: ', zone1, ' --> ', z1_exits, z1_enter)
                            else:
                                z2_exits = zone_counts[z2][0] + zone_counts[z2][1]
                                z2_enter = zone_counts[z2][0] + zone_counts[z2][2]
                                # Note that the connection will remove 1 door (=1 exit + 1 entrance) from each zone
                                if ((z1_exits + z2_exits) - 2 < 1) or ((z1_enter + z2_enter) - 2 < 1):
                                    # Creates a zone with no exit or no entrance
                                    invalid.append(d)
                                    if self.verbose:
                                        print('\t\t', d, '(', z2, ':', self.door_rooms[d], ') invalid: ', zone1, ' --> ', z1_exits, z1_enter, ', ', z2,
                                              ' --> ', z2_exits, z2_enter)

                    invalid = list(set(invalid))  # remove duplicates, if any.
                    for i in invalid:
                        valid.remove(i)

                # Make sure no invalid connections got through
                if door1 in self.invalid.keys():
                    #print('potentially invalid pair...', self.invalid[door1])
                    for d2 in self.invalid[door1]:
                        if d2 in valid:
                            if self.verbose:
                                print('\tBlocked door detected: ', door1, '<-/->', d2)
                            valid.remove(d2)

                if self.verbose:
                    print('\tValid connections: ')
                    for v in valid:
                        print('\t\t', v, '[', door_zones[v], ':', self.door_rooms[v], ']')

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
                    zone2 = door_zones[door2]
                    doors.remove(door2)
                    if self.verbose:
                        print('\tSelected:', door2)

                    # Write the connection
                    map.append([door1, door2])

                    # Modify the zones if necessary
                    if zone1 != zone2:
                        # Add zone1 to zone2
                        zones[zone2].extend(zones[zone1])
                        zones[zone1] = []

                        # Adjust counts
                        for i in range(len(zone_counts[zone2])):
                            zone_counts[zone2][i] += zone_counts[zone1][i]
                            zone_counts[zone1][i] = 0

                        # Update door_zone listing
                        for d in doors:
                            if door_zones[d] == zone1:
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
        if self.use_shared_exits:
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

    def map_oneways(self, areas='all'):
        # Generate lists of 1-way gates & reverse gate-->zone lookups
        if areas == 'all':
            areas = [a for a in range(len(self.rooms))]

        map = []
        for a in areas:
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

            zone_contents = {}
            for zi in range(len(zones)):
                zone_contents[zi] = [zi]

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
            to_share = [n for n in self.sharing.keys() if n in nobs]

            # Walk through all valid one-ways, connecting all zones and returning to the starting point
            walk = []
            if self.verbose:
                print('\nMapping Area',a,'one-way exits ... ')
            if len(nobs) > 0:

                if len(to_force) > 0:
                    # Connect all forced connections
                    while len(to_force) > 0:
                        # Create a new walk for this forced connection
                        this_walk = []

                        # Connect a forced nob ...
                        nob = to_force.pop(randrange(len(to_force)))
                        nobs.remove(nob)
                        zone1 = nob_zones[nob]
                        this_walk.append(zone1)  # record the path of the walk

                        # ... to its forced nib
                        available_nibs = [n for n in self.forcing[nob]]
                        nib = available_nibs.pop(randrange(len(available_nibs)))  # it's probably just len(1)...
                        nibs.remove(nib)
                        zone2 = nib_zones[nib]
                        if zone2 != zone1:
                            this_walk.append(zone2)

                        # Add this connection to the map
                        map.append([nob, nib])

                        # Add this walk to the walks
                        walk.append(this_walk)

                        # Adjust zone counts
                        zone_counts[zone1][1] -= 1  # remove an exit
                        zone_counts[zone2][2] -= 1  # remove an entrance

                        if self.verbose:
                            print('Created forced connection: ', nob, '[', zone1, '] --> ', nib, '[', zone2, ']')

                else:
                    # Just pick a random connection to start with
                    walk.append([randrange(len(zones))])

                # If any walks are connected, connect them
                w = 0
                while w < len(walk)-1:
                    zone_extends = [i for i in range(w, len(walk)) if walk[w][-1] == walk[i][0]]
                    if len(zone_extends) > 0:
                        if self.verbose:
                            print('Compacting walks: ', walk[w], ' --> ', walk[zone_extends[0]])
                        # add walk[zone_extends[0]] to the active walk
                        walk[w].extend(walk[zone_extends[0]][1:])
                        # remove walk[zone_extends[0]]
                        walk = walk[:zone_extends[0]] + walk[zone_extends[0] + 1:]
                    else:
                        w += 1

                if self.verbose:
                    print('Preprocessing complete.')

                # Begin the normal walk process
                # Construct the list of all downstream exits...
                available = [n for n in zone_nobs[walk[0][-1]] if n in nobs]
                # If any available are shared, do them first.
                available_shared = list(set(available).intersection(to_share))
                if len(available_shared) > 0:
                    nob = available_shared.pop(randrange(len(available_shared)))
                    if self.verbose:
                        print('From available shared: ', available_shared, ' choose: ', nob)
                else:
                    nob = available.pop(randrange(len(available)))
                    if self.verbose:
                        print('From available: ', available, ' choose: ', nob)
                nobs.remove(nob)
                zone1 = nob_zones[nob]

                while len(nibs) > 0:
                    if self.verbose:
                        print('\nZone state: ')
                        for z in range(len(zones)):
                            if len(zones[z]) > 0:
                                print(z, ': ', zones[z], ', ', zone_counts[z])
                        print('Walk state: ', walk)
                        print('Connecting: ', nob, '(', zone1, ':', self.door_rooms[nob], ')')

                    # Construct list of valid entrances: start with all nibs, then remove invalid ones
                    valid = [n for n in nibs]
                    invalid = []

                    is_shared = nob in self.sharing.keys()
                    if is_shared:
                        # This exit must share a destination with another exit (e.g. Umaro's cave #2 trapdoors)
                        #   shared[nob] = [nobs that must have the same exit]
                        to_share.remove(nob)  # clean up
                        shared = self.sharing[nob]

                        # Look to see if any have been assigned.
                        assigned = [n for n in shared if n not in nobs]
                        if len(assigned) > 0:
                            # Find the previously-assigned connection in the map; take the nib
                            mapped_nib = [m for m in map if assigned[0] == m[0]][0][1]
                            valid = [mapped_nib]
                            if self.verbose:
                                print('\tShared exit connection: ', valid)
                        else:
                            # Assign this one normally
                            if self.verbose:
                                is_shared = False
                                print('\tShared exit has not yet been connected.')

                    if len(nibs) > 1 and not is_shared:
                        # Remove doors that would create a zone with zero exits or zero entrances
                        # i.e. a zone with [0, n, 0], or [0, 0, n].
                        z1_exits = zone_counts[zone1][1]
                        z1_enter = zone_counts[zone1][2]

                        for n in valid:
                            z2 = nib_zones[n]

                            # Check if z2 is in any walk yet
                            z2_walked = [z2 in walk[i] for i in range(len(walk))]

                            if z2_walked[0]:  # the active walk
                                # Look for downstream exits from zone2 in the active walk
                                if self.verbose:
                                    print('\t\tTesting', n, '... ', '(', z2, ':', self.door_rooms[n], ') in the active walk')
                                # Search for a remaining downstream exit
                                z2i = walk[0].index(z2)
                                flag = False
                                for wi in range(z2i, len(walk[0])):
                                    if walk[0][wi] == zone1 and z1_exits > 1:
                                        if self.verbose:
                                            print('\t\t\tenough exits in the present zone!')
                                        flag = True
                                        break
                                    elif walk[0][wi] != zone1 and zone_counts[walk[0][wi]][1] > 0:
                                        if self.verbose:
                                            print('\t\t\tenough exits in zone', walk[0][wi])
                                        flag = True
                                        break
                                if not flag:
                                    # If no remaining downstream exit, remove this entrance
                                    invalid.append(n)
                                    if self.verbose:
                                        print('\tRemoving ', n, ' (zone ', z2, 'in walk, count: ',
                                              zone_counts[z2], '): no downstream exits!')

                                # Search for a remaining upstream entrance (including this zone)
                                z1i = walk[0].index(zone1)
                                flag2 = False
                                for wi in range(z1i+1):
                                    if walk[0][wi] == z2 and zone_counts[z2][2] > 1:
                                        if self.verbose:
                                            print('\t\t\tenough entrances in the connecting zone', walk[0][wi])
                                        flag2 = True
                                        break
                                    elif zone_counts[walk[0][wi]][2] > 0:
                                        if self.verbose:
                                            print('\t\t\tenough entrances in zone', walk[0][wi])
                                        flag2 = True
                                        break
                                if not flag2:
                                    # If no remaining downstream exit, remove this entrance
                                    invalid.append(n)
                                    if self.verbose:
                                        print('\tRemoving ', n, ' (zone ', z2, 'in walk, count: ',
                                              zone_counts[z2], '): no upstream entrances!')

                            elif z2_walked[1:].count(True):
                                # z2 is in some other walk.
                                # But any non-active walk has both exits and entrances by definition.
                                if self.verbose:
                                    print('\t', z2, 'is in walk ', z2_walked.index(True), 'and is probably ok.')

                            else:
                                # z2 isn't in a walk yet.  Verify that the connection would still have exits.
                                z2_exits = zone_counts[z2][1]
                                z2_enter = zone_counts[z2][2]
                                # Connection will remove 1 exit from zone1 and 1 entrance from zone2
                                if z2_exits < 1:
                                    # Connection would create a walk with no exits
                                    invalid.append(n)
                                    if self.verbose:
                                        print('\tRemoving ', n, ' (zone ', z2, 'not in walk, count: ',
                                              zone_counts[z2], ')')

                    invalid = list(set(invalid))  # remove any duplicates
                    if self.verbose:
                        print('Invalid connections found: ', invalid)
                    for i in invalid:
                        valid.remove(i)

                    # Select an entrance to connect:
                    nib = valid.pop(randrange(len(valid)))
                    zone2 = nib_zones[nib]
                    if nib in nibs:
                        nibs.remove(nib)
                        zone_counts[zone2][2] -= 1  # decrement entrances (nibs) in zone2
                    if self.verbose:
                        print('Selected entrance: ', nib, '[', zone2, ']')

                    # Write the connection
                    map.append([nob, nib])
                    zone_counts[zone1][1] -= 1  # decrement exits (nobs) in zone1

                    # Update the walk and zone counts
                    walk[0].append(zone2)

                    # Compactify the walks, if necessary
                    zone_extends = [i for i in range(1,len(walk)) if walk[i][0] == zone2]
                    if len(zone_extends) > 0:
                        # add walk[zone_extends[0]] to the active walk
                        walk[0].extend(walk[zone_extends[0]][1:])
                        # remove walk[zone_extends[0]]
                        walk = walk[:zone_extends[0]] + walk[zone_extends[0]+1:]

                    # If we created a loop, combine all zones in the loop into a new zone
                    # A loop is created when a zone appears a second time in the walk, and is always bookended by the
                    # last zone in the walk.
                    lastzone = walk[0][-1]
                    loop_found = False
                    loop_index = -1  # default value.
                    for z in walk[0][:-1]:
                        if lastzone in zone_contents[z]:
                            # if a loop is found, record the index and stop looking.
                            loop_found = True
                            loop_index = walk[0].index(z)
                            break
                    if loop_found:
                        # Check if the loop is just a self-loop (zone linking to itself)
                        if walk[0][-1] == walk[0][-2]:
                            # Self loop only, skip it.
                            walk[0] = walk[0][:-1]
                            if self.verbose:
                                print('\tSelf loop found (ignored)')

                        else:
                            # Collect the loop
                            loop = walk[0][loop_index:-1]

                            # Create a new zone with the properties of all the zones in the loop
                            # Gather information on the new zone
                            if self.verbose:
                                print('\tLoop found: zone', lastzone, 'at position', loop_index,'in: ', walk[0],' - Compressing')
                            newzone = []
                            newzone_count = [0, 0, 0]
                            newzone_nobs = []
                            newzone_nibs = []
                            newzone_contents = []
                            for zi in loop:
                                for zzi in zone_contents[zi]:
                                    newzone_contents.append(zzi)
                                newzone.extend(zones[zi])  # rooms in the zone
                                for j in range(3):
                                    newzone_count[j] += zone_counts[zi][j]
                                newzone_nobs.extend(zone_nobs[zi])
                                newzone_nibs.extend(zone_nibs[zi])
                                newzone = list(set(newzone)) # unique values only
                                # Delete old zone information
                                zones[zi] = []
                                zone_counts[zi] = [0, 0, 0]
                                zone_nobs[zi] = []
                                zone_nibs[zi] = []
                            nzi = len(zones)  # new zone index
                            newzone_contents = [nzi] + list(set(newzone_contents))  # unique values only
                            # Create the new zone
                            zones.append(newzone)
                            zone_counts.append(newzone_count)
                            zone_contents[nzi] = newzone_contents
                            zone_nobs[nzi] = newzone_nobs
                            # Update dictionaries for nob zones & nib zones
                            for n in zone_nobs[nzi]:
                                nob_zones[n] = nzi
                            zone_nibs[nzi] = newzone_nibs
                            for n in zone_nibs[nzi]:
                                nib_zones[n] = nzi
                            # Update walk to replace the loop with the new zone ID
                            walk[0] = walk[0][:loop_index]
                            walk[0].append(nzi)
                            lastzone = nzi
                            if self.verbose:
                                print('\tNew zone created:',nzi,':',newzone)

                    # Construct the list of all downstream exits...
                    z2i = walk[0].index(lastzone)
                    available = []
                    for wi in range(z2i, len(walk[0])):
                        available.extend([nob for nob in zone_nobs[walk[0][wi]] if nob in nobs])
                    # ... And randomly select one to connect:
                    available = list(set(available))  # just unique values
                    if self.verbose:
                        print('Available exits: ', available)
                    if len(nibs) > 0:
                        # prepare for the next loop
                        if len(available) > 0:
                            # If any available are shared, do them first.
                            available_shared = list(set(available).intersection(to_share))
                            if len(available_shared) > 0:
                                nob = available_shared.pop(randrange(len(available_shared)))
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
                # There's probably a forced or shared nob(s) that hasn't been connected.
                for nob in nobs:
                    print('Found a disconnected nob!', nob, '(to_share = ', to_share, ')')
                    assigned = []
                    if nob in to_share:
                        to_share.remove(nob)  # clean up
                        # Look for shared exits that have been assigned.
                        shared = self.sharing[nob]
                        assigned = [n for n in shared if n not in nobs]

                    if len(assigned) > 0:
                        # Find the previously-assigned connection in the map; take the nib
                        mapped_nib = [m for m in map if assigned[0] == m[0]][0][1]
                        map.append([nob, mapped_nib])
                        if self.verbose:
                            print('\tCleanup: forced or shared exit connection: ', nob, ' --> ', mapped_nib)

        return map

    def print(self):
        from log import SECTION_WIDTH, section, format_option
        lcolumn = []

        # Print state of the Doors object
        for a in range(len(self.rooms)):
            lcolumn.append('Area' + str(a) + ':')
            lcolumn.append('Doors:')
            for d in self.doors[a]:
                lcolumn.append(str(d) + ': Room = ' + str(self.door_rooms[d]) + '. ' + str(
                    self.door_descr[d]))  # ', Map = ', self.door_maps[d],
            lcolumn.append('Rooms:')
            for r in self.rooms[a]:
                lcolumn.append(str(r) + ': door count = ' + str(self.room_counts[r]) + '\n\t\tdoors: ' + str(
                    self.room_doors[r][0]) +
                               'one-way exits: ' + str(self.room_doors[r][1]) + '\n\t\t one-way entrances: ' + str(
                    self.room_doors[r][2]))
        lcolumn.append('Forced connections:')
        for d in self.forcing.keys():
            lcolumn.append(str(d) + ' --> ' + str(self.forcing[d]))
        if len(self.map) > 0:
            lcolumn.append('Map:')
            for m in self.map[0]:
                lcolumn.append(str(m[0]) + ' --> ' + str(m[1]) + '(' + str(self.door_descr[m[0]]) + ' --> ' + str(
                    self.door_descr[m[1]]) + ')')
            for m in self.map[1]:
                lcolumn.append(str(m[0]) + ' --> ' + str(m[1]) + '(' + str(self.door_descr[m[0]]) + ' --> ' + str(
                    self.door_descr[m[1]]) + ')')

        section("Door Rando: ", lcolumn, [])
