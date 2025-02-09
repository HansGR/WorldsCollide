from data.rooms import room_data, shared_exits, forced_connections, keys_applied_immediately, doors_as_traps
import networkx as nx
import random
from copy import deepcopy
import numpy as np


class Network:
    verbose = False

    def __init__(self, rooms):
        self.original_room_ids = list(rooms)  # Store original IDs
        self.rooms = Rooms(rooms)  # Now using improved Rooms class
        self.net = nx.DiGraph()
        #self.net.add_nodes_from(self.rooms)  # Rooms class is now iterable
        self.net.add_nodes_from(room.id for room in self.rooms)
        self.keychain = set()
        self.map = [[], []]
        self.protected = None

        self.active = None  # next(iter(self.rooms)).id  # Set first room's ID as active
        self.should_stop = None
        self.version = 'Claude'

    def __deepcopy__(self, memo):
        cls = self.__class__
        result = cls.__new__(cls)
        memo[id(self)] = result
        for k, v in self.__dict__.items():
            if k != 'should_stop':
                setattr(result, k, deepcopy(v, memo))
        result.should_stop = self.should_stop
        return result

    def ForceConnections(self, forcing, state='forced'):
        these_doors = self.rooms.doors + self.rooms.traps
        if self.protected is None:
            self.protected = []
        for d in forcing.keys():
            if d in these_doors:
                df = forcing[d][0]
                if self.verbose:
                    print('Forcing: ', d, df)
                self.connect(d, df, state=state)
                if self.verbose:
                    print('forcing successful.')
            self.protected.append(d)
            self.protected.extend(forcing[d])
        if self.verbose:
            print('added doors to protected: ', self.protected)

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
        # Get rooms containing elements
        R1 = self.rooms.get_room_from_element(d1)
        R2 = self.rooms.get_room_from_element(d2)

        #print('\t\t\tSelected rooms:', R1.id, R2.id)
        if R1 is not R2:
            self.net.add_edge(R1.id, R2.id)
            #print('\t\t\t\tadded edge', R1.id, '--> ', R2.id)
            if R1.element_type(d1) == 0:
                self.net.add_edge(R2.id, R1.id)
                #print('\t\t\t\tadded edge', R2.id, '--> ', R1.id)

        # Add to network map
        if R1.element_type(d1) == 0:
            self.map[0].append([d1, d2])
            #print('\t\t\tadded to map:', self.map[0][-1])
        else:
            self.map[1].append([d1, d2])
            #print('\t\t\tadded to map:', self.map[1][-1])


        # Remove elements from rooms
        R1.remove(d1)
        #print('\t\t\tremoved', d1)
        R2.remove(d2)
        #print('\t\t\tremoved', d2)

        if state != 'static':
            loop = self.get_loop(R1.id)
            #print('\t\t\tlook for loop', loop)
            if loop:
                loop_room = self.compress_loop(loop)
                #print('\t\t\tcompressed loop', loop_room.id)

            if state != 'forced':
                if loop:
                    # Need to change how we update active room
                    self.active = loop_room.id
                    #print('\t\t\tactivated', loop_room.id)
                    for k in loop_room.keys:
                        self.apply_key(k)
                        #print('\t\t\tapplied key', k)
                else:
                    self.active = R2.id
                    #print('\t\t\tactivated', R2.id)
                    for k in R2.keys:
                        self.apply_key(k)
                        #print('\t\t\tapplied key', k)

    def apply_key(self, key):
        # Add the key to the keychain
        #print('\t\t\t\t\tadding key: ', key)
        self.keychain.add(key)

        # unlock any doors or traps locked by key
        room_list = [r for r in self.rooms.rooms]
        if self.verbose:
            print('\t\tassessing key ', key, 'in rooms')   # : ', room_list)
        for room_id in room_list:
            #if self.verbose:
            #    print('\t\t\t\t\t\tchecking room ', room_id)
            room = self.rooms.get_room(room_id)
            #if key in room.locks.keys():
            room_keys = [k for k in room.locks.keys()]
            for required_keys in room_keys:
                if set(required_keys).issubset(self.keychain):
                    if self.verbose:
                        print('\t\t\tApplying key:', required_keys, 'in room', room.id)
                    locked = room.locks.pop(required_keys)  # this also removes the item from room.locks
                    for item in locked:
                        if isinstance(item, str):
                            # This is a key.  Immediately apply it.
                            if self.verbose:
                                print('\t\t\tApplying a new key:', item)
                            self.apply_key(item)
                        elif isinstance(item, dict):
                            # This is another locked item.  Should not happen with tuple keys
                            if self.verbose:
                                print('\t\t\tApplying a new lock:', item)
                            print('\t\t\tWARNING: found a nested lock in ', room_id,' : ', item)
                            room.add_locks(item)
                            unlockable = [k for k in item.keys() if set(k).issubset(self.keychain)]
                            for k in unlockable:
                                # unlock the nested lock, if we already have the key.
                                if self.verbose:
                                    print('\t\t\talready have key ', k,', applying it')
                                self.apply_key(k)
                        elif room.element_type(item) == 0:  # item < 2000
                            # This is a door.
                            if self.verbose:
                                print('\t\t\tadding a door...', item)
                            room.add_doors([item])
                        elif room.element_type(item) == 1:
                            # This is a trap.
                            if self.verbose:
                                print('\t\t\tadding a trap...', item)
                            room.add_traps([item])
                        else:
                            # Error
                            raise RoomError(f"Unknown item unlocked by key {required_keys} in room {room_id}: {item}")

            # Delete the key, we already have it.
            if key in room.keys:
                if self.verbose:
                    print('\t\t\tremoving key ', key, 'from', room.id)
                room.remove(key)

    def get_loop(self, room_id):
        # Look for a loop containing this room.  If found, return [list of nodes in loop]; if not, return [].
        paths = self.get_upstream_paths(room_id)
        is_loop = [path.__contains__(room_id) for path in paths]
        if True in is_loop:
            loop = paths[is_loop.index(True)]
            loop = loop[:loop.index(room_id) + 1]
            return loop
        return []

    def compress_loop(self, loop_ids):
        """Compress a loop of room IDs into a single room"""
        if len(loop_ids) > 1:
            # Create new room ID
            r_id = '_'.join(str(id) for id in loop_ids)
            #print('\t\t\t\t\tcreating a new room:', r_id)
            new_room = Room(r_id, self.rooms)

            # Combine elements from all rooms in loop
            #print('\t\t\t\t\tadding elements...')
            for room_id in loop_ids:
                room = self.rooms.get_room(room_id)
                #print('\t\t\t\t\tdoors...', room.doors)
                new_room.add_doors(room.doors)
                #print('\t\t\t\t\ttraps...', room.traps)
                new_room.add_traps(room.traps)
                #print('\t\t\t\t\tpits...', room.pits)
                new_room.add_pits(room.pits)
                #print('\t\t\t\t\tkeys...', room.keys)
                new_room.add_keys(room.keys)
                #print('\t\t\t\t\tlocks...', room.locks)
                new_room.add_locks(room.elements['locks'])

            # Add new_room
            #print('\t\t\t\t\tadding the room...', new_room.id)
            self.rooms.add_room(new_room)
            #print('\t\t\t\t\tadding as node...')
            self.net.add_node(new_room.id)

            # Inherit edges
            current_edges = list(self.net.edges)
            #print('\t\t\t\t\tinheriting edges from:', current_edges)
            for e in current_edges:
                if e[0] in loop_ids and e[1] not in loop_ids:
                    #print('\t\t\t\t\t\tinheriting:', new_room.id, e[1])
                    self.net.add_edge(new_room.id, e[1])
                elif e[0] not in loop_ids and e[1] in loop_ids:
                    #print('\t\t\t\t\t\tinheriting:', e[0], new_room.id)
                    self.net.add_edge(e[0], new_room.id)

            # Remove loop nodes
            for room_id in loop_ids:
                #print('\t\t\t\t\tremoving node:', room_id)
                self.net.remove_node(room_id)
                #print('\t\t\t\t\tremoving room:', room_id)
                self.rooms.remove(room_id)

            return new_room
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

    def get_upstream_paths(self, room_id, visited=None):
        """Return list of paths heading upstream from room_id"""
        if visited is None:
            visited = []

        pred = [p for p in self.net.predecessors(room_id) if p not in visited]
        if len(pred) > 0:
            if len(pred) == 1:
                p = pred[0]
                return self.get_upstream_paths(p, visited + [p])
            else:
                temp = []
                for p in pred:
                    temp.append(self.get_upstream_paths(p, visited + [p]))
                return self.flatten_paths(temp)
        return self.flatten_paths([visited])

    def get_upstream_nodes(self, room_id, visited=None):
        """Get nodes upstream from room_id"""
        if visited is None:
            visited = []

        pred = [p for p in self.net.predecessors(room_id) if p not in visited]
        if len(pred) > 0:
            temp = []
            for p in pred:
                if room_id in self.net.predecessors(p):
                    # Ignore simple 2-way doors
                    temp += self.get_upstream_nodes(p, visited)
                else:
                    temp += self.get_upstream_nodes(p, visited + [p])
            return temp
        return visited

    def get_downstream_nodes(self, room_id, visited=None):
        """Get nodes downstream from room_id"""
        if visited is None:
            visited = []

        succ = [s for s in self.net.successors(room_id) if s not in visited]
        if len(succ) > 0:
            temp = []
            for s in succ:
                if room_id in self.net.successors(s):
                    # Ignore simple 2-way doors
                    temp += self.get_downstream_nodes(s, visited)
                else:
                    temp += self.get_downstream_nodes(s, visited + [s])
            return temp
        return visited

    def get_elements(self, node_list, element_type):
        elements = []
        for R_id in node_list:
            R = self.rooms.get_room(R_id)
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

    def is_attachable(self, room_id):
        # Return True if the node can accept a dead end.
        up = self.get_upstream_nodes(room_id)
        down = self.get_downstream_nodes(room_id)
        room = self.rooms.get_room(room_id)
        if up or down:
            up_count = np.array([0, 0, 0])
            for u in up:
                up_count += self.rooms.get_room(u).full_count[:3]
            down_count = np.array([0, 0, 0])
            for d in down:
                down_count += self.rooms.get_room(d).full_count[:3]
            num_doors = len(room.alldoors)
            num_traps = len(room.alltraps)
            num_pits = len(room.pits)
            #print(str(node.id) + ' Attachability: ', num_doors, num_traps, num_pits, up_count, down_count)
            return (num_doors > 1) or (num_doors == 1 and (num_traps + down_count[0] + down_count[1]) > 0 and
                                       (num_pits + up_count[0] + up_count[2]) > 0)
        else:
            return room.is_attachable()

    def attach_dead_ends(self):
        # Attach all dead-end rooms to open connections
        dead_ends = [n for n in self.net.nodes if self.is_dead_end(n)]
        if self.verbose:
            print('Current room ids: ', [r.id for r in self.rooms])
            print("Attaching dead ends: ", len(dead_ends))
            print('\t', [(self.rooms.get_room(e).id, self.rooms.get_room(e).doors) for e in dead_ends])

        loop_flag = len(dead_ends) > 0
        max_loop_number = 20
        loop_count = 0
        while loop_flag:
            if self.rooms.count[0] == 2:
                # These are the last two doors. Just connect them.
                R1_id = dead_ends.pop()
                R1 = self.rooms.get_room(R1_id)
                attachable_doors = [R1.doors[0]]
            else:
                attachable_doors = []
                attachable_nodes = []
                for n in self.net.nodes:
                    if self.is_attachable(n):
                        attachable_nodes.append(n)
                        this_room = self.rooms.get_room(n)
                        attachable_doors.extend([d for d in this_room.doors + this_room.locked('doors')])
                random.shuffle(dead_ends)
                random.shuffle(attachable_doors)

                if self.verbose:
                    print("found attachable nodes: ", len(attachable_nodes), attachable_nodes)
                    print("...with attachable doors: ", len(attachable_doors), attachable_doors)

            for Rd_id in dead_ends:
                Rd = self.rooms.get_room(Rd_id)
                #if self.verbose:
                #    print('selected ', Rd.id, '.')

                if len(attachable_doors) > 0:
                    # select a door
                    dd = Rd.doors[0]

                    #if self.verbose:
                    #    print('\tnow on', dd, '(', Rd_id, '), ', len(attachable_doors), ' options remaining...')

                    is_valid = False
                    da = None  # Safe initial values
                    Ra = None
                    while (not is_valid) and (len(attachable_doors) > 0):
                        # select an attachable node
                        da = attachable_doors.pop(0)
                        Ra = self.rooms.get_room_from_element(da)
                        #if self.verbose:
                        #    print('\t\ttesting ', da, '(', Ra.id, '), ', len(attachable_doors), ' remaining...')

                        # Check for bad cases where the dead end has a key:
                        if len(Rd.keys) > 0 or len(Ra.keys) > 0:
                            # 1. Verify the dead end doesn't contain the key to unlock this door
                            flags = [False]
                            if da in Ra.locked('doors'):
                                ka = Ra.get_key(da)
                                flags[0] = (ka in Rd.keys)

                            # 2. Verify there is an exit from this room that isn't locked by keys in these 2 rooms
                            flags.append(True)
                            otherdoors = [d for d in Ra.alldoors if d is not da]
                            available_keys = [k for k in Rd.keys] + [k for k in Ra.keys]
                            for d in otherdoors:
                                if d in Ra.locked('doors'):
                                    ka = Ra.get_key(d)
                                    is_internally_locked = [k in available_keys for k in ka]
                                    if is_internally_locked.count(True) == 0:
                                        # It's not locked by a key in the room
                                        flags[1] = False
                                else:
                                    # It's not locked
                                    flags[1] = False

                            # Look at the results & fail if necessary.
                            if flags.count(True) > 0:
                                # ERROR don't connect it!
                                if self.verbose:
                                    print('\t\tCannot connect ' + str(dd) + ' to ' + str(da) + ': ')
                                    if flags[0]:
                                        print('\t\t' + str(da) + ' is locked by key ' + str(ka) + ' which is in ' + str(Rd.id) + '!')
                                    elif flags[1]:
                                        print('\t\tall other exits from ' + str(Ra.id) + ' are locked by a key in ' + str(Rd.id) + '!')
                                da = None  # Safety in case we run out of exits
                                Ra = None

                        if da is not None:
                            # This exit is acceptable, lets move on
                            is_valid = True
                            #if self.verbose:
                            #    print('\t\t', da, '(', Ra.id, ') accepted. ')  # , len(attachable_doors), ' remaining...'

                    if da is not None:
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
                        old_id = Ra.id
                        new_id = f"{Ra.id}_{Rd.id}"
                        self.rooms.update_room_id(old_id, new_id)
                        self._rename_node(old_id, new_id)

                        # Remove the dead room from the network and list of rooms
                        self.net.remove_node(Rd_id)
                        self.rooms.remove(Rd)

                        # Check to see if the attached room is still attachable.
                        if not self.is_attachable(Ra.id):
                            # If not, remove any remaining doors.
                            more_doors = [d for d in Ra.alldoors]
                            if self.verbose:
                                print('\t' + str(Ra.id) + ' is no longer attachable. Removing doors:', more_doors)
                            for d in more_doors:
                                if d in attachable_doors:
                                    attachable_doors.remove(d)

                    else:
                        if self.verbose:
                            print('\tRan out of doors to connect',dd,'to.')

                else:
                    # If no attachable doors, just end.  It'll probably get straightened out in the walk.
                    #return
                    if self.verbose:
                        print('Ran out of attachable rooms.  Moving on...')

            # having attached all the dead ends, see if we created any & attach them if we did.
            dead_ends = [n for n in self.net.nodes if self.is_dead_end(n)]
            if self.verbose:
                print('End of loop', loop_count, '.  Remaining dead ends:', dead_ends)

            if len(dead_ends) > 0:
                loop_count += 1
                loop_flag = (loop_count <= max_loop_number)
            else:
                loop_flag = False
                if self.verbose:
                    print('done attaching dead ends.\n')

            if len(dead_ends) > 0 and self.verbose:
                print('Current room ids: ', [r.id for r in self.rooms])
                print("Attaching dead ends: ", len(dead_ends), '(loop', loop_count,')')
                print('\t', [(self.rooms.get_room(e).id, self.rooms.get_room(e).doors[0]) for e in dead_ends])

    def _rename_node(self, old_id, new_id):
        """Helper to rename a node using networkx relabeling"""
        mapping = {old_id: new_id}
        self.net = nx.relabel_nodes(self.net, mapping)

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

        dead_end_count = 0
        doors_in_non_dead_ends = 0
        total_count = np.array([c for c in self.rooms.count])
        #if self.verbose:
        #    print('\t\tbug hunting: total count', total_count)
        total_self_count = np.array([0, 0, 0])

        for room_id in self.net.nodes:
            #if self.verbose:
            #    print('\t\tbug hunting: room analysis', room_id)
            room = self.rooms.get_room(room_id)
            self_count = self.count_unprotected(room_id)  #   room.full_count[:3]  #
            total_self_count += np.array(room.count[:3])

            up_count = np.array([0, 0, 0])
            up_nodes = self.get_upstream_nodes(room_id)
            for up_id in set(up_nodes):   # for up_id in up_nodes:  don't doublecount?
                up_room = self.rooms.get_room(up_id)
                up_count += self.count_unprotected(up_id)  #  up_room.full_count[:3]  #

            down_count = np.array([0, 0, 0])
            down_nodes = self.get_downstream_nodes(room_id)
            for down_id in set(down_nodes):   # for down_id in down_nodes:  don't doublecount?
                down_room = self.rooms.get_room(down_id)
                down_count += self.count_unprotected(down_id)  #  down_room.full_count[:3]  #

            #if self.verbose:
            #    print('\t\tbug hunting 0. self:', self_count, '.', up_count,'in', len(up_nodes),': ', up_nodes, '; ',
            #          down_count, 'in', len(down_nodes), ': ', down_nodes)

            ### Using count_unprotected.  All forced exits should be protected, and therefore not counted.
            # # Look for the small number of cases in which a forced exit is still locked
            # locked_forced = [lf for lf in room.locked() if lf in forced_connections.keys()]  # locked forced traps
            # if 'forced' in room.locks.keys():
            #     locked_protected = [lf for lf in room.locks['forced']]   # locked forced entrances
            # else:
            #     locked_protected = []
            # for lf in locked_forced:
            #     if self.verbose:
            #         print('\t\t\tFound locked forced connection:', lf, 'in', room_id)
            #     [l_type, c_type] = [[0, 1][[True, False].index(room.element_type(lf) == 0)],
            #                         [0, 2][[True, False].index(room.element_type(lf) == 0)]]
            #     fc = forced_connections[lf][0]
            #     if self.verbose:
            #         print('\t\t\t\t-->', fc)
            #     if fc in locked_protected:
            #         # Forced connection is in the same room.  Remove 1 entrance & 1 exit from here.
            #         if self.verbose:
            #             print('\t\t\t\tforced connection in same room!')
            #         self_count[l_type] -= 1
            #         self_count[c_type] -= 1
            #         locked_protected.remove(fc)
            #     else:
            #         Rconn = self.rooms.get_room_from_element(fc)
            #         if self.verbose:
            #             print('\t\t\t\tforced connection in room:', Rconn.id)
            #         if Rconn.id in up_nodes:
            #             # Forced connection is upstream.  Remove 1 exit from here & 1 entrance from upstream
            #             self_count[l_type] -= 1
            #             up_count[c_type] -= 1
            #             if self.verbose:
            #                 print('\t\t\t\t... in upstream')
            #         elif Rconn.id in down_nodes:
            #             # Forced connection is downstream.  Remove 1 exit from here & 1 entrance from downstream
            #             self_count[l_type] -= 1
            #             down_count[c_type] -= 1
            #             if self.verbose:
            #                 print('\t\t\t\t... in downstream')
            # for lp in locked_protected:
            #     if self.verbose:
            #         print('\t\t\tFound locked forced connection:', lp, 'in', room_id)
            #     # already handled case where lf and lp are in the same room
            #     [l_type, c_type] = [[0, 2][[True, False].index(room.element_type(lp) == 0)],
            #                         [0, 1][[True, False].index(room.element_type(lp) == 0)]]
            #     fc = [lf for lf in forced_connections.keys() if lp in forced_connections[lf]][0]
            #     if self.verbose:
            #         print('\t\t\t\t-->', fc)
            #     Rconn = self.rooms.get_room_from_element(fc)
            #     if self.verbose:
            #         print('\t\t\t\tForced connection is in room:', Rconn.id)
            #     if Rconn.id in up_nodes:
            #         # Forced connection is upstream.  Remove 1 entrance from here & 1 exit from upstream
            #         self_count[l_type] -= 1
            #         up_count[c_type] -= 1
            #         if self.verbose:
            #             print('\t\t\t\t... in upstream')
            #     elif Rconn.id in down_nodes:
            #         # Forced connection is downstream.  Remove 1 entrance from here & 1 exit from downstream
            #         self_count[l_type] -= 1
            #         down_count[c_type] -= 1
            #         if self.verbose:
            #             print('\t\t\t\t... in downstream')

            # Assess classifications
            #if self.verbose:
            #    print('\t\tbug hunting 1: ', up_count, self_count, down_count)
            door_in = (up_count[0] + self_count[0]) > 0
            door_out = (down_count[0] + self_count[0]) > 0
            is_dead_end = (sum(up_count) == 0) and (sum(down_count) == 0) and (sum(self_count[1:3]) == 0) and (self_count[0] == 1)
            if is_dead_end:
                dead_end_count += 1
            else:
                doors_in_non_dead_ends += self_count[0]  # (up_count[0] + down_count[0] + self_count[0])
            exit_is_locked_internally = (len([d for d in room.locked() if room.element_type(d) == 0 and set(room.get_key(d)).issubset(room.keys)]) > 0)

            # Handle special case (avoid double counting self exits)
            door_in_door_out = (door_in and down_count[0] > 0) or (door_out and up_count[0] > 0) or (self_count[0] > 1)
            pit_in = (up_count[2] + self_count[2]) > 0
            trap_out = (down_count[1] + self_count[1]) > 0

            # Count total doors in/out OF THIS NODE
            #if self.verbose:
            #    print('\t\tbug hunting 2: ', door_in, door_out, door_in_door_out, pit_in, trap_out)
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

            #if self.verbose:
            #    print('\t\tbug hunting 3: ', delta_in, delta_out, delta_either)

            total_doors_in += delta_in
            total_doors_out += delta_out
            total_doors_either += delta_either

            #if self.verbose:
            #    print('\t\tbug hunting 4: ', total_doors_in, total_doors_out, total_doors_either)
            # For each node: [(door in, door out), (door in, trap out), (pit in, door out), (pit in, trap out)]
            classifications[room_id] = [door_in_door_out, door_in and trap_out, pit_in and door_out, pit_in and trap_out,
                                     [list(up_count), list(self_count), list(down_count)],
                                     [delta_in, delta_out, delta_either],
                                       is_dead_end and exit_is_locked_internally ]

            #if self.verbose:
            #    print('\t\tbug hunting 5: ', classifications[room_id])

        #if self.verbose:
        #    print('\t\tbug hunting 6: room analysis complete.')

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
        # Note that Rule_E should not be necessary: there should be no way to form new dead ends that aren't the active
        # room, which would be immediately connected.  Also, Rule E is false if the last connection is a door.
        Rule_E = (dead_end_count > doors_in_non_dead_ends)
        # If there are any dead ends with internally locked exits, fail immediately.
        Rule_F = [cl[6] for cl in classifications.values()].count(True) > 0

        #if self.verbose:
        #    print('\t\tbug hunting 7: ', DiDo, DiTo, PiDo, PiTo, Rule_A, Rule_B, Rule_C, Rule_D)
        if self.verbose and (sum(total_self_count == total_count[:3]) < 3):
            print('WARNING: total count', total_count, 'not equal to total self count', total_self_count)

        return [
            Rule_A or Rule_B or Rule_C or Rule_D or Rule_F,
            [Rule_A, Rule_B, Rule_C, Rule_D, Rule_E, Rule_F],
            [DiDo, DiTo, PiDo, PiTo],
            classifications,
            [total_doors_in, total_doors_out, total_doors_either],
            [dead_end_count, doors_in_non_dead_ends]
        ]

    def connect_network(self):
        if self.should_stop and self.should_stop.is_set():
            raise TimeoutError('Operation cancelled')

        net_state = deepcopy(self)

        if sum(net_state.rooms.count[:3]) == 0:
            return net_state
        else:
            [invalidity, by_rules, classification, cl, td, dec] = net_state.check_network_invalidity()
            if self.verbose:
                print('Network classification: ', classification)
            if invalidity:
                if self.verbose:
                    print('\tInvalid! By rule: ',
                          [['A','B','C','D','E','F'][i] for i in range(len(by_rules)) if by_rules[i]],
                          'in/out/either = ', td, ', deadends/other doors = ', dec)
                    for k in cl.keys():
                        print('\t',k.id,': ', cl[k])
                raise Exception('Invalid network state.')
            else:
                if self.verbose:
                    print('\tValid! in/out/either = ', td, ', deadends/other doors = ', dec)

            # Get active room - now using ID instead of index
            R_active = self.rooms.get_room(self.active)
            if self.verbose:
                print('Active node: ', R_active.id)
                #print('classified nodes: ', [r.id for r in cl.keys()])
                #r_classified = [r for r in cl.keys() if r.id == R_active.id][0]

            # Rest of method remains similar but uses new Room/Rooms methods
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
                      R_active.keys, ', L: ', R_active.locks, '. [U/s/D]:', cl[R_active.id][4])
            for node_id in net_state.get_downstream_nodes(R_active.id):
                # Collect exits from downstream nodes.
                ### AS WE DO THIS: do we need to look for keys & apply them?  but only along the present branch???
                node = self.rooms.get_room(node_id)
                node_exits = [[d for d in node.doors], [t for t in node.traps]]
                if self.verbose:
                    print('\t' + str(node_id) + ': ', node_exits, ' - (', node.count[:3], '). K: ', node.keys, ', L: ',
                          node.locks, '. [U/s/D]:', cl[node_id][4])
                possible_exits[0] += node_exits[0]
                possible_exits[1] += node_exits[1]

            possible_exits = possible_exits[0] + possible_exits[1]
            random.shuffle(possible_exits)  # randomize order

            forced_exits = [f for f in possible_exits if f in forced_connections.keys()]
            #for f in forced_exits:
            #    possible_exits.remove(f)
            #possible_exits = possible_exits + forced_exits
            # If there are any forced exits, only connect these.  Fail fast!
            if len(forced_exits) > 0:
                possible_exits = [forced_exits[0]]

            # Start trying exits
            while len(possible_exits) > 0:
                d1 = possible_exits.pop()
                R1 = net_state.rooms.get_room_from_element(d1)
                d1_type = R1.element_type(d1)
                if self.verbose:
                    print('selected: ', d1, ', type ', d1_type, ' (', R1.id, ')')

                # if d1 was in a downstream node, R1 might have a key that hasn't been used yet.
                if R1.id is not R_active.id:
                    trail = [R1.id]
                    if R_active.id not in net_state.net.predecessors(R1.id):
                        # R_active is significantly upstream.  Find the traversed nodes.
                        trails = [p for p in net_state.get_upstream_paths(R1.id) if R_active.id in p]
                        if self.verbose:
                            print('trails = ', trails)
                        trail += trails[0][:trails[0].index(R_active.id)]
                        if self.verbose:
                            print('Traversed: ', [r for r in trail])
                    # Apply any keys found along the way.
                    for Rt_id in trail:
                        Rt = self.rooms.get_room(Rt_id)
                        for k in Rt.keys:
                            if self.verbose:
                                print('Found an unused key: ', k, 'in', Rt_id)
                            net_state.apply_key(k)

                # Collect possible entrances for d1
                possible_entrances = []
                if self.verbose:
                    print('Possible entrances: (', len(net_state.net.nodes), ' rooms)')
                for node_id in net_state.net.nodes:
                    node = self.rooms.get_room(node_id)
                    if d1_type == 0:
                        node_entr = [d for d in node.doors if d is not d1]
                    else:
                        node_entr = [p for p in node.pits]
                    if self.verbose:
                        print('\t' + str(node.id) + ': ', node_entr, ' - (', node.count[:3], '). K: ', node.keys,
                              ', L: ', node.locks, '. [U/s/D]:', cl[node.id][4])
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
                        net_state = net_backup  # reset the network

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
            room = self.rooms.get_room(node)
            nc = room.count
            return nc[:3] == [1, 0, 0] and nc[4] == 0

    def count_unprotected(self, room_id):
        """Count including locked elements"""
        r = self.rooms.get_room(room_id)
        #if self.verbose:
        #    print('\t\tcount unprotected rooms in', room_id)
        unprotected = np.array([
            len([d for d in r.alldoors if d not in self.protected]),
            len([d for d in r.alltraps if d not in self.protected]),
            len([d for d in r.allpits if d not in self.protected]),
        ]
        )
        #if self.verbose:
        #    print('\t\t\t', unprotected)
        return unprotected


## Coprogramming with Claude.ai to rewrite data classes
# Suggested re-implementation of Rooms by Claude
class RoomsError(Exception):
    """Base class for Rooms collection errors"""
    pass


class Rooms:
    """
    Collection class managing a set of Room objects with efficient lookups
    and element tracking.
    """

    def __init__(self, room_ids):
        """Initialize Rooms collection from list of room IDs"""
        # Main room storage
        self.rooms = {}  # id -> Room mapping

        # Reverse lookup maps for O(1) element location
        self._element_to_room = {}  # element_id -> room_id mapping

        # Initialize from room IDs
        for room_id in room_ids:
            self.add_room(Room(room_id, self))

    def add_room(self, room):
        """Add a room and index all its elements"""
        if room.id in self.rooms:
            raise RoomsError(f"Room {room.id} already exists")

        # Add room to main storage
        self.rooms[room.id] = room

        # Index all elements
        self._index_room_elements(room)

    def _index_room_elements(self, room):
        """Index all elements in a room for reverse lookup"""
        # Index standard elements
        for element_type in ['doors', 'traps', 'pits', 'keys']:
            for element in room.elements[element_type]:
                self._element_to_room[element] = room.id

        # Recursively index locked elements
        def index_locked_items(items):
            for item in items:
                if isinstance(item, dict):
                    # Recurse into nested locks
                    for nested_items in item.values():
                        index_locked_items(nested_items)
                else:
                    self._element_to_room[item] = room.id

        # Index all locked elements including nested ones
        for locked_items in room.elements['locks'].values():
            index_locked_items(locked_items)

    def _unindex_room_elements(self, room):
        """Remove all element indexes for a room"""
        for element in self._element_to_room.copy():
            if self._element_to_room[element] == room.id:
                del self._element_to_room[element]

    def remove(self, room_id):
        """Remove a room and all its element indexes"""
        if isinstance(room_id, Room):
            room_id = room_id.id

        if room_id not in self.rooms:
            return False

        # Remove element indexes
        self._unindex_room_elements(self.rooms[room_id])

        # Remove room
        del self.rooms[room_id]
        return True

    def reindex_room(self, room_id):
        """Reindex all elements in a room after lock changes"""
        if isinstance(room_id, Room):
            room_id = room_id.id

        if room_id not in self.rooms:
            raise RoomsError(f"Cannot reindex non-existent room {room_id}")

        # Remove old indexes
        self._unindex_room_elements(self.rooms[room_id])
        # Create new indexes
        self._index_room_elements(self.rooms[room_id])

    def notify_lock_change(self, room_id):
        """Called by Room when its locks are modified"""
        if room_id in self.rooms:
            self.reindex_room(room_id)

    def get_room(self, room_id):
        """Get room by ID"""
        return self.rooms.get(room_id)

    def get_room_from_element(self, element_id):
        """Get room containing an element, O(1) lookup"""
        room_id = self._element_to_room.get(element_id)
        return self.rooms.get(room_id)

    def update_room_id(self, old_id, new_id):
        """Update a room's ID and maintain all mappings"""
        if old_id not in self.rooms:
            raise RoomsError(f"Room {old_id} not found")
        if new_id in self.rooms:
            raise RoomsError(f"Room {new_id} already exists")

        # Get the room and update its ID
        room = self.rooms[old_id]
        room.id = new_id

        # Update the rooms dictionary
        self.rooms[new_id] = room
        del self.rooms[old_id]

        # Update element to room mappings
        for element, room_id in self._element_to_room.items():
            if room_id == old_id:
                self._element_to_room[element] = new_id


    @property
    def count(self):
        """Count of all elements by type across all rooms"""
        totals = [0, 0, 0, 0, 0]  # [doors, traps, pits, keys, locks]
        for room in self.rooms.values():
            for i, count in enumerate(room.count):
                totals[i] += count
        return totals

    # Collection-like behavior
    def __iter__(self):
        return iter(self.rooms.values())

    def __len__(self):
        return len(self.rooms)

    def __contains__(self, item):
        if isinstance(item, str):
            return item in self.rooms
        elif isinstance(item, Room):
            return item.id in self.rooms
        return False

    # Element collection properties
    @property
    def doors(self):
        """List of all unlocked doors"""
        doors = []
        for room in self.rooms.values():
            doors.extend(room.doors)
        return doors

    @property
    def traps(self):
        """List of all unlocked traps"""
        traps = []
        for room in self.rooms.values():
            traps.extend(room.traps)
        return traps

    @property
    def pits(self):
        """List of all unlocked pits"""
        pits = []
        for room in self.rooms.values():
            pits.extend(room.pits)
        return pits

    @property
    def keys(self):
        """List of all unlocked keys"""
        keys = []
        for room in self.rooms.values():
            keys.extend(room.keys)
        return keys

    @property
    def locks(self):
        """List of all lock keys"""
        locks = []
        for room in self.rooms.values():
            locks.extend(room.elements['locks'].keys())
        return locks

    @property
    def locked(self):
        """List of all locked elements"""
        locked = []
        for room in self.rooms.values():
            locked.extend(room.locked())
        return locked

    @property
    def alldoors(self):
        """List of all doors (unlocked and locked)"""
        doors = []
        for room in self.rooms.values():
            doors.extend(room.alldoors)
        return doors

    @property
    def alltraps(self):
        """List of all traps (unlocked and locked)"""
        traps = []
        for room in self.rooms.values():
            traps.extend(room.alltraps)
        return traps


# Suggested re-implementation of Room by Claude.ai
class RoomError(Exception):
    """Base class for Room-related errors"""
    pass


class InvalidElementError(RoomError):
    """Raised when an element ID is invalid"""
    pass


class LockError(RoomError):
    """Raised for lock-related errors"""
    pass


class Room:
    """
    A room in the map containing doors, traps, pits, keys, and locks.
    Elements are identified by:
    - doors: integers < 2000
    - traps: integers 2000-2999
    - pits: integers >= 3000
    - keys: strings
    - locks: dictionary mapping key strings to lists of locked elements
    """

    verbose = False  # Class-level verbose flag

    def __init__(self, room_id=None, rooms_ref=None):
        """Initialize a room with optional room_data"""
        self.id = room_id
        self.rooms_ref = rooms_ref  # Reference to parent Rooms collection
        self.elements = {
            'doors': set(),
            'traps': set(),
            'pits': set(),
            'keys': set(),
            'locks': {}
        }

        if room_id in room_data.keys():
            # Load from room_data if ID provided
            data = room_data[room_id]
            if len(data) == 4:  # Old format without keys/locks
                contents = list(data[:-1]) + [[], {}]
            else:
                contents = data[:-1]

            # Initialize elements
            self.add_doors(contents[0])
            self.add_traps(contents[1])
            self.add_pits(contents[2])
            self.add_keys(contents[3])
            self.add_locks(contents[4])

            # Handle shared exits
            self._handle_shared_exits()

    def _handle_shared_exits(self):
        """Remove shared exits defined in shared_exits global"""
        shared_doors = [d for d in self.alldoors if d in shared_exits]
        for door in shared_doors:
            for shared in shared_exits[door]:
                self.remove(shared)

    def _validate_element(self, element_id, expected_type):
        """
        Validate element ID matches expected type.
        Returns element_id if valid, raises InvalidElementError if not.
        Element ID allocations:
            0--1999:  doors of various types
                0--1128: short exits in original game
                1129--1280:  long exits in original game
                1500--1999:  reserved for event tiles operating as doors
            2000--2999:  one-way exits ('traps') in original game
            3000--3999:  one-way entrances ('pits') in original game.
                For original connections, trap_id + 1000 = pit_id
            4000--5999:  logical (WOR) exits on shared maps
                For original connections,  door_id + 4000 = logical_wor_id
            6000--7999:  one-way entrances (pits) associated with rare doors that act as one-ways (see below)

        Exceptions: doors in doma dream that act as one-way exits
            [843, 844, 845, 846, 847, 848, 849, 852, 853, 854, 859, 862]:
        """
        if expected_type == 'doors':
            if not isinstance(element_id, int) or (element_id >= 2000 and element_id < 4000) or (element_id in doors_as_traps):
                raise InvalidElementError(f"Invalid door ID: {element_id}")
        elif expected_type == 'traps':
            if not isinstance(element_id, int) or not ((2000 <= element_id < 3000) or element_id in doors_as_traps):
                raise InvalidElementError(f"Invalid trap ID: {element_id}")
        elif expected_type == 'pits':
            if not isinstance(element_id, int) or not ((3000 <= element_id < 4000) or (6000 <= element_id < 8000)):
                raise InvalidElementError(f"Invalid pit ID: {element_id}")
        elif expected_type == 'keys':
            if not isinstance(element_id, str):
                raise InvalidElementError(f"Invalid key ID: {element_id}")
        return element_id

    def _add_elements(self, element_type, elements):
        """Add multiple elements of the same type"""
        for element in elements:
            validated = self._validate_element(element, element_type)
            self.elements[element_type].add(validated)

    def add_doors(self, doors):
        self._add_elements('doors', doors)

    def add_traps(self, traps):
        self._add_elements('traps', traps)

    def add_pits(self, pits):
        self._add_elements('pits', pits)

    def add_keys(self, keys):
        self._add_elements('keys', keys)

    def add_locks(self, lock_dict):
        """Add locks with validation"""
        for key, locked_items in lock_dict.items():
            #if not isinstance(key, str):
            #    raise LockError(f"Lock key must be string, got: {key}")
            if not isinstance(key, (list, tuple)):
                key = (key,)
            key_tuple = tuple(sorted(key))
            if key_tuple in self.elements['locks']:
                if self.verbose:
                    print(f"Warning: Merging lock {key_tuple} in room {self.id}")
                self.elements['locks'][key_tuple].extend(locked_items)
            else:
                self.elements['locks'][key_tuple] = locked_items

        # Notify parent collection of lock changes
        if self.rooms_ref is not None:
            self.rooms_ref.notify_lock_change(self.id)

    def remove(self, element_id):
        """Remove an element from the room"""
        # Try direct removal from element sets
        for element_type, elements in self.elements.items():
            if element_type != 'locks' and element_id in elements:
                elements.remove(element_id)
                if self.verbose:
                    print(f"Removed {element_id} from {self.id}")
                return True

        # Check locks
        for key, locked_items in list(self.elements['locks'].items()):
            if element_id in locked_items:
                locked_items.remove(element_id)
                if self.verbose:
                    print(f"Removed locked item {element_id} from lock {key} in room {self.id}")
                # Remove empty locks
                if not locked_items:
                    del self.elements['locks'][key]
                    if self.verbose:
                        print(f"Removed empty lock {key}")
                return True

        return False

    def extract_locked(self, lock_dict):
        """Recursively extract all locked elements"""
        elements = []
        for locked_items in lock_dict.values():
            for item in locked_items:
                if isinstance(item, dict):
                    elements.extend(self.extract_locked(item))
                else:
                    elements.append(item)
        return elements

    def locked(self, element_type=None):
        """Get locked elements, optionally filtered by type"""
        locked_elements = self.extract_locked(self.elements['locks'])

        if element_type is None:
            return locked_elements

        if element_type in ['doors', 0]:
            return [d for d in locked_elements if isinstance(d, int) and d < 2000]
        elif element_type in ['traps', 1]:
            return [d for d in locked_elements if isinstance(d, int) and 2000 <= d < 3000]
        elif element_type in ['pits', 2]:
            return [d for d in locked_elements if isinstance(d, int) and d >= 3000]
        elif element_type in ['keys', 3]:
            return [d for d in locked_elements if isinstance(d, str)]

        return []

    def get_key(self, locked_element):
        """Find all keys needed to access a locked element.
        Returns a list of keys in order from outermost to innermost lock.
        Returns empty list if element is not locked."""

        def find_in_locks(element, lock_dict):
            for key, items in lock_dict.items():
                # Check direct containment
                if element in items:
                    return tuple(key)
                # Check nested locks
                for item in items:
                    if isinstance(item, dict):
                        nested_keys = find_in_locks(element, item)
                        if nested_keys:
                            return tuple(key) + nested_keys
            return tuple()

        return find_in_locks(locked_element, self.elements['locks'])

    def contains(self, element_id):
        """Check if room contains an element"""
        return any(
            element_id in elements
            for element_type, elements in self.elements.items()
            if element_type != 'locks'
        ) or element_id in self.locked()

    def element_type(self, element_id):
        """Get the type (0-3) of an element"""
        """Element ID allocations:
            0--1999:  doors of various types
                0--1128: short exits in original game
                1129--1280:  long exits in original game
                1500--1999:  reserved for event tiles operating as doors
            2000--2999:  one-way exits ('traps') in original game
            3000--3999:  one-way entrances ('pits') in original game.
                For original connections, trap_id + 1000 = pit_id
            4000--5999:  logical (WOR) exits on shared maps
                For original connections,  door_id + 4000 = logical_wor_id
            6000--7999:  one-way entrances (pits) associated with rare doors that act as one-ways (see below)

        Exceptions: doors in doma dream that act as one-way exits
        Calculated in data.rooms:
            doors_as_traps = [843, 844, 845, 846, 847, 848, 849, 852, 853, 854, 859, 862]
        """
        if isinstance(element_id, str) or element_id in self.elements['keys']:
            return 3
        if (element_id < 2000 or (4000 <= element_id < 6000)) and element_id not in doors_as_traps:
            return 0
        if (2000 <= element_id < 3000) or element_id in doors_as_traps:
            return 1
        if (3000 <= element_id < 4000) or (6000 <= element_id < 8000):
            return 2
        return False

    def get_elements(self, element_type):
        """Get all elements of a given type"""
        if element_type in [0, 'doors']:
            return list(self.elements['doors'])
        elif element_type in [1, 'traps']:
            return list(self.elements['traps'])
        elif element_type in [2, 'pits']:
            return list(self.elements['pits'])
        elif element_type in [3, 'keys']:
            return list(self.elements['keys'])
        elif element_type in [4, 'locks']:
            return list(self.elements['locks'].keys())
        elif element_type in [5, 'locked']:
            return list(self.elements['locks'].values())
        return []

    def get_exit(self):
        """Get a random exit (door or trap)"""
        exits = list(self.elements['doors']) + list(self.elements['traps'])
        return random.choice(exits) if exits else None

    def is_attachable(self):
        """Check if room can be attached to a dead end"""
        all_doors = self.alldoors
        all_traps = self.alltraps
        all_pits = self.elements['pits']
        return (len(all_doors) > 1 or
                (len(all_doors) == 1 and len(all_traps) > 0 and len(all_pits) > 0))

    # Properties
    @property
    def doors(self):
        return list(self.elements['doors'])

    @property
    def traps(self):
        return list(self.elements['traps'])

    @property
    def pits(self):
        return list(self.elements['pits'])

    @property
    def keys(self):
        return list(self.elements['keys'])

    @property
    def locks(self):
        return self.elements['locks']

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
        """Count of each basic element type"""
        return [
            len(self.elements['doors']),
            len(self.elements['traps']),
            len(self.elements['pits']),
            len(self.elements['keys']),
            len(self.elements['locks'])
        ]

    @property
    def full_count(self):
        """Count including locked elements"""
        return np.array(self.count[:4]) + np.array([
            len(self.locked('doors')),
            len(self.locked('traps')),
            len(self.locked('pits')),
            len(self.locked('keys'))
        ])

