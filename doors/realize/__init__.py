"""Realization: write a finished DoorPlan into the ROM.

realize_doors() below is the entry point, called by Maps.write().
Functions take the live Maps object at call time; nothing here runs at
import time, so the doors/ package stays importable without a ROM.

    door_map.py     postprocess_door_map: plan pairs -> the realized
                    door_map/trap_map lookup (+4000 logical WOR ids,
                    shared-exit conflict resolution).
    exits.py        connect_exits + exit-event writers (entrance/exit
                    door patches are applied here as unified transition
                    logic), event-trigger relocation, cleanup.
    transitions.py  the one-way (trap->pit) and event-tile writer.
    event_tiles.py  event_exit_info runtime address updates for the
                    event tiles used on the final map.
"""


def realize_doors(maps):
    """The door-realization half of Maps.write(): update the runtime
    event-exit addresses (both partners of used event connections -- the
    Top-10 #4 gotcha), write the one-way transitions, then connect the
    two-way doors."""
    from data.event_exit_data import event_exit_info
    from doors.realize.event_tiles import update_event_exit_addresses
    from doors.realize.transitions import Transitions
    from doors.realize.exits import connect_exits

    update_event_exit_addresses(maps)

    # Connect one-way event exits using the Transitions class
    transitions = Transitions(maps.doors.map[1], maps.rom,
                              maps.exits.exit_original_data,
                              event_exit_info, args=maps.args)
    transitions.write(maps=maps)

    # Connect two-way doors
    connect_exits(maps)
