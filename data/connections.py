from data.map_exit_extra import exit_data, exit_data_patch
from data.rooms import room_data, exit_world

# Construct DOOR_ROOMS lookup from room_doors:
DOOR_ROOMS = {}
for r in room_data.keys():
    for d in room_data[r]:
        DOOR_ROOMS[d] = r

# NOTES:
# To be comprehensive, we should treat this the same way we treat exits:
#   - load all vanilla connections from the ROM at initialization
#   - Make any modifications in mod()
#   - write all connections at the end (just before writing exits, presumably, since this acts on exits, not the ROM)
# This will be a little tricky because:
#   - changing one connection shouldn't leave a 'hanging' connection.  Will have to be careful about this.
#       just double up on connections for doors? might be smart. in-->out for every possible in.  Only change outs.
#   - have to document world & event data somewhere.
#       - can look for event tiles directly
#       - world bit is metadata: currently included in room_data, but that's not single-valued.
#           - TO DO: ADD WORLD DATA FOR EVERY ROOM!
#           - not being single valued doesn't matter for this: doubled-up rooms never change worlds.

class Connections:
    connections = []
    door_rooms = {}

    def __init__(self, mapping, door_rooms):
        # For all doors in doors.map[0], we want to find the exit and change where it leads to
        # Create sorted map, so they are connected in order:
        self.door_rooms = door_rooms
        map = {}
        for m in mapping:
            if m[0] not in map.keys():
                map[m[0]] = m[1]
            if m[1] not in map.keys():
                map[m[1]] = m[0]

        temp = [m for m in map.keys() if m + 4000 in exit_data.keys() and m + 4000 not in map.keys()]
        for m in temp:
            # Add logical WoR exits to the map (with vanilla connections)
            map[m + 4000] = exit_data[m + 4000][0]
            map[map[m + 4000]] = m + 4000

            # Look up the rooms of these exits
            this_room = [r for r in room_data.keys() if (m + 4000) in room_data[r][0]]
            self.door_rooms[m + 4000] = this_room[0]
            that_room = [r for r in room_data.keys() if map[m + 4000] in room_data[r][0]]
            self.door_rooms[map[m + 4000]] = that_room[0]

        # Need to add modified world map exits if they weren't randomized (to print exit events)
        for m in exit_data_patch.keys():
            if m not in map.keys():
                map[m] = exit_data[m][0]

                # Look up the rooms of these exits
                this_room = [r for r in room_data.keys() if m in room_data[r][0]]
                self.door_rooms[m] = this_room[0]
                that_room = [r for r in room_data.keys() if map[m] in room_data[r][0]]
                self.door_rooms[map[m]] = that_room[0]

        all_exits = list(map.keys())
        all_exits.sort()

    def mod(self):
        pass

    def write(self):
        pass


class Connection:
    def __init__(self, pair, exits):
        size = [exits.exit_type[p] for p in pair]
        self.exit = Exit(pair[0], exit_world[pair[0]], size[0])
        self.entr = Exit(pair[1], exit_world[pair[1]], size[1])

    def write(self):
        pass

    def makeConnectionEvent(self):
        pass


class Exit:
    ind = -1            # index of exit
    world = -1          # which world is it in
    #event = -1          # does it have an exit event? (event data?)
    size = ''           # 'short'/'long'

    def __init__(self, ind, world, size):
        self.ind = ind
        self.world = world
        self.size = size