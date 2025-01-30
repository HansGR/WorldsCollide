from memory.space import *
import data.event_bit as event_bit
import data.direction as direction
import instruction.field as field

KT_CHECK_ADDR = 0xa014f
CUSTOM_WARP_HOOK = 0xa0138
CUSTOM_WARP_BITS = [event_bit.PHOENIX_CAVE_WARP_OPTION,
                    event_bit.FLOATING_CONTINENT_WARP_OPTION,
                    event_bit.ANCIENT_CASTLE_WARP_OPTION]

SAVE_POINT_DATA = {
    # 'Name':          [map_id, x, y, npc_id, npc_bit, address of associated event tile]
    'Scenario':         [0x009, 8, 6, 0x15, 0x632, 0xc9aeb],    # Map unused in WC
    'Snowfield_WOB':    [0x016, 25, 5, 0x26, 0x633, 0xcc581],   # special event for K@N, edited in WC
    'Snowfield_WOR':    [0x022, 25, 5, 0x10, 0x632, 0xc9aeb],
    'Narshe_mineWOB':   [0x029, 33, 22, 0x10, 0x632,  0xc9aeb],  # removed in WC
    'Narshe_caves':     [0x032, 66, 41, 0x14, 0x632, 0xc9aeb],
    'SF_duncan_house':  [0x054, 53, 57, 0x10, 0x632, 0xc9aeb],
    'SF_prison_cell':   [0x058, 11, 34, 0x10, 0x632, 0xc9aeb],
    'Mt_Kolts':         [0x067, 57,  8, 0x10, 0x632, 0xc9aeb],
    'Narshe_school':    [0x06b, 60, 32, 0x10, 0x690, 0xc9aeb],
    'Returners':        [0x06e, 50, 39, 0x17, 0x632, 0xc9aeb],
    'Lete_1':           [0x072, 20, 21, 0x12, 0x632, 0xc9aeb],
    'Lete_2':           [0x072, 6, 13, 0x13, 0x632, 0xc9aeb],
    'Dream_Doma':       [0x07e, 8, 8, 0x13, 0x548, 0xc9aeb],
    'Train_caboose':    [0x092, 20, 10, 0x11, 0x632, 0xc9aeb],  # ALSO DREAM!
    'Train_mid':        [0x095, 24, 6, 0x13, 0x632, 0xc9aeb],
    'Train_front':      [0x099, 8, 9, 0x11, 0x517, 0xc9aeb],  # ALSO DREAM
    'Mt_Zozo':          [0x0b3, 40, 15, 0x11, 0x632, 0xc9aeb],
    'Owzer_basement':   [0x0cf, 87, 41, 0x15, 0x632, 0xc9aeb],
    'Vector_MTek3':     [0x0f0, 58,  7, 0x19, 0x6ae,  0xc9aeb],
    'MTek_pit':         [0x10e, 25, 10, 0x10, 0x632, 0xc9aeb],
    'MTek_minecart':    [0x110, 3, 55, 0x12, 0x632, 0xc9aeb],
    'Zoneeater':        [0x117, 24, 4, 0x10, 0x632, 0xc9aeb],
    'KT_Guardian':      [0x123, 12, 12, 0x19, 0x6ba, 0xc9aeb],
    'Daryl_tomb':       [0x12c, 122, 14, 0x12, 0x632, 0xc9aeb],
    'Phoenix_exit':     [0x139, 14, 47, 0x12, 0x693, 0xc215e],  # Not a save point!  it's the warp point!
    'Phoenix_cave':     [0x13b, 37, 28, 0x11, 0x632, 0xc9aeb],
    'Dream_stairs':     [0x13d, 23, 53, 0x2d, 0x632, 0xc9aeb],
    'Dream_train_1':    [0x142, 28, 5, 0x10, 0x632, 0xc9aeb],
    'KT_Atma':          [0x14b, 76, 51, 0x11, 0x6be, 0xc9aeb],
    'Veldt_cave':       [0x161, 57, 44, 0x10, 0x632, 0xc9aeb],
    'KT_Goddess':       [0x162, 12, 31, 0x13, 0x6b9, 0xc9aeb],
    'KT_Doom':          [0x163, 64, 11, 0x16, 0x6b8, 0xc9aeb],
    'FloatingC_cave':   [0x166, 8, 10, 0x10, 0x632, 0xc9aeb],
    'EsperMtn':         [0x177, 8, 44, 0x10, 0x632, 0xc9aeb],
    'SealedGate':       [0x182, 74, 53, 0x10, 0x632, 0xc9aeb],
    'FloatingC_land':   [0x18a, 7, 12, 0x22, 0x632, 0xc9aeb],
    'AncientCastle':    [0x192, 22, 51, 0x10, 0x632, 0xc9aeb],
    'EbotsRock':        [0x195, 7, 5, 0x12, 0x632, 0xc9aeb],
    'KT_inferno':       [0x19a, 37, 17, 0x11, 0x632, 0xc9aeb],
    'KT_statue2':       [0x19c, 82, 47, 0x10, 0x632, 0xc9aeb],
}

class Warps():

    def __init__(self):
        self.verbose = False

        # List of custom warps to add
        self.warps = []

        # bits to be set/cleared by all warp actions.  Initial values from 0xa0159
        self.bits = {
            event_bit.DARYL_TOMB_TURTLE1_MOVED: 'clear',
            event_bit.DARYL_TOMB_TURTLE2_MOVED: 'clear',
        }

        # additional code to run
        self.additional_code = []

        # warp override
        self.warp_override = None

    def add_warp(self, event_bit, warp_code):
        new_warp = Warp(event_bit, warp_code)
        self.warps.append(new_warp)
        if self.verbose:
            print('Added custom warp: ', hex(event_bit), '@ address: ', hex(warp_code))

    def add_bit(self, bit, setting):
        if setting in ['clear', 'set']:
            self.bits[bit] = setting
            if self.verbose:
                print('Added custom bit set to warp: ', hex(bit), ' --> ', setting)
        else:
            print('warning: bad setting', hex(bit), setting)

    def add_code(self, src):
        self.additional_code.extend(src)

    def add_warp_override(self, src):
        self.warp_override = src

    def mod(self):
        # (1) Set/Clear required bits
        src = []
        for b in self.bits.keys():
            if self.bits[b] == 'clear':
                src += [field.ClearEventBit(b)]
            elif self.bits[b] == 'set':
                src += [field.SetEventBit(b)]

        # (2) run additional code
        src += self.additional_code

        # (3) check for individual warp conditions
        for warp in self.warps:
            src += [field.BranchIfEventBitSet(warp.event_bit, warp.code_addr)]

        # Add KT check last
        src += [field.BranchIfEventBitSet(event_bit.KT_WARP_OPTION, KT_CHECK_ADDR)]

        # (4a) if warp_override is not None use warp override code
        if self.warp_override is not None:
            src += self.warp_override

        # (4b) otherwise, use return to parent map
        else:
            # Load map $01FF (world map) instantly, (upper bits $2400), place party at (0, 0), facing down
            src += [field.LoadMap(0x1ff, x=0, y=0, default_music=True, direction=direction.DOWN,
                                         fade_in = True, entrance_event = False)]  

        space = Write(Bank.CA, src, "modified custom warp handler")
        warp_handler_addr = space.start_address
        if self.verbose:
            print('Custom warp script:')
            for s in src:
                print('\t', s.__str__())

        space = Reserve(CUSTOM_WARP_HOOK, CUSTOM_WARP_HOOK+5, "branch to modified custom warp handler", field.NOP())
        space.write(field.Branch(warp_handler_addr))


class Warp():
    def __init__(self, event_bit, warp_code_addr):
        self.event_bit = event_bit
        self.code_addr = warp_code_addr
