from data.rooms import room_data, shared_exits
import networkx as nx
import random
from copy import deepcopy
import numpy as np

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
        r1 = w1.get_room_from_element(d1)
        r2 = w2.get_room_from_element(d2)
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
        return False

    def get_room_from_element(self, id):
        for room in self.rooms:
            if room.contains(id):
                return room
        return False

    @property
    def count(self):
        # Return the count of unused [doors, traps, pits, keys, locks] in this walk
        return [len(self.doors), len(self.traps), len(self.pits), len(self.keys), sum([len(r.locks) for r in self.rooms])]

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

    def remove(self, id):
        for room in self.rooms:
            if room.id == id:
                # This is a room id.  Remove it.
                self.rooms.remove(room)
                return True
            # If this is an exit id, remove it.
            if room.remove(id):
                return True
        return False


class Room():
    def __init__(self, r=None):
        self.id = r
        if r is not None:
            data = room_data[r]
            if len(data) == 4:
                # before implementing keys & locks
                contents = [i for i in data[:-1]] + [[], {}]
            else:
                contents = [i for i in data[:-1]]   # [ doors, traps, pits, keys, locks ]
            self._contents = deepcopy(contents)  # Copy, don't replicate

            # Adjust shared exits:
            d_shared = [d for d in self.doors if d in shared_exits.keys()]
            for d in d_shared:
                for s in shared_exits[d]:
                    self.remove(s)

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

    def add_doors(self, doors):
        self._contents[0].extend(doors)

    def add_traps(self, traps):
        self._contents[1].extend(traps)

    def add_pits(self, pits):
        self._contents[2].extend(pits)

    def add_keys(self, keys):
        self._contents[3].extend(keys)

    def add_locks(self, lock_dict):
        for k in lock_dict.keys():
            self._contents[4][k] = lock_dict[k]

    def locked(self, elementtype=None):
        if elementtype is None:
            return self._contents[4].values()
        elif elementtype in ['doors', 0]:
            locked = [d for d in self._contents[4].values() if type(d) is int]
            return [d for d in locked if d < 2000]
        elif elementtype in ['traps', 1]:
            locked = [d for d in self._contents[4].values() if type(d) is int]
            return [d for d in locked if 2000 <= d < 3000]
        elif elementtype in ['pits', 2]:
            locked = [d for d in self._contents[4].values() if type(d) is int]
            return [d for d in locked if 3000 <= d]
        elif elementtype in ['keys', 3]:
            return [d for d in self._contents[4].values() if type(d) is str]
        else:
            return False

    def remove(self, id):
        for r in range(len(self._contents)):
            if id in self._contents[r]:
                self._contents[r].remove(id)
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

    def element_type(self, e_id):
        is_element = [e_id in self.doors, e_id in self.traps, e_id in self.pits, e_id in self.keys, e_id in self.locks.keys(), e_id in self.locks.values()]
        if True in is_element:
            return is_element.index(True)
        else:
            print('ERROR: ', e_id, 'is not in ', self.id,': ', self._contents)
            raise Exception('Missing Element')

    def get_elements(self, element_type):
        if element_type in [0, 'doors']:
            return self.doors
        elif element_type in [1, 'traps']:
            return self.traps
        elif element_type in [2, 'pits']:
            return self.pits
        elif element_type in [3, 'keys']:
            return self.keys
        elif element_type in [4, 'locks']:
            return self.locks.keys()
        elif element_type in [5, 'locked']:
            return self.locks.values()
        else:
            return False

    def get_key(self, locked_element):
        for k, l in self.locks:
            if locked_element in l:
                return k

    def get_exit(self):
        # Return a random exit from those available
        exit_list = self.doors + self.traps
        return random.choice(exit_list)

    def is_attachable(self):
        # A room is attachable to a dead end room if it has 2 doors or 1 door and at least 1 pit AND 1 trap.
        # These can include locked values.
        all_doors = self.doors + self.locked('doors')
        all_traps = self.traps + self.locked('traps')
        all_pits = self.pits + self.locked('pits')
        return (len(all_doors) > 1) or (len(all_doors) == 1 and len(all_traps) > 0 and len(all_pits) > 0)


class Network:
    verbose = True

    def __init__(self, rooms):
        self.original_room_ids = [r for r in rooms]
        self.rooms = Rooms(rooms)
        self.net = nx.DiGraph()
        self.net.add_nodes_from(self.rooms.rooms)
        self.map = [[], []]

        self.active = 0  # index of active room

    def ForceConnections(self, forcing):
        # Look up forced connections for doors and connect them
        these_doors = self.rooms.doors + self.rooms.traps
        for d in forcing.keys():
            if d in these_doors:
                df = forcing[d][0]  # get forced connection ID
                self.connect(d, df)

    def connect(self, d1, d2, state=None):
        # (0) Create directed connection: d1 --> d2
        R1 = self.rooms.get_room_from_element(d1)
        R2 = self.rooms.get_room_from_element(d2)
        if R1 is not R2:
            # Add the edge connecting R1 --> R2
            self.net.add_edge(R1, R2)
            if R1.element_type(d1) == 0:
                # This is a normal door: add the reverse connection R2 --> R1
                self.net.add_edge(R2, R1)
        # Add to the network map
        if R1.element_type(d1) == 0:
            self.map[0].append([d1, d2])
        else:
            self.map[1].append([d1, d2])
        # (1) Remove the doors from their respective rooms
        R1.remove(d1)
        R2.remove(d2)

        # Update the state of the network if desired:
        if state != 'static':
            # (2) Compress any loops
            loop = self.get_loop(R1)
            if loop:
                # Compress the node, update the active room
                loop_room = self.compress_loop(loop)

            # (3) Apply any keys in R2:
            for k in R2.keys:
                self.apply_key(k)

            # (4) Update the active room
            if loop:
                self.active = self.rooms.rooms.index(loop_room)
            else:
                self.active = self.rooms.rooms.index(R2)

    def apply_key(self, key):
        # unlock any doors or traps locked by key
        for room in self.rooms.rooms:
            if key in room.locks.keys():
                if self.verbose:
                    print('Applying key:', key, 'in room', room.id)
                locked = room.locks.pop(key)  # this also removes the item from room.locks
                for item in locked:
                    if type(item) is str:
                        # This is a key.  Immediately apply it.
                        self.apply_key(item)
                    elif item < 2000:
                        room.add_doors([item])
                    else:
                        room.add_traps([item])
            # Delete the key, we already have it.
            if key in room.keys:
                room.remove(key)

    def get_loop(self, room):
        # Look for a loop containing this room.  If found, return [list of nodes in loop]; if not, return [].
        paths = self.get_upstream_paths(room)
        is_loop = [path.__contains__(room) for path in paths]
        if True in is_loop:
            loop = paths[is_loop.index(True)]  # returns the first loop found
            loop = loop[:loop.index(room)+1]  # return only the looping part; not any subsequent bits
            return loop
        else:
            return []

    def compress_loop(self, loop):
        # compress a loop = [list of nodes].  All nodes must be accessible from all other nodes: it is not checked here.
        if len(loop) > 1:
            r_id = ''
            for node in loop:
                r_id += str(node.id) + '_'
            r_id = r_id[:-1]  # Remove trailing '_'
            new_room = Room()
            new_room.id = r_id
            for node in loop:
                new_room.add_doors([d for d in node.doors])
                new_room.add_traps([t for t in node.traps])
                new_room.add_pits([p for p in node.pits])
                new_room.add_keys([k for k in node.keys])
                new_room.add_locks(node.locks)

            # Add new_room to the network
            self.rooms.rooms.append(new_room)
            self.net.add_node(new_room)

            # Inherit edges from all nodes to/from new node
            current_edges = [e for e in self.net.edges]
            for e in current_edges:
                if e[0] in loop and e[1] not in loop:
                    self.net.add_edge(new_room, e[1])
                elif e[0] not in loop and e[1] in loop:
                    self.net.add_edge(e[0], new_room)
                else:
                    pass

            # Delete loop nodes from network
            for node in loop:
                self.net.remove_node(node)  # remove from the network
                self.rooms.remove(node.id)  # remove from the list of rooms

            # If successful, return the room
            return new_room

        # If no loop is given, return false
        else:
            return False

    def flatten_paths(self, paths):
        temp = []
        for p in paths:
            if len(p) == 0:
                pass
            elif isinstance(p[0], list):
                temp.extend(self.flatten_paths(p))
            else:
                temp.append(p)
        return temp

    def get_upstream_paths(self, room, nodes=None):
        # Return a list of each branching path heading upstream from room until it hits a dead end.
        if nodes is None:
            nodes = []
        pred = [p for p in self.net.predecessors(room) if p not in nodes]
        if len(pred) > 0:
            if len(pred) == 1:
                p = pred[0]
                #if room in list(self.net.predecessors(p)):
                #    # Ignore simple 2-way doors
                #    return self.get_upstream_paths(p, nodes)
                #else:
                return self.get_upstream_paths(p, nodes + [p])
            else:
                temp = []
                for p in pred:
                    #if room in list(self.net.predecessors(p)):
                    #    # Ignore simple 2-way doors
                    #    temp.append(self.get_upstream_paths(p, nodes))
                    #else:
                    temp.append(self.get_upstream_paths(p, nodes + [p]))
                return self.flatten_paths(temp)
        return self.flatten_paths([nodes])

    def get_upstream_nodes(self, room, nodes=None):
        if nodes is None:
            nodes = []
        pred = [p for p in self.net.predecessors(room) if p not in nodes]
        if len(pred) > 0:
            temp = []
            for p in pred:
                if room in list(self.net.predecessors(p)):
                    # Ignore simple 2-way doors
                    temp += self.get_upstream_nodes(p, nodes)
                else:
                    temp += self.get_upstream_nodes(p, nodes + [p])
            return temp
        return nodes

    def get_downstream_nodes(self, room, nodes=None):
        if nodes is None:
            nodes = []
        succ = [s for s in self.net.successors(room) if s not in nodes]
        if len(succ) > 0:
            temp = []
            for s in succ:
                if room in list(self.net.successors(s)):
                    # Ignore simple 2-way doors
                    temp += self.get_downstream_nodes(s, nodes)
                else:
                    temp += self.get_downstream_nodes(s, nodes + [s])
            return temp
        return nodes

    def get_elements(self, node_list, element_type):
        elements = []
        for R in node_list:
            elements.extend(R.get_elements(element_type))
        return elements

    def get_top_nodes(self):
        top_nodes = set([])
        for n in self.net.nodes:
            paths = self.get_upstream_paths(n)
            for path in paths:
                # Add the ultimate node to the set
                top_nodes.add(path[-1])
        return top_nodes

    def attach_dead_ends(self):
        # Attach all dead-end rooms to open connections
        dead_ends = [n for n in self.net.nodes if self.is_dead_end(n)]
        if self.verbose:
            print("Attaching dead ends: ", [(e.id, e.doors[0]) for e in dead_ends])

        while len(dead_ends) > 0:
            if self.rooms.count[0] == 2:
                # These are the last two doors. Just connect them.
                R1 = dead_ends.pop()
                attachable_doors = [R1.doors[0]]
            else:
                attachable_doors = []
                for n in self.net.nodes:
                    if n.is_attachable():
                        attachable_doors.extend([d for d in n.doors + n.locked('doors')])
                if self.verbose:
                    print("found attachable doors: ", attachable_doors)
                random.shuffle(dead_ends)
                random.shuffle(attachable_doors)

            for Rd in dead_ends:
                if len(attachable_doors) > 0:
                    # select a door
                    dd = Rd.doors[0]
                    # select an attachable node
                    da = attachable_doors.pop(0)
                    Ra = self.rooms.get_room_from_element(da)

                    # Verify the dead end doesn't contain the key to unlock this door
                    while len(Rd.keys) > 0 and da in Ra.locked('doors'):
                        ka = Ra.get_key(da)
                        if ka in Ra.keys:
                            # ERROR don't connect it!
                            if self.verbose:
                                print('\t\tCannot connect ' + str(dd) + ' to ' + str(da) + ': ')
                                print('\t\t' + str(da) + ' is locked by key ' + str(ka) + ' which is in ' + str(Rd.id) + '!')
                            attachable_doors.append(da)  # put the door back
                            da = attachable_doors.pop(0) # get another
                            Ra = self.rooms.get_room_from_element(da) # check again

                    # Attach the doors
                    if self.verbose:
                        print('\tConnecting: ' + str(dd) + '(' + str(Rd.id) + ') to ' + str(da) + '(' + str(Ra.id) + ')')
                    self.connect(dd, da, 'static')

                    # If there were any keys in the dead end, add them to the connected room
                    if da in Ra.locked('doors'):
                        # If we connected to a locked door, add the key to the locked items
                        ka = Ra.get_key(da)
                        for kd in Rd.keys:
                            if self.verbose:
                                print('\t\tMoving key' + str(kd) + ' to room ' + str(Ra.id) + ' behind lock ' + str(ka))
                            Ra.locks[ka].append(kd)
                    elif len(Rd.keys) > 0:
                        if self.verbose:
                            print('\t\tMoving keys to room ' + str(Ra.id) + ': ', Rd.keys)
                        Ra.add_keys([k for k in Rd.keys])

                    # Add the dead room name to the attached room
                    Ra.id = str(Ra.id) + '_' + str(Rd.id)

                    # Remove the dead room from the network and list of rooms
                    self.net.remove_node(Rd)
                    self.rooms.remove(Rd.id)

                    # Check to see if the attached room is still attachable.
                    if not Ra.is_attachable():
                        # If not, remove any remaining doors.
                        more_doors = [d for d in Ra.doors + Ra.locked('doors')]
                        if self.verbose:
                            print('\t' + str(Ra.id) + ' is no longer attachable. Removing doors:', more_doors)
                        for d in more_doors:
                            attachable_doors.remove(d)

                else:
                    # If no attachable doors, just end.  It'll probably get straightened out in the walk.
                    return

            # having attached all the dead ends, see if we created any & attach them if we did.
            dead_ends = [n for n in self.net.nodes if self.is_dead_end(n)]
            if len(dead_ends) > 0 and self.verbose:
                print("Attaching dead ends: ", [(e.id, e.doors[0]) for e in dead_ends])

    def check_network_invalidity(self):
        # Check the network validity based on the following three validity rules:
        # [A] not [(Door in / trap out) and (Pit in / door out)] and (Door in / door out) and (Pit in / trap out)
        #     = not "Network Bifurcation"
        # If returns True, network is invalid
        ## [B] not (Door out) and (Door in / trap out). May be impossible.
        ## [C] not (Trap out) and (Pit in / door out).  May be impossible.

        classifications = {}
        total_doors_in = 0
        total_doors_out = 0
        total_doors_either = 0
        for node in self.net.nodes:
            # Count entrances & exits
            self_count = node.count[:3]
            up_count = np.array([0, 0, 0])
            for up in self.get_upstream_nodes(node):
                up_count += up.count[:3]
            down_count = np.array([0, 0, 0])
            for down in self.get_downstream_nodes(node):
                down_count += down.count[:3]

            # Assess classifications
            door_in = (up_count[0] + self_count[0]) > 0
            door_out = (down_count[0] + self_count[0]) > 0
            # Handle special case (avoid double counting self exits)
            door_in_door_out = (door_in and down_count[0] > 0) or (door_out and up_count[0] > 0) or (self_count[0] > 1)
            pit_in = (up_count[2] + self_count[2]) > 0
            trap_out = (down_count[1] + self_count[1]) > 0

            # Count total doors in/out OF THIS NODE
            #total_doors_in += up_count[0]
            #total_doors_out += down_count[0]
            delta_in = 0
            delta_out = 0
            delta_either = 0
            if self_count == [2, 0, 0] and sum(up_count + down_count) == 0:
                # Special case: hallways always have 1 entrance and 1 exit.
                delta_in += 1
                delta_out += 1
            elif self_count[0] > 1:
                # all self doors count as both doors in and doors out.
                delta_either += self_count[0]
            elif self_count[0] == 1:
                # self door may not be either a door in or a door out.
                is_out = up_count[0] + up_count[2] + self_count[2] > 0    # pits or doors in: it's a door out
                is_in = down_count[0] + down_count[1] + self_count[1] > 0 # doors or traps out: it's a door in
                if is_out and is_in:
                    delta_either += self_count[0]
                elif is_out:
                    delta_out += self_count[0]
                elif is_in:
                    delta_in += self_count[0]
            total_doors_in += delta_in
            total_doors_out += delta_out
            total_doors_either += delta_either

            # For each node: [(door in, door out), (door in, trap out), (pit in, door out), (pit in, trap out)]
            classifications[node] = [door_in_door_out, door_in and trap_out, pit_in and door_out, pit_in and trap_out,
                                     [list(up_count), self_count, list(down_count)],
                                     [delta_in, delta_out, delta_either]]

        # Assess logical parameters
        DiDo = [cl[0] for cl in classifications.values()].count(True) > 0
        DiTo = [cl[1] for cl in classifications.values()].count(True) > 0
        PiDo = [cl[2] for cl in classifications.values()].count(True) > 0
        PiTo = [cl[3] for cl in classifications.values()].count(True) > 0
        Rule_A = not (DiTo and PiDo) and DiDo and PiTo
        Rule_B = DiTo and not PiDo
        Rule_C = PiDo and not DiTo
        Rule_D = (total_doors_in + total_doors_either < total_doors_out) or \
                 (total_doors_out + total_doors_either < total_doors_in)
        return [
            Rule_A or Rule_B or Rule_C or Rule_D,
            [Rule_A, Rule_B, Rule_C, Rule_D],
            [DiDo, DiTo, PiDo, PiTo],
            classifications,
            [total_doors_in, total_doors_out, total_doors_either]
        ]

    def connect_network_stupid(self):
        # The rules for how to validly connect the network are too hard to figure out.
        # However, it's relatively easy to figure out when the network is invalid.
        # So: let's make a recursive connection algorithm that throws an error if it is invalid, and tries again at the
        # next step up.  This is like solving a maze by retreating to the most recent fork if you find a dead end.
        # Update: THIS ACTUALLY WORKS.  It can also occasionally take forever.
        # We might be able to make it more reliable by adding a *few* rules.
        # 1. Dead ends make this approach take a long time.  Solutions:
        # *** reimplement "connect all dead ends first" procedure
        # 2. Something else is also making this code take a long time.  Needs addl testing...
        # --- Minimum broken example: -dru -drem -drbh produced 300 MB+ output file on first try, ran instantly on 2,3.
        # --- I think this has to do with making a sub-net that has no door (trap) exits, and excluded nodes that
        # have no door (pit) entrances, and then it has to try all permutations of the subnet before escaping.
        # *** Can we avoid this by disallowing choice of an exit that results in no connections of the other type, if
        # connections of the other type still exist?
        net_state = deepcopy(self)

        if sum(net_state.rooms.count[:3]) == 0:
            # Successfully completed the network.
            return net_state

        else:
            [invalidity, by_rules, classification, cl, td] = net_state.check_network_invalidity()
            if self.verbose:
                print('Network classification: ', classification)
            if invalidity:
                # If network state is invalid, fail now.
                if self.verbose:
                    print('\tInvalid!  By rule: ', [['A','B','C','D'][i] for i in range(len(by_rules)) if by_rules[i]],
                          'in/out/either = ', td)
                raise Exception('Invalid network state.')

            R_active = net_state.rooms.rooms[net_state.active]
            if self.verbose:
                print('Active node: ', R_active.id)
            # Collect possible exits
            possible_exits = [[d for d in R_active.doors], [t for t in R_active.traps]]
            if self.verbose:
                print('Possible exits: ')
                print('\t' + str(R_active.id) + ': ', possible_exits, ' - (', cl[R_active], ')')
            for node in net_state.get_downstream_nodes(R_active):
                node_exits = [[d for d in node.doors], [t for t in node.traps]]
                if self.verbose:
                    print('\t' + str(node.id) + ': ', node_exits, ' - (', cl[node], ')')
                possible_exits[0] += node_exits[0]
                possible_exits[1] += node_exits[1]

            possible_exits = possible_exits[0] + possible_exits[1]
            random.shuffle(possible_exits)  # randomize order

            # Start trying exits
            while len(possible_exits) > 0:
                d1 = possible_exits.pop()
                R1 = net_state.rooms.get_room_from_element(d1)
                d1_type = R1.element_type(d1)
                if self.verbose:
                    print('selected: ', d1)

                # Collect possible entrances for d1
                possible_entrances = []
                if self.verbose:
                    print('Possible entrances:')
                for node in net_state.net.nodes:
                    if d1_type == 0:
                        node_entr = [d for d in node.doors if d is not d1]
                    else:
                        node_entr = [p for p in node.pits]
                    if self.verbose:
                        print('\t' + str(node.id) + ': ', node_entr, '(count: ',node.count,')', ' - ', cl[node])
                    possible_entrances.extend(node_entr)
                random.shuffle(possible_entrances)  # randomize order

                while len(possible_entrances) > 0:
                    d2 = possible_entrances.pop()

                    try:
                        net_backup = deepcopy(net_state)
                        if self.verbose:
                            print('\t\tTrying Connection: ', str(d1), str(d2))
                        net_state.connect(d1, d2)
                        net_state = net_state.connect_network_stupid()

                        # up_propagate the successful connection
                        return net_state

                    except:
                        if self.verbose:
                            print('\t\t(' + str(d1) + ',' + str(d2) + ') failed')
                        net_state = net_backup # reset the network

                # If you get here, you ran out of possible entrances.
                if self.verbose:
                    print('\t' + str(d1) + ' ran out of possible entrances.')
                raise Exception(str(d1) + ' ran out of possible entrances.')

            if self.verbose:
                print('\t' + str(R_active.id) + ' ran out of possible exits.')
            raise Exception("Ran out of possible exits.")


    def get_valid_connections(self, d1):
        # Return a list of valid connections for the door or trap d1
        R1 = self.rooms.get_room_from_element(d1)
        d1_type = R1.element_type(d1)
        if d1_type == 0:
            d2_type = 0
        elif d1_type == 1:
            d2_type = 2
        if self.verbose:
            print('\nConnecting ' + str(R1.id) + ' (' + str(d1) + '): type = ' + str(d1_type) + ', looking for type ' + str(d2_type))

        # Collect information about the state of the network
        top_nodes = self.get_top_nodes()
        inlets = [[], []]
        inlet_count = [0, 0]
        outlet_count = [0 - (d1_type == 0), 0 - (d1_type == 1)]
        downstream_exits = {}
        for n in top_nodes:
            # Count entrances/exits for the top node
            inlets[0].extend([d for d in n.doors if d is not d1])
            inlet_count[0] += len(n.doors) - (d1 in n.doors)
            inlets[1].extend([p for p in n.pits])
            inlet_count[0] += len(n.pits)
            outlet_count[0] += len(n.doors) - (d1 in n.doors)
            outlet_count[1] += len(n.traps) - (d1 in n.traps)

            # Count downstream exits from the top node
            downstream_exits[n] = [[d for d in n.doors if d is not d1], [t for t in n.traps if t is not d1]]
            d_nodes = self.get_downstream_nodes(n)
            for dn in d_nodes:
                downstream_exits[n][0].extend([d for d in dn.doors if d is not d1])
                downstream_exits[n][1].extend([t for t in dn.traps if t is not d1])
            outlet_count[0] += len(downstream_exits[n][0])
            outlet_count[1] += len(downstream_exits[n][1])

        if self.verbose:
            print('\tTop nodes are: ', [n.id for n in top_nodes])
            print('\tinlet count: ', inlet_count)
            print('\toutlet count: ', outlet_count)

        # If inlet count == outlet count for the type in question, only include inlets in the valid set.
        valid = []

        if inlet_count[d1_type] == outlet_count[d1_type]:
            valid.extend(inlets[d1_type])
        else:
            upstream_nodes = self.get_upstream_nodes(R1)
            if self.verbose:
                print('\tFound upstream nodes: ', [e.id for e in upstream_nodes])
            # Only connect loose nodes if they have no predecessors
            unconnected_nodes = [r for r in self.rooms.rooms if r not in upstream_nodes and
                                 r is not R1 and len(list(self.net.predecessors(r))) == 0]
            if self.verbose:
                print('\tFound loose nodes: ', [e.id for e in unconnected_nodes])

            # By construction, there should be no loops or downstream nodes.

            # Validity rules:
            self_exits = [d for d in R1.doors if d is not d1] + [t for t in R1.traps if t is not d1]
            is_last_exit = len(self_exits) == 0
            if self.verbose:
                print('\tSelf-exits found: ', self_exits)

            up_conn = [[c for c in node.get_elements(d2_type)] for node in upstream_nodes]
            if self.verbose:
                print('\tUpstream connections found: ', up_conn)
            self_conn = [c for c in R1.get_elements(d2_type) if c is not d1]
            if self.verbose:
                print('\tSelf connections found: ', self_conn)
            conn = up_conn + [self_conn]
            conn_count = [len(c) for c in conn]

            outside_count = [0, 0]  # count ways into outside nodes
            for node in unconnected_nodes:
                outside_count[0] += node.count[0]  # number of doors in node
                outside_count[1] += node.count[2]  # number of pits in node
                if self.verbose:
                    print('\t\tChecking node ', node.id, '(', node.count, ')')
                if not self.is_dead_end(node):
                    # 0. Always include unconnected nodes from non-dead-ends
                    if self.verbose:
                        print('\t\tnot a dead end, add connections: ', [c for c in node.get_elements(d2_type)])
                    valid.extend([c for c in node.get_elements(d2_type)])

                else:
                    if self.verbose:
                        print('\t\tis a dead end.  Check if valid.')
                    if not is_last_exit or (sum(conn_count) == 0 and len(unconnected_nodes) == 1):
                        # 1. Include dead ends IF there's another exit in R1, or it's the last exit
                        if self.verbose:
                            print('\t\tis valid, add connections: ', [c for c in node.get_elements(d2_type)])
                        valid.extend([c for c in node.get_elements(d2_type)])

            conn_outside_count = len(valid)  # number of valid connections in outside nodes


            # 2. if there are no loose connections and there is only one upstream connection, add it.
            if conn_outside_count == 0 and sum(conn_count) == 1:
                if self.verbose:
                    print('\tOnly one connection available: add it. ', conn[conn_count.index(1)])
                valid.extend(conn[conn_count.index(1)])

            # 3. Otherwise, add connections that leave downstream exits
            elif len(self_exits) == 0:
                if self.verbose:
                    print('\tNo self-exits.  Add upstream connections that have downstream exits.')
                paths = self.get_upstream_paths(R1)
                for path in paths:
                    if self.verbose:
                        print('\tChecking path: ', [p.id for p in path])
                    # Get the cumulative downstream exit count on the list of nodes.
                    down_exits = []  # there are no exits downstream (len(self_exits) == 0)
                    down_exit_count = [-(d1_type == 0), 0]  # Reduce count by one door, if d1 is a door.
                    for p in path:
                        down_exits.extend([c for c in p.doors] + [c for c in p.traps])
                        down_exit_count[0] += len(p.doors)
                        down_exit_count[1] += len(p.traps)
                        if self.verbose:
                            print('\t\tNode ' + str(p.id) + ' exits:', down_exits, '(', down_exit_count, ')')
                        # If the cumulative count of exits > 0, add the entrances above that point.
                        if (down_exit_count[0] > 0) or (down_exit_count[1] > 0):
                            # and (down_exit_count[d1_type] > 0 or conn_outside_count == 0)
                            if self.verbose:
                                print('\t\tThere are downstream exits, include these connections: ', [c for c in p.get_elements(d2_type)])
                            valid.extend([c for c in p.get_elements(d2_type)])

            elif len(self_exits) == 1 and d1_type == 0 and R1.element_type(self_exits[0]) == 0:
                    # We are connecting a door, and there is one door in R1.
                    if self.verbose:
                        print('\tOne self-exit.  Add all upstream connections (but not the self exit)')
                    # Connect to any upstream path, but not the door in R1
                    for connection in up_conn:
                        if self.verbose:
                            print('\t\tadd:', [c for c in connection])
                        valid.extend([c for c in connection])

            else:
                if self.verbose:
                    print('\tSeveral self-exits.  Add all self and upstream connections')
                # (4) There are more exits in the room: include everything above it.
                for connection in conn:
                    if self.verbose:
                        print('\t\tadd:', [c for c in connection])
                    valid.extend([c for c in connection])

            if self.verbose:
                print('Valid connections found: ', valid)
            valid = list(set(valid))  # remove duplicates, if any.
            if self.verbose:
                print('No duplicates: ', valid)

        return valid

    def plot_map(self):
        # Make a plot of the map
        # Construct a new network and write in the map edges
        plotnet = nx.DiGraph()
        plotnet.add_nodes_from(self.original_room_ids)
        door_rooms = {}
        room_labels = {}
        for r in plotnet.nodes():
            room_labels[r] = str(r)
            for t in room_data[r][:3]:
                for d in t:
                    door_rooms[d] = r
            if len(room_data[r]) == 6:
                # Collect locked items data
                for t in room_data[r][4].values():
                    for l in t:
                        door_rooms[l] = r
        # add edges to the plotnet
        edge_labels = {}
        for m in self.map[0]:
            # Add doors
            r1 = door_rooms[m[0]]
            r2 = door_rooms[m[1]]
            plotnet.add_edge(r1, r2)
            plotnet.add_edge(r2, r1)
            edge_labels[(r1, r2)] = str(m[0]) + '<->'+str(m[1])
        for m in self.map[1]:
            # Add traps
            r1 = door_rooms[m[0]]
            r2 = door_rooms[m[1]]
            plotnet.add_edge(r1, r2)
            edge_labels[(r1, r2)] = str(m[0]) + '-->' + str(m[1])

        pos = nx.spring_layout(plotnet)
        nx.draw_networkx_nodes(plotnet, pos=pos)
        nx.draw_networkx_labels(plotnet, pos=pos)
        two_ways = [e for e in plotnet.edges if (e[1],e[0]) in plotnet.edges]
        one_ways = [e for e in plotnet.edges if (e[1], e[0]) not in plotnet.edges]
        nx.draw_networkx_edges(plotnet, pos=pos, edgelist=two_ways)
        nx.draw_networkx_edges(plotnet, pos=pos, edgelist=one_ways, edge_color='r')
        nx.draw_networkx_edge_labels(plotnet, pos=pos, edge_labels=edge_labels)


    def is_dead_end(self, node):
        # Return True if node is a dead end (one entrance, no exits)
        down = self.get_downstream_nodes(node)
        up = self.get_upstream_nodes(node)
        if down or up:
            # Cannot be a dead-end if it has downstream or upstream nodes, by definition
            return False
        else:
            nc = node.count
            return nc[:3] == [1, 0, 0] and nc[4] == 0
