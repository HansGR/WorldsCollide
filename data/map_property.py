class MapProperty:
    DATA_SIZE = 33
    DATA_START = 0x2d8f00

    def __init__(self, rom, id):
        self.rom = rom

        self.set_id(id)
        self.read()

    def set_id(self, id):
        self.id = id
        self.data_start = self.DATA_START + self.id * self.DATA_SIZE

    def read(self):
        self.data = self.rom.get_bytes(self.data_start, self.DATA_SIZE)

        self.name_index = self.data[0]

        ##### read in layer effects flags
        self.enable_xzone = (self.data[1] & 0x01) >> 0
        self.warpable = (self.data[1] & 0x02) >> 1
        self.wavy_bg3 = (self.data[1] & 0x04) >> 2
        self.wavy_bg2 = (self.data[1] & 0x08) >> 3
        self.wavy_bg1 = (self.data[1] & 0x10) >> 4
        self.enable_spotlights = (self.data[1] & 0x20) >> 5
        self.load_timer_graphics = (self.data[1] & 0x80) >> 7
        ##### read in layer effects flags

        self.battle_properties = (self.data[5] & 0x7f) >> 6
        self.enable_random_encounters = (self.data[5] & 0x80) >> 7

        # map palettes and background animations
        self.paletteindex = self.data[25]
        self.paletteanimationindex = self.data[26]
        self.backgroundanimations = self.data[27]
        # map palettes and background animations

        self.song = self.data[28]

    def write(self):
        ##### write layer effects flags
        self.data[1] = self.enable_xzone << 0
        self.data[1] |= self.warpable << 1
        self.data[1] |= self.wavy_bg3 << 2
        self.data[1] |= self.wavy_bg2 << 3
        self.data[1] |= self.wavy_bg1 << 4
        self.data[1] |= self.enable_spotlights << 5
        self.data[1] |= self.load_timer_graphics << 7

        ##### write random encounter flags
        self.data[5] = self.battle_properties << 6
        self.data[5] |= self.enable_random_encounters << 7

        self.data[25] = self.paletteindex
        self.data[26] = self.paletteanimationindex
        self.data[27] = self.backgroundanimations
        self.data[28] = self.song
        self.rom.set_bytes(self.data_start, self.data)

    def print(self):
        # print(f"{self.id}: {self.enable_random_encounters}")
        print(f"{self.id}: {self.warpable} | {self.enable_random_encounters}")
