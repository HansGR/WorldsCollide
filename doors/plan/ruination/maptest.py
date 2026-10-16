"""-maptest (TESTING ONLY) room entries: ROOM[@IN][/OUT]."""

def maptest_doors(spec, chained):
    """-maptest entry 'ROOM[@IN][/OUT]' -> (room, door entered, door chained onward or None).
    Defaults: the room's first door in, and its first other door out when `chained`."""
    from data.rooms import room_data
    room, _, out_text = spec.partition('/')
    room, _, in_text = room.partition('@')
    if room not in room_data:
        raise ValueError(f"-maptest: unknown room id {room!r}")
    room_doors = [d for d in room_data[room][0] if isinstance(d, int)]

    def door(text, what):
        try:
            value = int(text)
        except ValueError:
            raise ValueError(f"-maptest: {spec!r}: {what} door {text!r} is not a number")
        if value not in room_doors:
            raise ValueError(f"-maptest: {spec!r}: door {value} is not one of {room}'s doors {room_doors}")
        return value

    entry = door(in_text, "entry") if in_text else room_doors[0]
    if not chained:
        if out_text:
            raise ValueError(f"-maptest: {spec!r}: the last room is not chained onward, so it takes no /OUT door")
        return room, entry, None
    others = [d for d in room_doors if d != entry]
    if out_text:
        exit_door = door(out_text, "exit")
        if exit_door == entry:
            raise ValueError(f"-maptest: {spec!r}: the entry and exit doors are the same")
    elif others:
        exit_door = others[0]
    else:
        raise ValueError(f"-maptest: {room!r} has fewer than two doors and cannot chain to the next room")
    return room, entry, exit_door
