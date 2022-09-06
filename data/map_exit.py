class ShortMapExit():
    DATA_SIZE = 0x06

    def __init__(self):
        self.x = 0
        self.y = 0

        ### mod for exit rando, sync up with longmapexit
        self.index = 0
        self.parent_map = 0
        self.size = 0
        self.direction = 0
        self.dest_map = 0
        self.unknown = 0
        self.facing = 0
        self.dest_x = 0
        self.dest_y = 0
        ### mod for exit rando, sync up with longmapexit

    def from_data(self, data):
        assert(len(data) == self.DATA_SIZE)

        self.x = data[0]
        self.y = data[1]
        self.dest_map = data[2] | (data[3] & 0x01) << 8
        ### mod for exit details
        #print(str(data[2]) + " | " + str(data[3]))
        self.refreshparentmap = (data[3] & 0x02) >> 1
        self.enterlowZlevel = (data[3] & 0x04) >> 2
        self.displaylocationname = (data[3] & 0x08) >> 3
        self.facing = (data[3] & 0x30) >> 4  #0 = north, 1 = east, 2 = south, 3 = west
        ### mod for exit details
        #self.unknown = data[3] & 0xfe  ##this is wrong now that we are using more than the first bit
        self.unknown = data[3] & 0xC0
        self.dest_x = data[4]
        self.dest_y = data[5]

    def to_data(self):
        data = [0x00] * self.DATA_SIZE

        data[0] = self.x
        data[1] = self.y
        data[2] = self.dest_map & 0xff
        data[3] = ((self.dest_map & 0x100) >> 8) | self.unknown
        # mod for exit rando
        data[3] |= self.facing << 4
        #print(str(data[2]) + " | " + str(data[3]))
        # mod for exit rando
        data[4] = self.dest_x
        data[5] = self.dest_y

        return data

    def print(self):
        #print("{}, {} -> {}: {}, {} ({})".format(self.x, self.y, hex(self.dest_map), self.dest_x, self.dest_y, self.hex(self.unknown)))
        #print(str(self.x) + " | " + str(self.y) + " | " + str(self.dest_map) + " | " +
              #str(self.dest_x) + " | " + str(self.dest_y) + " | " + str(self.facing) + " | " + 
              #str(self.displaylocationname) + " | " + str(self.refreshparentmap) + " | " +
              #str(self.unknown))
        tmp = ((self.dest_map & 0x100) >> 8) | self.unknown
        tmp |= self.facing << 4
        print(str(self.index) + " | " + str(self.parent_map) + " | " +
              str(self.x) + " | " + str(self.y) + " | " + str(self.dest_map) + " | " +
              str(self.dest_x) + " | " + str(self.dest_y) + " | " + str(self.facing) + " | " + 
              str(self.displaylocationname) + " | " + str(self.refreshparentmap) + " | " +
              str(self.unknown) + " | " + str(self.size) + " | " + str(self.direction) + " | " + 
              str(self.dest_map & 0xff) + " | " + str(tmp))
        
class LongMapExit():
    DATA_SIZE = 0x07

    def __init__(self):
        self.x = 0
        self.y = 0

        ### mod for exit rando
        self.index = 0
        self.parent_map = 0
        self.size = 0
        self.direction = 0
        self.dest_map = 0
        self.unknown = 0
        self.facing = 0
        self.dest_x = 0
        self.dest_y = 0
        ### mod for exit rando

    def from_data(self, data):
        assert(len(data) == self.DATA_SIZE)

        self.x = data[0]
        self.y = data[1]
        self.size = data[2] & 0x7f  #tile length
        self.direction = data[2] & 0x80 # 0 = horizontal, 128 = vertical
        self.dest_map = data[3] | (data[4] & 0x01) << 8
        ### mod for exit details
        #print(str(data[3]) + " | " + str(data[4]))
        self.refreshparentmap = (data[4] & 0x02) >> 1
        self.enterlowZlevel = (data[4] & 0x04) >> 2
        self.displaylocationname = (data[4] & 0x08) >> 3
        self.facing = (data[4] & 0x30) >> 4  #0 = north, 1 = east, 2 = south, 3 = west
        ### mod for exit details
        #self.unknown = data[3] & 0xfe  ##this is wrong now that we are using more than the first bit
        self.unknown = data[3] & 0xC0
        self.dest_x = data[5]
        self.dest_y = data[6]

    def to_data(self):
        data = [0x00] * self.DATA_SIZE

        data[0] = self.x
        data[1] = self.y
        data[2] = self.size | self.direction
        data[3] = self.dest_map & 0xff
        data[4] = ((self.dest_map & 0x100) >> 8) | self.unknown
        # mod for exit rando
        data[4] |= self.facing << 4
        #print(str(data[3]) + " | " + str(data[4]))
        # mod for exit rando
        data[5] = self.dest_x
        data[6] = self.dest_y

        return data

    def print(self):
        #print("{}, {} {}, {} -> {}: {}, {}".format(self.x, self.y, self.size, self.direction, hex(self.dest_map), self.dest_x, self.dest_y))
        tmp = ((self.dest_map & 0x100) >> 8) | self.unknown
        tmp |= self.facing << 4
        print(str(self.index) + " | " + str(self.parent_map) + " | " +
              str(self.x) + " | " + str(self.y) + " | " + str(self.dest_map) + " | " +
              str(self.dest_x) + " | " + str(self.dest_y) + " | " + str(self.facing) + " | " + 
              str(self.displaylocationname) + " | " + str(self.refreshparentmap) + " | " +
              str(self.unknown) + " | " + str(self.size) + " | " + str(self.direction) + " | " + 
              str(self.dest_map & 0xff) + " | " + str(tmp))
