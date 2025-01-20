from data.rooms import room_data, shared_exits, forced_connections, keys_applied_immediately
import networkx as nx
import random
from copy import deepcopy
import numpy as np


class Network:
    verbose = False

    def __init__(self, rooms):
        self.original_room_ids = [r for r in rooms]
        self.rooms = Rooms(rooms)
        self.net = nx.DiGraph()
        self.net.add_nodes_from(self.rooms.rooms)
        self.keychain = set()
        self.map = [[], []]

        self.active = 0  # index of active room

        self.should_stop = None  # timeout control

    def __deepcopy__(self, memo):
        # Custom deepcopy that excludes the should_stop Event
        cls = self.__class__
        result = self.__new__(cls)
        memo[id(self)] = result
        for k, v in self.__dict__.items():
            if k != 'should_stop':  # Skip copying the Event object
                setattr(result, k, deepcopy(v, memo))
        result.should_stop = self.should_stop  # share the same Event object
        return result

    def ForceConnections(self, forcing):
        # Look up forced connections for doors and connect them
        these_doors = self.rooms.doors + self.rooms.traps
        self.protected = []
        for d in forcing.keys():
            if d in these_doors:
                df = forcing[d][0]  # get forced connection ID
                if self.verbose:
                    print('Forcing: ', d, df)
                self.connect(d, df, state='forced')
            self.protected.extend(forcing[d])

    def ApplyImmediateKeys(self, args):
        # Apply keys controlled by args
        for flag in keys_applied_immediately.keys():
            if self.verbose:
                print('testing flag: ', flag, '(', getattr(args, flag), ')')
            [condition, keylist] = keys_applied_immediately[flag]
            applykeys = (getattr(args, flag) == condition)
            if applykeys:
                if self.verbose:
                    print('condition satisfied!')
                for k in keylist:
                    self.apply_key(k)

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

            if state != 'forced':
                # (4) Update the active room & apply any keys
                if loop:
                    self.active = self.rooms.rooms.index(loop_room)
                    for k in loop_room.keys:
                        self.apply_key(k)

                else:
                    self.active = self.rooms.rooms.index(R2)
                    for k in R2.keys:
                        self.apply_key(k)


    def apply_key(self, key):
        # Add the key to the keychain
        self.keychain.add(key)

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
                    elif type(item) is dict:
                        # This is another locked item.
                        room.add_locks(item)
                        unlockable = [k for k in item.keys() if k in self.keychain]
                        for k in unlockable:
                            # unlock the nested lock, if we already have the key.
                            self.apply_key(k)
                    elif item < 2000:
                        # This is a door.
                        room.add_doors([item])
                    else:
                        # This is a trap.
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
                return self.get_upstream_paths(p, nodes + [p])
            else:
                temp = []
                for p in pred:
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

    # def get_top_nodes(self):
    #     top_nodes = set([])
    #     for n in self.net.nodes:
    #         paths = self.get_upstream_paths(n)
    #         for path in paths:
    #             # Add the ultimate node to the set
    #             top_nodes.add(path[-1])
    #     return top_nodes

    def is_attachable(self, node):
        # Return True if the node can accept a dead end.
        up = self.get_upstream_nodes(node)
        down = self.get_downstream_nodes(node)
        if up or down:
            up_count = np.array([0, 0, 0])
            for u in up:
                up_count += u.full_count[:3]
            down_count = np.array([0, 0, 0])
            for d in down:
                down_count += d.full_count[:3]
            num_doors = len(node.alldoors)
            num_traps = len(node.alltraps)
            num_pits = len(node.pits)
            #print(str(node.id) + ' Attachability: ', num_doors, num_traps, num_pits, up_count, down_count)
            return (num_doors > 1) or (num_doors == 1 and (num_traps + down_count[0] + down_count[1]) > 0 and
                                       (num_pits + up_count[0] + up_count[2]) > 0)
        else:
            return node.is_attachable()

    def attach_dead_ends(self):
        # Attach all dead-end rooms to open connections
        dead_ends = [n for n in self.net.nodes if self.is_dead_end(n)]
        if self.verbose:
            print("Attaching dead ends: ", len(dead_ends))
            print([(e.id, e.doors[0]) for e in dead_ends])

        while len(dead_ends) > 0:
            if self.rooms.count[0] == 2:
                # These are the last two doors. Just connect them.
                R1 = dead_ends.pop()
                attachable_doors = [R1.doors[0]]
            else:
                attachable_doors = []
                for n in self.net.nodes:
                    if self.is_attachable(n):
                        attachable_doors.extend([d for d in n.doors + n.locked('doors')])
                if self.verbose:
                    print("found attachable doors: ", attachable_doors)
                random.shuffle(dead_ends)
                random.shuffle(attachable_doors)

            for Rd in dead_ends:
                #if self.verbose:
                #    print('selected ', Rd.id, '.')

                if len(attachable_doors) > 0:
                    # select a door
                    dd = Rd.doors[0]
                    # select an attachable node
                    da = attachable_doors.pop(0)
                    Ra = self.rooms.get_room_from_element(da)

                    #if self.verbose:
                    #    print('\tConnecting: ' + str(dd) + '(' + str(Rd.id) + ') to ' + str(da) + '(' + str(Ra.id) + ')')

                    # Handle various bad cases if the dead end has a key:
                    if len(Rd.keys) > 0 or len(Ra.keys) > 0:
                        # 1. Verify the dead end doesn't contain the key to unlock this door
                        flags = [False]
                        if da in Ra.locked('doors'):
                            ka = Ra.get_key(da)
                            flags[0] = ka in Rd.keys

                        # 2. Verify there is an exit from this room that isn't locked by keys in these 2 rooms
                        flags.append(True)
                        otherdoors = [d for d in Ra.alldoors if d is not da]
                        available_keys = [k for k in Rd.keys] + [k for k in Ra.keys]
                        for d in otherdoors:
                            if d in Ra.locked('doors'):
                                ka = Ra.get_key(d)
                                if ka not in available_keys:
                                    # It's locked by something else
                                    flags[1] = False
                            else:
                                # It's not locked
                                flags[1] = False

                        if flags.count(True) > 0:
                            # ERROR don't connect it!
                            if self.verbose:
                                print('\t\tCannot connect ' + str(dd) + ' to ' + str(da) + ': ')
                                if flags[0]:
                                    print('\t\t' + str(da) + ' is locked by key ' + str(ka) + ' which is in ' + str(Rd.id) + '!')
                                elif flags[1]:
                                    print('\t\tall other exits from ' + str(Ra.id) + ' are locked by a key in ' + str(Rd.id) + '!')
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
                    if not self.is_attachable(Ra):
                        # If not, remove any remaining doors.
                        more_doors = [d for d in Ra.alldoors]
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
                print("Attaching dead ends: ", len(dead_ends))
                print([(e.id, e.doors[0]) for e in dead_ends])

    def check_network_invalidity(self):
        # Check the network validity based on the following four validity rules:
        # [A] not [(Door in / trap out) and (Pit in / door out)] and (Door in / door out) and (Pit in / trap out)
        #     = not "Network Bifurcation"
        # [B] not (Door in / trap out) and (Pit in / door out)   = not "one-way version 1"
        # [C] (Door in / trap out) and not (Pit in / door out)   = not "one-way version 2"
        # [D] (#_doors_in + #_undetermined_doors < #_doors_out) or (#_doors_out + #_undetermined_doors < #_doors_in)
        #     = door imbalance
        # If returns True, network is invalid
        classifications = {}
        total_doors_in = 0
        total_doors_out = 0
        total_doors_either = 0
        for node in self.net.nodes:
            # Count entrances & exits
            self_count = node.full_count[:3]
            up_count = np.array([0, 0, 0])
            up_nodes = self.get_upstream_nodes(node)
            for up in up_nodes:
                up_count += up.full_count[:3]
            down_count = np.array([0, 0, 0])
            down_nodes = self.get_downstream_nodes(node)
            for down in down_nodes:
                down_count += down.full_count[:3]

            # Look for the small number of cases in which a forced exit is still locked
            locked_forced = [lf for lf in node.locked() if lf in forced_connections.keys()]  # locked forced traps
            if 'forced' in node.locks.keys():
                locked_protected = [lf for lf in node.locks['forced']]   # locked forced entrances
            else:
                locked_protected = []
            for lf in locked_forced:
                if self.verbose:
                    print('\t\t\tFound locked forced connection:', lf, 'in', node.id)
                [l_type, c_type] = [[0, 1][[True, False].index(lf < 2000)],
                                    [0, 2][[True, False].index(lf < 2000)]]
                fc = forced_connections[lf][0]
                if self.verbose:
                    print('\t\t\t\t-->', fc)
                if fc in locked_protected:
                    # Forced connection is in the same room.  Remove 1 entrance & 1 exit from here.
                    if self.verbose:
                        print('\t\t\t\tforced connection in same room!')
                    self_count[l_type] -= 1
                    self_count[c_type] -= 1
                    locked_protected.remove(fc)
                else:
                    Rconn = self.rooms.get_room_from_element(fc)
                    if self.verbose:
                        print('\t\t\t\tforced connection in room:', Rconn.id)
                    if Rconn in up_nodes:
                        # Forced connection is upstream.  Remove 1 exit from here & 1 entrance from upstream
                        self_count[l_type] -= 1
                        up_count[c_type] -= 1
                        if self.verbose:
                            print('\t\t\t\t... in upstream')
                    elif Rconn in down_nodes:
                        # Forced connection is downstream.  Remove 1 exit from here & 1 entrance from downstream
                        self_count[l_type] -= 1
                        down_count[c_type] -= 1
                        if self.verbose:
                            print('\t\t\t\t... in downstream')
            for lp in locked_protected:
                if self.verbose:
                    print('\t\t\tFound locked forced connection:', lp, 'in', node.id)
                # already handled case where lf and lp are in the same room
                [l_type, c_type] = [[0, 2][[True, False].index(lp < 2000)],
                                    [0, 1][[True, False].index(lp < 2000)]]
                fc = [lf for lf in forced_connections.keys() if lp in forced_connections[lf]][0]
                if self.verbose:
                    print('\t\t\t\t-->', fc)
                Rconn = self.rooms.get_room_from_element(fc)
                if self.verbose:
                    print('\t\t\t\tForced connection is in room:', Rconn.id)
                if Rconn in up_nodes:
                    # Forced connection is upstream.  Remove 1 entrance from here & 1 exit from upstream
                    self_count[l_type] -= 1
                    up_count[c_type] -= 1
                    if self.verbose:
                        print('\t\t\t\t... in upstream')
                elif Rconn in down_nodes:
                    # Forced connection is downstream.  Remove 1 entrance from here & 1 exit from downstream
                    self_count[l_type] -= 1
                    down_count[c_type] -= 1
                    if self.verbose:
                        print('\t\t\t\t... in downstream')

            # Assess classifications
            door_in = (up_count[0] + self_count[0]) > 0
            door_out = (down_count[0] + self_count[0]) > 0
            # Handle special case (avoid double counting self exits)
            door_in_door_out = (door_in and down_count[0] > 0) or (door_out and up_count[0] > 0) or (self_count[0] > 1)
            pit_in = (up_count[2] + self_count[2]) > 0
            trap_out = (down_count[1] + self_count[1]) > 0

            # Count total doors in/out OF THIS NODE
            delta_in = 0
            if sum(up_count) == 0 and self_count[2] == 0:
                # No guaranteed entrances.  One door must be an entrance.
                delta_in = min([1, self_count[0]])
            delta_out = 0
            if sum(down_count) == 0 and self_count[1] == 0:
                # No guaranteed exits.  One door must be an exit.
                delta_out = min([1, self_count[0]])
            # All remaining doors may be either
            delta_either = max([0, self_count[0] - delta_in - delta_out])

            total_doors_in += delta_in
            total_doors_out += delta_out
            total_doors_either += delta_either

            # For each node: [(door in, door out), (door in, trap out), (pit in, door out), (pit in, trap out)]
            classifications[node] = [door_in_door_out, door_in and trap_out, pit_in and door_out, pit_in and trap_out,
                                     [list(up_count), list(self_count), list(down_count)],
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

    def connect_network(self):
        if self.should_stop and self.should_stop.is_set():
            raise TimeoutError('Operation cancelled')

        # Connect the network by proposing a connection & recursively connecting the created network.
        # If a connection fails or creates an invalid network, retreat a step and try a different one.
        net_state = deepcopy(self)  # AFTER THIS POINT: all operations should be on net_state!

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
                    for k in cl.keys():
                        print('\t',k.id,': ', cl[k])
                raise Exception('Invalid network state.')
            else:
                if self.verbose:
                    print('\tValid!  in/out/either = ', td)

            R_active = net_state.rooms.rooms[net_state.active]
            if self.verbose:
                print('Active node: ', R_active.id)

            # Apply any keys in this node if they haven't been already
            for k in R_active.keys:
                if self.verbose:
                    print('Found an unused key: ', k)
                net_state.apply_key(k)

            # Collect possible exits
            possible_exits = [[d for d in R_active.doors], [t for t in R_active.traps]]
            if self.verbose:
                print('Possible exits: ')
                print('\t' + str(R_active.id) + ': ', possible_exits, ' - (', R_active.count[:3], '). K: ',
                      R_active.keys, ', L: ', R_active.locks, '. [U/s/D]:', cl[R_active][4])
            for node in net_state.get_downstream_nodes(R_active):
                # Collect exits from downstream nodes.
                ### AS WE DO THIS: do we need to look for keys & apply them?  but only along the present branch???
                node_exits = [[d for d in node.doors], [t for t in node.traps]]
                if self.verbose:
                    print('\t' + str(node.id) + ': ', node_exits, ' - (', node.count[:3], '). K: ', node.keys, ', L: ',
                          node.locks, '. [U/s/D]:', cl[node][4])
                possible_exits[0] += node_exits[0]
                possible_exits[1] += node_exits[1]

            possible_exits = possible_exits[0] + possible_exits[1]
            random.shuffle(possible_exits)  # randomize order

            forced_exits = [f for f in possible_exits if f in forced_connections.keys()]
            for f in forced_exits:
                possible_exits.remove(f)
            possible_exits = possible_exits + forced_exits

            # Start trying exits
            while len(possible_exits) > 0:
                d1 = possible_exits.pop()
                R1 = net_state.rooms.get_room_from_element(d1)
                d1_type = R1.element_type(d1)
                if self.verbose:
                    print('selected: ', d1, '(', R1.id, ')')

                # if d1 was in a downstream node, R1 might have a key that hasn't been used yet.
                if R1 is not R_active:
                    trail = [R1]
                    if R_active not in net_state.net.predecessors(R1):
                        # R_active is significantly upstream.  Find the traversed nodes.
                        trails = [p for p in net_state.get_upstream_paths(R1) if R_active in p]
                        trail += trails[0][:trails[0].index(R_active)]
                        if self.verbose:
                            print('Traversed: ', [r.id for r in trail])
                    # Apply any keys found along the way.
                    for Rt in trail:
                        for k in Rt.keys:
                            if self.verbose:
                                print('Found an unused key: ', k, 'in',Rt.id)
                            net_state.apply_key(k)

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
                        print('\t' + str(node.id) + ': ', node_entr, ' - (', node.count[:3], '). K: ', node.keys,
                              ', L: ', node.locks, '. [U/s/D]:', cl[node][4])
                    possible_entrances.extend(node_entr)

                if d1 in forced_connections.keys():
                    # This should only happen for forced one-way connections.  d2 must be locked, so it's not sampled.
                    possible_entrances = [d for d in forced_connections[d1]] # fail fast!
                    if self.verbose:
                        print('\t\tForced connection: ', possible_entrances)
                else:
                    possible_entrances = [p for p in possible_entrances if p not in net_state.protected]

                random.shuffle(possible_entrances)  # randomize order

                while len(possible_entrances) > 0:
                    d2 = possible_entrances.pop()

                    try:
                        net_backup = deepcopy(net_state)
                        if self.verbose:
                            print('\t\tTrying Connection: ', str(d1), str(d2))
                        net_state.connect(d1, d2)
                        if self.verbose:
                            print('\t\t...')
                        net_state = net_state.connect_network()

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


class Rooms:
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

    @property
    def alldoors(self):
        locked_doors = []
        for room in self.locked:
            for locked in room:
                locked_doors.extend([ll for ll in locked if ll < 2000])
        return self.doors + locked_doors

    @property
    def alltraps(self):
        locked_traps = []
        for room in self.locked:
            for locked in room:
                locked_traps.extend([ll for ll in locked if 2000 <= ll < 3000])
        return self.traps + locked_traps

    def remove(self, id):
        for room in self.rooms:
            if room.id == id:
                # Remove this room id
                self.rooms.remove(room)
                return True
            # If this is an exit id, remove it.
            # UPDATE: NEVER DO THIS.  ONLY explicitly remove an exit from its room using Room.remove(exit_id)
            #if room.remove(id):
            #    return True
        return False


class Room:
    verbose = False

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
            d_shared = [d for d in self.alldoors if d in shared_exits.keys()]
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
    def alldoors(self):
        return self.doors + self.locked('doors')

    @property
    def alltraps(self):
        return self.traps + self.locked('traps')

    @property
    def allpits(self):
        return self.pits + self.locked('pits')

    @property
    def allkeys(self):
        return self.keys + self.locked('keys')

    @property
    def count(self):
        return [len(s) for s in self._contents]

    @property
    def full_count(self):
        return np.array(self.count[:4]) + np.array(
            [len(self.locked('doors')), len(self.locked('traps')), len(self.locked('pits')), len(self.locked('keys'))]
        )

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

    def extract_locked(self, lock):
        elements = []
        for vv in lock.values():
            elements.extend([v for v in vv if type(v) is not dict])
            locked_locks = [v for v in vv if type(v) is dict]
            for ll in locked_locks:
                elements.extend(self.extract_locked(ll))
        return elements

    def locked(self, elementtype=None):
        locked_elements = self.extract_locked(self._contents[4])

        if elementtype is None:
            return locked_elements
        elif elementtype in ['doors', 0]:
            locked = [d for d in locked_elements if type(d) is int]
            return [d for d in locked if d < 2000]
        elif elementtype in ['traps', 1]:
            locked = [d for d in locked_elements if type(d) is int]
            return [d for d in locked if 2000 <= d < 3000]
        elif elementtype in ['pits', 2]:
            locked = [d for d in locked_elements if type(d) is int]
            return [d for d in locked if 3000 <= d]
        elif elementtype in ['keys', 3]:
            return [d for d in locked_elements if type(d) is str]
        else:
            return False

    def remove(self, item):
        for r in range(len(self._contents) - 1):
            if item in self._contents[r]:
                self._contents[r].remove(item)
                if self.verbose:
                    print('Removed:', item, 'from room:', self.id)
                return True
        for k in self.locks.keys():
            if item in self.locks[k]:
                self.locks[k].remove(item)
                if self.verbose:
                    print('Removed locked item:', item, 'from lock:', self.locks[k], 'in room:', self.id)
                if len(self.locks[k]) == 0:
                    # This lock is empty.  Remove it.
                    self.locks.pop(k)
                    if self.verbose:
                        print('Empty lock, deleted.')
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
        elif id in self.locked():
            return True
        return False

    def element_type(self, e_id):
        is_element = [e_id in self.alldoors, e_id in self.alltraps, e_id in self.allpits, e_id in self.allkeys]
        if True in is_element:
            return is_element.index(True)
        else:
            # it's not here.
            #print('ERROR: ', e_id, 'is not in ', self.id,': ', self._contents)
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
        for k in self.locks:
            if locked_element in self.locks[k]:
                return k

    def get_exit(self):
        # Return a random exit from those available
        exit_list = self.doors + self.traps
        return random.choice(exit_list)

    def is_attachable(self):
        # A room is attachable to a dead end room if it has 2 doors or 1 door and at least 1 pit AND 1 trap.
        # These can include locked values.
        all_doors = [d for d in self.alldoors]
        all_traps = [t for t in self.alltraps]
        pits = [p for p in self.pits]
        return (len(all_doors) > 1) or (len(all_doors) == 1 and len(all_traps) > 0 and len(pits) > 0)