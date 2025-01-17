from memory.space import *
import data.event_bit as event_bit
import data.direction as direction
import instruction.field as field

KT_CHECK_ADDR = 0xa014f
CUSTOM_WARP_HOOK = 0xa0138
CUSTOM_WARP_BITS = [event_bit.PHOENIX_CAVE_WARP_OPTION,
                    event_bit.FLOATING_CONTINENT_WARP_OPTION,
                    event_bit.ANCIENT_CASTLE_WARP_OPTION]


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
