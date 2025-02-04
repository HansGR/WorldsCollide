from memory.space import *
import data.event_bit as event_bit
import data.direction as direction
import instruction.field as field
import instruction.field.entity as field_entity
from data.npc import *
import data.npc_bit as npc_bit
from instruction.event import EVENT_CODE_START
from data.map_event import MapEvent

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
    'KT_Poltrgeist':       [0x19c, 82, 47, 0x10, 0x632, 0xc9aeb],
}


AVAILABLE_NPC_BITS = [     # list of available NPC bits for warp points
    0x337, 0x338, 0x339, 0x33a, 0x33b, 0x33c, 0x33d, 0x33e, 0x33f, 0x357, 0x35a, 0x35b, 0x35c, 0x35d,  # Esper World npcs
    0x62d, 0x62e, 0x630  # Imperial castle NPCs
]
NPC_OFF_BIT = 0x306      # An npc_bit that is always off in WC
WARP_DIALOG_IDS = [i for i in range(1426, 1426+2*len(AVAILABLE_NPC_BITS))]  # how many do we need? 2x # warp points...  # range(1426, 1491)
WARP_POINTS = {
    # "name":  [map_id, x, y, "Location name"] for warp location in Esper World
    #"Narshe_school":  [0x0d9, 35, 22, "Narshe classroom"],  # list of save points to convert to warp points
    'Snowfield_WOR':    [0x0d9, 35, 22, "Narshe snowfield"],
    'SF_prison_cell':   [0x0db, 7, 9, "South Figaro"],
    'Mt_Kolts':         [0x0d9, 38, 40, "Mount Kolts"],
    'Returners':        [0x0d9, 50, 42, "Returners Hideout"],
    'Train_caboose':    [0x0db, 39, 52, "Phantom Train"],
    'Owzer_basement':   [0x0d9, 28, 29, "Owzer's Mansion"],
    'MTek_pit':         [0x0db, 19, 29, "Magitek Factory"],
    'Zoneeater':        [0x0d9, 20, 30, "Zone Eater"],
    'Daryl_tomb':       [0x0d9, 24, 35, "Daryl's Tomb"],
    'Dream_stairs':     [0x0db, 47, 40, "Cyan's Dream"],
    'Veldt_cave':       [0x0d9, 40, 37, "Cave on the Veldt"],
    'EsperMtn':         [0x0db, 13, 50, "Esper Mountain"],
    'AncientCastle':    [0x0db, 33, 10, "Ancient Castle"],
    'KT_Doom':          [0x0d9, 26, 48, "Kefka's Tower left"],
    'KT_Poltrgeist':    [0x0d9, 28, 46, "Kefka's Tower center"],
	'KT_Goddess':       [0x0d9, 30, 48, "Kefka's Tower right"],
}
WARP_WORLD_MAPS = set([wp[0] for wp in WARP_POINTS.values()])

class WarpPoints:
    verbose = False

    def __init__(self):
        self.points = []
        for wp in WARP_POINTS.keys():
            new_point = WarpPoint(wp)
            point_texts = self.create_point_dialog_text(wp)
            new_point.activated_point_text = point_texts[0]
            new_point.warp_to_point_text = point_texts[1]

            self.points.append(new_point)

        self.npc_bits_available = [a for a in AVAILABLE_NPC_BITS]
        self.npc_bits_used = []

    def create_point_dialog_text(self, name):
        # Edit two dialog items to say the right thing;
        # return their dialog IDs
        location_name = WARP_POINTS[name][3]
        leading_spaces = " "*round((36 - len(location_name))/2)   # 10 + 16 + 10 = 36 characters per line
        return ["<line>" + leading_spaces + location_name + "<line>       warp point activated!<end>",
                "Warp to " + location_name + "?<line><choice> Yes<line><choice> No<end>"]


    def mod(self, dialogs, maps):
        # Set dialogs for warp points
        self.warp_to_esper_world_dialog = 0x05a6
        dialogs.set_text(self.warp_to_esper_world_dialog,
                         "Warp to the Esper world?<line><choice> Yes<line><choice> No<end>")

        # Write common animations for warp points
        self.warp_out_animation_addr = self.warp_out_animation()
        self.warp_in_animation_addr = self.warp_in_animation()


        for wp in self.points:
            # Choose an npc_bit for this point
            this_bit = self.npc_bits_available.pop()
            wp.npc_bit = this_bit
            self.npc_bits_used.append(this_bit)

            # Edit text
            wp.activated_point_dialog_id = WARP_DIALOG_IDS.pop()
            dialogs.set_text(wp.activated_point_dialog_id, wp.activated_point_text)

            wp.warp_to_point_dialog_id = WARP_DIALOG_IDS.pop()
            dialogs.set_text(wp.warp_to_point_dialog_id, wp.warp_to_point_text)

            # Write code & modify tile event
            dest = WARP_POINTS[wp.name][:3]
            src = self._warp_point_code(wp, dest)
            space = Write(Bank.CC, src, "warp point code "+wp.name)
            event_tile = maps.get_event(wp.map_id, wp.x, wp.y)
            event_tile.event_address = space.start_address - EVENT_CODE_START

            # Edit aesthetics
            wp_npc = maps.get_npc(wp.map_id, wp.npc_id)
            wp_npc.palette = 0  # Default = 6 (blue); Phoenix Cave warp = 5 (reddish)

            # Create pair warp point in Esper World
            self.make_warp_point_pair(wp, maps)

            if self.verbose:
                print('Modified warp point:', wp.name)

        # Deconflict used npc_bits
        ### APPARENTLY maps.get_npc_count gets out of whack at some point?  I'm not sure how.
        ### But this code was deactivating the new warp points in the esper world.
        ### Will just have to be careful with which NPC bits we use.
        # other_maps = [i for i in range(0x19f) if i not in WARP_WORLD_MAPS]
        # for map_id in other_maps:
        #     count = maps.get_npc_count(map_id)
        #     #if self.verbose:
        #     #    print('Getting NPCs on map', hex(map_id),': ', count)
        #     for npc_id in [i for i in range(count)]:
        #         npc = maps.get_npc(map_id, npc_id)
        #         this_npc_bit = npc.event_byte * 8 + npc.event_bit + 0x300
        #         if this_npc_bit in self.npc_bits_used:
        #             npc.event_byte = (NPC_OFF_BIT - 0x300) // 8
        #             npc.event_bit = (NPC_OFF_BIT - 0x300) % 8
        #             if self.verbose:
        #                 print('Deconflicted NPC', npc_id, 'on map', hex(map_id))



    def _warp_point_code(self, warp_point, destination):
        src = [
            field.BranchIfAll([0x1b5, True,
                               event_bit.PRESSING_A, True], "WARP_QUERY"),
            field.ReturnIfEventBitSet(0x1b5),
            field.PlaySoundEffect(0xd1),    # shing!
            field.FlashScreen(field.Flash.GREEN),
            field.SetEventBit(0x1b5),       # multipurpose bit: standing on savepoint
            field.SetEventBit(event_bit.SAVE_ENABLED),
            field.BranchIfEventBitClear(warp_point.npc_bit, "ENABLE_WARP"),
            field.FreeMovement(),
            field.Return(),
            "WARP_QUERY",
            field.DialogBranch(self.warp_to_esper_world_dialog, "DO_WARP", "RETURN"),
            "DO_WARP",
            field.Call(self.warp_out_animation_addr),
            field.FadeLoadMap(map_id=destination[0], x=destination[1], y=destination[2], direction=direction.DOWN,
                              default_music=True, entrance_event=True, fade_in=False),
            field.Call(self.warp_in_animation_addr),
            "RETURN",
            field.Return(),
            "ENABLE_WARP",
            field.SetEventBit(warp_point.npc_bit),
            field.Dialog(warp_point.activated_point_dialog_id),
            field.Return()
        ]
        if self.verbose:
            print('Warp point code: ', warp_point.name)
            print([s.__str__() for s in src])

        return src

    def _warp_point_pair_code(self, warp_point):
        src = [
            field.ReturnIfEventBitClear(warp_point.npc_bit),
            field.ReturnIfEventBitClear(event_bit.PRESSING_A),
            #field.PlaySoundEffect(0xd1),    # shing!
            #field.FlashScreen(field.Flash.GREEN),
            field.DialogBranch(warp_point.warp_to_point_dialog_id, "DO_WARP", "RETURN"),
            "DO_WARP",
            field.Call(self.warp_out_animation_addr),
            field.FadeLoadMap(map_id=warp_point.map_id, x=warp_point.x, y=warp_point.y, direction=direction.DOWN,
                              default_music=True, entrance_event=True, fade_in=False),
            field.Call(self.warp_in_animation_addr),
            "RETURN",
            field.Return(),
        ]
        if self.verbose:
            print('Warp point pair code: ', warp_point.name)
            print([s.__str__() for s in src])
        return src

    def warp_out_animation(self):
        # Animation for warping from a warp point
        src = [
            field.HoldScreen(),
            field.PlaySoundEffect(0x09),  # still need to pick this
            field.TintBackground(field.Tint.BLACK),
            field.Repeat(5,
                field.EntityAct(field_entity.PARTY0, True, field_entity.Turn(direction.LEFT)),
                field.EntityAct(field_entity.PARTY0, True, field_entity.Turn(direction.UP)),
                field.EntityAct(field_entity.PARTY0, True, field_entity.Turn(direction.RIGHT)),
                field.EntityAct(field_entity.PARTY0, True, field_entity.Turn(direction.DOWN)),
            ),
            field.DisableEntityCollision(field_entity.PARTY0),
            field.EntityAct(field_entity.PARTY0, True,
                            #field_entity.SetSpriteLayer(3),
                            field_entity.SetSpeed(field_entity.Speed.FASTEST),
                            field_entity.Move(direction.UP, 7),
                            field_entity.Hide()
                            ),
            field.TintBackground(field.Tint.BLACK, invert=True),
            field.Return()
        ]
        space = Write(Bank.CC, src, "Warp out animation")
        if self.verbose:
            print('Warp out animation:  ')
            print([s.__str__() for s in src])
        return space.start_address

    def warp_in_animation(self):
        # Animation for warping to a warp point
        src = [
            field.EntityAct(field_entity.PARTY0, True,
                            field_entity.Move(direction.UP, 7),
                            #field_entity.SetSpriteLayer(3),
                            ),
            field.ShowEntity(field_entity.PARTY0),
            field.FadeInScreen(),
            field.TintBackground(field.Tint.BLACK),
            field.PlaySoundEffect(0x54),  # still need to pick this
            field.DisableEntityCollision(field_entity.PARTY0),
            field.EntityAct(field_entity.PARTY0, True,
                            field_entity.SetSpeed(field_entity.Speed.FASTEST),
                            field_entity.Move(direction.DOWN, 7),
                            #field_entity.SetSpriteLayer(0),
                            ),
            field.TintBackground(field.Tint.BLACK, invert=True),
            field.FreeScreen(),
            field.Return()
        ]
        if self.verbose:
            print('Warp in animation:  ')
            print([s.__str__() for s in src])
        space = Write(Bank.CC, src, "Warp in animation")
        return space.start_address

    def make_warp_point_pair(self, wp, maps):
        # Create a warp point in the correct location in the esper world
        dest = WARP_POINTS[wp.name][:3]   # [map_id, x, y]

        wpp = NPC()
        wpp.x = dest[1]
        wpp.y = dest[2]
        wpp.event_byte = (wp.npc_bit - 0x300) // 8
        wpp.event_bit = (wp.npc_bit - 0x300) % 8
        wpp.palette = 0  # default = 6
        wpp.sprite = 104  # 111 = save point
        wpp.split_sprite = 1
        wpp.const_sprite = 0
        wpp.direction = direction.LEFT
        wpp.no_face_on_trigger = 0
        wpp.speed = 0  # 2 = save point
        wpp.movement = 0
        wpp.map_layer = 1
        wpp.background_scrolls = 0
        wpp.background_layer = 0

        maps.append_npc(dest[0], wpp)

        # Create an event tile that does the warping action
        newevent = MapEvent()
        newevent.x = wpp.x
        newevent.y = wpp.y
        space = Write(Bank.CC, self._warp_point_pair_code(wp), "Warp point pair " + wp.name)
        newevent.event_address = space.start_address - EVENT_CODE_START
        maps.add_event(dest[0], newevent)



class WarpPoint:
    def __init__(self, warp_point_name):
        self.name = warp_point_name
        data = [0, 0, 0, 0, 0, 0xc9aeb]
        if warp_point_name in SAVE_POINT_DATA.keys():
            data = SAVE_POINT_DATA[warp_point_name]

        self.map_id = data[0]
        self.x = data[1]
        self.y = data[2]
        self.npc_id = data[3]
        self.npc_bit = data[4]
        self.event_code = data[5]

        # Dynamically set by WarpPoints when created
        self.activated_point_text = "<end>"
        self.warp_to_point_text = "<end>"
        self.activated_point_dialog_id = 0x0000
        self.warp_to_point_dialog_id = 0x0000
