from data.rooms import room_data

class Walks:
    # Class for handling a group of Walks, i.e. logical mapping sequences for rooms
    def __init__(self, rooms, room_doors, room_counts):
        self.walks = []
        self.deadends = []
        self.room_doors = room_doors    # dictionary for [ [doors], [traps], [pits], [keys], [locks] ] in each room
        self.room_counts = room_counts  # count of [ doors, traps, pits, keys, locks ] in each room
        for r in rooms:
            if self.is_dead_end(r):
                self.deadends.append(r)
            else:
                self.walks.append(Walk([r]))

        self.active = 0  # Index of the active walk

    def is_dead_end(self, r):
        rc = self.room_counts[r]
        return rc[:3] == [1, 0, 0] and rc[4] == 0

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
    # Class for handling a logical mapping sequence for rooms
    def __init__(self, rooms):
        self.walk = []
        for r in rooms:
            self.walk.append(Room(r))

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
        for r in self.walk[inds[0]:inds[1]+1]:
            for i in range(len(looproom._contents)-1):
                looproom._contents[i].extend(r._contents[i])
            for k in r._contents[-1].keys():
                looproom._contents[-1][k] = r._contents[-1][k]
        self.walk = self.walk[:inds[0]] + [looproom] + self.walk[inds[1]+1:]

    def get_upstream_entr_count(self):
        pass

    def get_upstream_exit_count(self):
        pass


class Room():
    def __init__(self, r=None):
        if r is not None:
            if len(room_data[r]) == 4:
                # before implementing keys & locks
                self._contents = room_data[r][:-1] + [[], {}]
            else:
                self._contents = room_data[r][:-1]   # [ doors, traps, pits, keys, locks ]
            self.count = [len(d) for d in self._contents]
        else:
            self._contents = [ [], [], [], [], {}]
            self.count = [0, 0, 0, 0, 0]

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

