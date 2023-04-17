from data.rooms import room_data
import networkx as nx

class Walks:
    # Class for handling a group of Walks, i.e. logical mapping sequences for rooms
    def __init__(self, rooms):
        self.walks = []
        self.deadends = []
        #self.room_doors = room_doors    # dictionary for [ [doors], [traps], [pits], [keys], [locks] ] in each room
        #self.room_counts = room_counts  # count of [ doors, traps, pits, keys, locks ] in each room
        for r in rooms:
            R = Room(r)
            if R.is_dead_end():
                self.deadends.append(R)
            else:
                self.walks.append(Walk([R]))

        self.active = 0  # Index of the active walk

    @property
    def count(self):
        # Return the number of unused [doors, traps, pits, keys, locks] in the walk
        count = [0, 0, 0, 0, 0]
        for w in self.walks:
            w_count = w.count
            for i in range(len(count)):
                count[i] += w_count[i]
        return count

    def ForceConnections(self, forcing):
        # Look up forced connections for doors and connect them
        map = []
        for w in self.walks:
            for d in w.doors:
                if d in forcing.keys():
                    df = forcing[d]  # get forced connection ID
                    self.connect(d, df)
                    map.append([d, df])
        return map

    def connect(self, d1, d2):
        # Connect two doors & handle updates to the walks
        w1 = self.get_walk(d1)
        w2 = self.get_walk(d2)

        # Find rooms and remove the doors
        r1 = w1.get_room(d1)
        r2 = w2.get_room(d2)
        r1.remove(d1)
        r2.remove(d2)

        if w1 == w2:
            # Both doors are in the same walk. Combine all rooms in the walk between r1 and r2 into a new room
            w1.compress_loop(r1, r2)

        else:
            # Doors are in different walks.  By default, can only enter a new walk at the first node.
            # Add the new walk (w2) onto the end of this one (w1) & delete the other copy
            for r in w2.walk:
                w1.walk.append(r)

            # Delete w2
            self.walks.remove(w2)

    def get_walk(self, id):
        # Return the walk containing an object
        for w in self.walks:
            if w.get_room(id) is not False:
                return w
        return False


class Walk:
    # Class for handling a logical mapping sequence for Rooms
    def __init__(self, rooms):
        self.walk = []
        for r in rooms:
            self.walk.append(r)

    @property
    def count(self):
        # Return the count of unused [doors, traps, pits, keys, locks] in this walk
        return [len(self.doors), len(self.traps), len(self.pits), len(self.keys), len(self.locks)]

    @property
    def doors(self):
        # List of doors in the walk
        doors = []
        for r in self.walk:
            doors.extend(r.doors)
        return doors

    @property
    def traps(self):
        # List of traps in the walk
        traps = []
        for r in self.walk:
            traps.extend(r.traps)
        return traps

    @property
    def pits(self):
        # List of pits in the walk
        pits = []
        for r in self.walk:
            pits.extend(r.pits)
        return pits

    @property
    def keys(self):
        # List of keys in the walk
        keys = []
        for r in self.walk:
            keys.extend(r.keys)
        return keys

    @property
    def locks(self):
        # List of locks in the walk
        locks = []
        for r in self.walk:
            locks.append(r.locks.keys())
        return locks

    @property
    def locked(self):
        # List of locked exits in the walk
        locked = []
        for r in self.walk:
            locked.append(r.locks.values())
        return locked

    def remove(self, id):
        for room in self.walk:
            if room.remove(id):
                return True
        return False

    def get_room(self, id):
        for room in self.walk:
            if room.contains(id):
                return room
        return False

    def compress_loop(self, room1, room2):
        # Compress a loop containing two rooms
        # Note: the active connection should be removed from the room before compressing.
        inds = [self.walk.index(room1), self.walk.index(room2)]
        inds.sort()  # this shouldn't matter, but doesn't hurt
        looproom = Room()
        looproom.id = ''
        for r in self.walk[inds[0]:inds[1]+1]:
            looproom.id += str(r.id) + '_'
            looproom.doors.extend(r.doors)
            looproom.traps.extend(r.traps)
            looproom.pits.extend(r.pits)
            looproom.keys.extend(r.keys)
            for k in r.locks.keys():
                looproom.locks[k] = r.locks[k]
        self.walk = self.walk[:inds[0]] + [looproom] + self.walk[inds[1]+1:]

    def get_upstream_entr_count(self):
        pass

    def get_upstream_exit_count(self):
        pass


class Rooms():
    def __init__(self, rooms):
        self.rooms = []
        for r in rooms:
            self.rooms.append(Room(r))

    def get_room(self, id):
        for room in self.rooms:
            if room.id == id:
                return room
            elif room.contains(id):
                return room
        return False

    @property
    def count(self):
        # Return the count of unused [doors, traps, pits, keys, locks] in this walk
        return [len(self.doors), len(self.traps), len(self.pits), len(self.keys), len(self.locks)]

    @property
    def doors(self):
        # List of doors in the walk
        doors = []
        for r in self.rooms:
            doors.extend(r.doors)
        return doors

    @property
    def traps(self):
        # List of traps in the walk
        traps = []
        for r in self.rooms:
            traps.extend(r.traps)
        return traps

    @property
    def pits(self):
        # List of pits in the walk
        pits = []
        for r in self.rooms:
            pits.extend(r.pits)
        return pits

    @property
    def keys(self):
        # List of keys in the walk
        keys = []
        for r in self.rooms:
            keys.extend(r.keys)
        return keys

    @property
    def locks(self):
        # List of locks in the walk
        locks = []
        for r in self.rooms:
            locks.append(r.locks.keys())
        return locks

    @property
    def locked(self):
        # List of locked exits in the walk
        locked = []
        for r in self.rooms:
            locked.append(r.locks.values())
        return locked

    def remove(self, door_id):
        for room in self.rooms:
            if room.remove(door_id):
                return True
        return False


class Room():
    def __init__(self, r=None):
        self.id = r
        if r is not None:
            if len(room_data[r]) == 4:
                # before implementing keys & locks
                contents = room_data[r][:-1] + [[], {}]
            else:
                contents = room_data[r][:-1]   # [ doors, traps, pits, keys, locks ]
            self._contents = [i for i in contents]  # Copy, don't replicate

        else:
            self._contents = [ [], [], [], [], {}]

    @property
    def doors(self):
        return self._contents[0]

    @property
    def traps(self):
        return self._contents[1]

    @property
    def pits(self):
        return self._contents[2]

    @property
    def keys(self):
        return self._contents[3]

    @property
    def locks(self):
        return self._contents[4]

    @property
    def count(self):
        return [len(s) for s in self._contents]

    def remove(self, id):
        for r in range(len(self._contents)):
            if id in self._contents[r]:
                self._contents[r].remove(id)
                self.count[r] -= 1
                return True
        return False

    def contains(self, id):
        if id in self.doors:
            return True
        elif id in self.traps:
            return True
        elif id in self.pits:
            return True
        elif id in self.keys:
            return True
        elif id in self.locks.values():
            return True
        else:
            return False

    def is_dead_end(self):
        rc = self.count
        return rc[:3] == [1, 0, 0] and rc[4] == 0

    def element_type(self, e_id):
        return [e_id in self.doors, e_id in self.traps, e_id in self.pits, e_id in self.keys, e_id in self.locks.keys(), e_id in self.locks.values()].index(True)

    def get_elements(self, node_list, element_type):
        if element_type == 0:
            return self.doors
        elif element_type == 1:
            return self.traps
        elif element_type == 2:
            return self.pits
        elif element_type == 3:
            return self.keys
        elif element_type == 4:
            return self.locks.keys()
        elif element_type == 5:
            return self.locks.values()
        else:
            return False


class Network:
    def __init__(self, rooms):
        self.rooms = Rooms(rooms)
        self.net = nx.DiGraph()
        self.net.add_nodes_from(self.rooms.rooms)
        self.map = []

        self.active = 0  # index of active room

    def ForceConnections(self, forcing):
        # Look up forced connections for doors and connect them
        these_doors = self.rooms.doors + self.rooms.traps
        for d in forcing.keys():
            if d in these_doors:
                df = forcing[d][0]  # get forced connection ID
                self.connect(d, df)
                self.map.append([d, df])

    def connect(self, d1, d2):
        R1 = self.rooms.get_room(d1)
        R2 = self.rooms.get_room(d2)
        self.net.add_edge(R1, R2)
        R1.remove(d1)
        R2.remove(d2)

    def get_upstream_nodes(self, room, nodes=None):
        if nodes is None:
            nodes = []
        pred = [p for p in self.net.predecessors(room) if p not in nodes]
        if len(pred) > 0:
            for p in pred:
                if room not in list(self.net.predecessors(p)):
                    # Ignore simple 2-way doors
                    nodes.append(p)
                nodes.extend(self.get_upstream_nodes(p, nodes))
        return nodes

    def get_downstream_nodes(self, room, nodes=None):
        if nodes is None:
            nodes = []
        succ = [s for s in self.net.successors(room) if s not in nodes]
        if len(succ) > 0:
            for s in succ:
                if room not in list(self.net.successors(s)):
                    # Don't include simple 2-way doors
                    nodes.append(s)
                nodes.extend(self.get_downstream_nodes(s, nodes))
        return nodes

    def get_connected_nodes(self, room, nodes=None):
        if nodes is None:
            nodes = []
            is_original = True
        conn = [c for c in self.net.successors(room) if c in self.net.predecessors(room) and c not in nodes]
        if len(conn) > 0:
            for c in conn:
                nodes.append(c)
                nodes.extend(self.get_connected_nodes(c, nodes))
        if is_original and room in nodes:
            # Remove room from the connected nodes
            nodes.remove(room)
        return nodes

    def get_elements(self, node_list, element_type):
        elements = []
        for R in node_list:
            elements.extend(R.get_elements(element_type))
        return elements

    def get_valid_connections(self, d1):
        # Return a list of valid connections for the door or trap d1
        R1 = self.rooms.get_room(d1)
        d1_type = R1.element_type(d1)
        if d1_type == 0:
            d2_type = 0
        elif d1_type == 1:
            d2_type = 2

        upstream_nodes = self.get_upstream_nodes(R1)
        downstream_nodes = self.get_downstream_nodes(R1)
        connected_nodes = self.get_connected_nodes(R1)
        # Only connect loose nodes if they have no predecessors
        unconnected_nodes = [r for r in self.rooms.rooms if r not in upstream_nodes and
                             r not in downstream_nodes and r is not R1 and
                             len(list(self.net.predecessors(r))) == 0]
        loose_conn = [l for l in self.get_elements(unconnected_nodes, d2_type)]  # available connections in new nodes

        # (2) Do not create a loop with no exits while there remain entrances
        if R1 in upstream_nodes:
            # inspect the loop for other exits
            loop = upstream_nodes[upstream_nodes.index(R1):] + downstream_nodes
            doors_out = [d for d in self.get_elements(loop, 0) if d is not d1]
            traps_out = [t for t in self.get_elements(loop, 1) if t is not d1]

            if len(doors_out) + len(traps_out) == 0:
                # Remove the loop connections:
                upstream_nodes = upstream_nodes[:upstream_nodes.index(R1)]

        upstream_conn = [u for u in self.get_elements(upstream_nodes, d2_type)]
        downstream_conn = [d for d in self.get_elements(downstream_nodes, d2_type)]
        self_conn = [id for id in R1.get_elements(d2_type) if id is not d1]

        valid = [u for u in loose_conn]   # always include unconnected nodes
        # Validity rules:
        # (1) Do not complete this loop while there remain disconnected nodes
        if len(upstream_conn + downstream_conn + self_conn) > 1 and len(loose_conn) == 0:
            pass




        # We can check for loops by seeing if R1 is in its own upstream_nodes (or downstream_nodes)

