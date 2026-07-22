"""event_exit_info runtime address updates for the event tiles used on
the final map (called by doors.realize.realize_doors)."""

from log.verbose import vprint
from instruction.event import EVENT_CODE_START
from data.map_exit_extra import exit_data
from data.event_exit_data import event_exit_info
from event.switchyard import SWITCHYARD_MAP, switchyard_xy


def update_event_exit_addresses(maps):
    """Fill in the runtime event addresses for every event-tile exit the
    final map uses (entries with a None address in event_exit_info)."""
    # Patch exits if necessary
    used_exits = [m for m in maps.door_map.keys()]

    # Build used_events list for event_exit_info runtime update.
    # Event tiles with None addresses in event_exit_info (switchyard tiles) need their
    # addresses updated at runtime by finding the event at their map location.
    #
    # IMPORTANT: When Transitions creates an entrance EventExit for an event tile (1500-2000),
    # it checks if the vanilla partner is also an event tile. If so, it uses the partner's
    # event code via use_event_info=partner_id. This means the PARTNER's event_exit_info
    # must have a valid address, not just the entrance itself.
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
