from data.map_event import MapEvent
from memory.space import Write, Bank
import instruction.field as field
from instruction import world
from instruction.event import EVENT_CODE_START
from data.event_exit_info import event_exit_info
import data.direction as direction

SWITCHYARD_MAP = 0x005


def switchyard_xy(event_id):
    # Return [x, y] of switchyard tile based on event_id
    return [event_id % 128, event_id // 128]


def AddSwitchyardEvent(event_id, maps, branch=[], src=[]):
    [sx, sy] = switchyard_xy(event_id)

    if branch:
        src = [
            field.Branch(branch),
            field.Return()
        ]
    elif not src:
        raise Exception()

    space = Write(Bank.CA, src, f"Switchyard tile for event {event_id}")

    switchyard_event = MapEvent()
    switchyard_event.x = sx
    switchyard_event.y = sy
    switchyard_event.event_address = space.start_address - EVENT_CODE_START
    maps.add_event(SWITCHYARD_MAP, switchyard_event)


def GoToSwitchyard(event_id, map=''):
    [sx, sy] = switchyard_xy(event_id)

    # field maps and world maps have different LoadMap codes.  Use the correct one:
    if not map:
        this_map = event_exit_info[event_id][5][0]
        if this_map > 0x002:
            map = 'field'
        else:
            map = 'world'

    if map == 'field':
        src = [
            field.LoadMap(SWITCHYARD_MAP, direction=direction.UP, default_music=False,
                          x=sx, y=sy, fade_in=False, entrance_event=False),
            field.Return()
        ]
        #print('*** ', event_id , ': ', [f.__call__([]) for f in src])
    elif map == 'world':
        src = [
            world.LoadMap(SWITCHYARD_MAP, direction=direction.UP, default_music=False,
                          x=sx, y=sy, fade_in=False, entrance_event=False),
            field.Return()
        ]

    return src
