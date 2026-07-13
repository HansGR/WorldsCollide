"""Realization: write a finished DoorPlan into the ROM (rewrite plan
section 3.5). Re-homed verbatim from data/maps.py / data/transitions.py
in Stage F -- functions take the live Maps object; nothing here runs at
import time, so the doors/ package stays importable without a ROM.

    door_map.py     postprocess_door_map: plan pairs -> the realized
                    door_map/trap_map lookup (+4000 logical WOR ids,
                    shared-exit conflict resolution).
    exits.py        connect_exits + exit-event writers (entrance/exit
                    door patches are applied here as unified transition
                    logic), event-trigger relocation, cleanup.
    transitions.py  the one-way (trap->pit) and event-tile writer.
    event_tiles.py  event_exit_info runtime address updates + the
                    Transitions/connect_exits orchestration for write().
"""
