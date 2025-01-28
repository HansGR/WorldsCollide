from data.map_event import MapEvent
from memory.space import Write, Bank
import instruction.field as field
from instruction import world, vehicle
from instruction.event import EVENT_CODE_START
from data.event_exit_info import event_exit_info
import data.direction as direction
import data.event_bit as event_bit
from data.parse import functions_to_bytes
from event.event import *

SWITCHYARD_MAP = 0x005


class Switchyard(Event):
    def name(self):
        return "Switchyard"

    def mod(self):
        self.make_tiles_unwalkable()

    def make_tiles_unwalkable(self):
        # make all tiles on the switchyard map unwalkable
        from utils.compression import compress, decompress

        layer1_tilemap = 0x103  # layer1 tilemap for black maps (0x3, 0x4, 0x5, 0x9)
        tilemap_ptrs_start = 0x19cd90
        tilemap_ptr_addr = tilemap_ptrs_start + layer1_tilemap * self.rom.LONG_PTR_SIZE
        tilemap_addr_bytes = self.rom.get_bytes(tilemap_ptr_addr, self.rom.LONG_PTR_SIZE)
        tilemap_addr = int.from_bytes(tilemap_addr_bytes, byteorder="little")

        next_tilemap_ptr_addr = tilemap_ptr_addr + self.rom.LONG_PTR_SIZE
        next_tilemap_addr_bytes = self.rom.get_bytes(next_tilemap_ptr_addr, self.rom.LONG_PTR_SIZE)
        next_tilemap_addr = int.from_bytes(next_tilemap_addr_bytes, byteorder="little")

        tilemaps_start = 0x19d1b0
        tilemap_len = next_tilemap_addr - tilemap_addr
        #tilemap = self.rom.get_bytes(tilemaps_start + tilemap_addr, tilemap_len)
        #decompressed = decompress(tilemap)

        map_size = [16, 16]
        no_movement_tile = 0x1e  # tile that cannot be moved into or on
        compressed = compress([no_movement_tile for i in range(map_size[0]*map_size[1])])
        if len(compressed) < tilemap_len:
            self.rom.set_bytes(tilemaps_start + tilemap_addr, compressed)
        else:
            print('warning: tilemap too large!')
            self.rom.set_bytes(tilemaps_start + tilemap_addr, compressed[:tilemap_len])


id_to_switchyard_xy = {}
def switchyard_xy(event_id):
    # Return [x, y] of switchyard tile based on event_id
    #return [event_id % 128, event_id // 128]
    # Modify to use the 16x16 space more efficiently
    if event_id not in id_to_switchyard_xy.keys():
        index = len(id_to_switchyard_xy)
        xy = [index % 16, index // 16]
        id_to_switchyard_xy[event_id] = xy
    return id_to_switchyard_xy[event_id]


def AddSwitchyardEvent(event_id, maps, branch=[], src=[]):
    if not src and not branch:
        raise Exception()

    [sx, sy] = switchyard_xy(event_id)

    switchyard_event = MapEvent()
    switchyard_event.x = sx
    switchyard_event.y = sy

    if branch:
        switchyard_event.event_address = branch - EVENT_CODE_START   # Just do it directly
        #src = [field.Branch(branch), field.Return()]
    if src:
        space = Write(Bank.CA, src, f"Switchyard tile for event {event_id}")
        switchyard_event.event_address = space.start_address - EVENT_CODE_START

    maps.add_event(SWITCHYARD_MAP, switchyard_event)
    #print('Added Switchyard event: ', event_id, sx, sy, hex(space.start_address), hex(space.end_address))


def GoToSwitchyard(event_id, map='', use_fade=False):
    [sx, sy] = switchyard_xy(event_id)

    # field maps and world maps have different LoadMap codes.  Use the correct one:
    if not map:
        this_map = event_exit_info[event_id][5][0]
        if this_map > 0x002:
            map = 'field'
        else:
            map = 'world'

    if map == 'field':
        if use_fade:
            src = [
                field.FadeLoadMap(SWITCHYARD_MAP, direction=direction.UP, default_music=False,
                              x=sx, y=sy, fade_in=False, entrance_event=False)
                ]
        else:
            src = [
                field.LoadMap(SWITCHYARD_MAP, direction=direction.UP, default_music=False,
                              x=sx, y=sy, fade_in=False, entrance_event=False)
            ]
        src += [field.Return()]
        #print('*** ', event_id , ': ', [f.__call__([]) for f in src])

    elif map == 'world':
        # World map always fades
        src = [
            # world.FadeScreen(),
            world.LoadMap(SWITCHYARD_MAP, direction=direction.UP, default_music=False,
                          x=sx, y=sy, fade_in=False, entrance_event=False),
            field.Return()
        ]

    return src

def SummonAirship(map_id, x, y, bytes=False, fadeout=False):
    # Return code that puts you in position [x,y] on world map map_id, with the airship there as well.
    if map_id not in [0x0, 0x1]:
        # Not an airshippable map!
        return []

    src = [
        field.SetEventBit(event_bit.TEMP_SONG_OVERRIDE),
    ]

    if fadeout:
        src += [
            field.FadeLoadMap(map_id, direction.DOWN, default_music=False, x=x, y=y, fade_in=False, airship=True),
        ]
    else:
        src += [
            field.LoadMap(map_id, direction.DOWN, default_music=False, x=x, y=y, fade_in=False, airship=True),
        ]

    src += [
        vehicle.SetPosition(x, y),
        vehicle.ClearEventBit(event_bit.TEMP_SONG_OVERRIDE),
        vehicle.LoadMap(map_id, direction.DOWN, default_music=True, x=x, y=y, fade_in=True),
        world.Turn(direction.DOWN),
        world.End()
    ]
    if bytes:
        return functions_to_bytes(src)
    else:
        return src
