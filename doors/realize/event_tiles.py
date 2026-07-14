"""event_exit_info runtime updates + door-realization orchestration for
Maps.write()."""

from log.verbose import vprint
from instruction.event import EVENT_CODE_START
from data.map_exit_extra import exit_data
from data.event_exit_info import event_exit_info
from doors.realize.transitions import Transitions
from doors.realize.exits import connect_exits
from event.switchyard import SWITCHYARD_MAP, switchyard_xy


def realize_doors(maps):
    """The door-realization half of Maps.write(): update the runtime
    event-exit addresses (both partners of used event connections -- the
    Top-10 #4 gotcha), write the one-way transitions, then connect the
    two-way doors."""
    # Patch exits if necessary
    used_exits = [m for m in maps.door_map.keys()]

    # Build used_events list for event_exit_info runtime update.
    # Event tiles with None addresses in event_exit_info (switchyard tiles) need their
    # addresses updated at runtime by finding the event at their map location.
    #
    # IMPORTANT: When Transitions creates an entrance EventExit for an event tile (1500-2000),
    # it checks if the vanilla partner is also an event tile. If so, it uses the partner's
    # event code via use_event_info=partner_id. This means the PARTNER's event_exit_info
    # must have a valid address, not just the entrance itmaps.
    #
    # Connections are stored as [exit_id, entrance_id]. We must include partners for BOTH:
    # - m[1] partners: when the entrance is an event tile (e.g., [1515, 1560] -> partner of 1560)
    # - m[0] partners: when the exit is an event tile (e.g., [1560, 1515] -> partner of 1560)
    used_events = [m[0] for m in maps.doors.map[1]] \
                  + [m[1] - 1000 for m in maps.doors.map[1]] \
                  + [m[0] for m in maps.doors.map[0] if 2000 > m[0] >= 1500] \
                  + [m[1] for m in maps.doors.map[0] if 2000 > m[1] >= 1500]

    # Also include vanilla partners of event tile entrances whose partners are also event tiles
    # (used by Transitions when creating entrance EventExit with use_event_info=partner)
    used_events += [exit_data[m[1]][0] for m in maps.doors.map[0]
                    if 2000 > m[1] >= 1500 and 1500 <= exit_data[m[1]][0] < 2000]
    # Also include vanilla partners of event tile EXITS whose partners are also event tiles
    # (needed when the exit side is an event tile like 1560 whose partner 1559 needs updating)
    used_events += [exit_data[m[0]][0] for m in maps.doors.map[0]
                    if 2000 > m[0] >= 1500 and 1500 <= exit_data[m[0]][0] < 2000]

    for e in event_exit_info.keys():
        if (e in used_events or e in used_exits) and event_exit_info[e][0] is None:
            if maps.doors.verbose:
                vprint('attempting to update event exit info: ', e)
            # Update the event addresses
            #mapid = event_exit_info[e][5][0]
            #ex = event_exit_info[e][5][1]
            #ey = event_exit_info[e][5][2]
            if event_exit_info[e][5][0] is SWITCHYARD_MAP:
                mapid = SWITCHYARD_MAP
                [ex, ey] = switchyard_xy(e)
            else:
                mapid = event_exit_info[e][5][0]
                ex = event_exit_info[e][5][1]
                ey = event_exit_info[e][5][2]
            ev = maps.get_event(mapid, ex, ey)
            event_exit_info[e][0] = ev.event_address + EVENT_CODE_START
            if maps.doors.verbose:
                vprint('Updated event exit info: ', e, hex(event_exit_info[e][0]))

    # Connect one-way event exits using the Transitions class
    maps.transitions = Transitions(maps.doors.map[1], maps.rom, maps.exits.exit_original_data, event_exit_info, args=maps.args)
    maps.transitions.write(maps=maps)

    # Connect two-way doors
    connect_exits(maps)

    #if maps.doors.verbose:
    #    print('Switchyard indexes:')
    #    for s, id in enumerate(id_to_switchyard_xy):
    #        print(s, id, id_to_switchyard_xy[id])

