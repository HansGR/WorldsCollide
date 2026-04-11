def main():
    import args
    import log

    from memory.memory import Memory
    memory = Memory()

    from data.data import Data
    data = Data(memory.rom, args)

    from event.events import Events
    events = Events(memory.rom, args, data)

    from menus.menus import Menus
    menus = Menus(data.characters, data.dances, data.rages, data.enemies)

    from battle import Battle
    battle = Battle()

    from settings import Settings
    settings = Settings()

    from bug_fixes import BugFixes
    bug_fixes = BugFixes()

    data.write()
    memory.write()

    # Append -debug-verbose diagnostics (if any) to the spoiler log. No-op
    # unless -debug-verbose is set on the command line.
    from log import verbose as verbose_log
    verbose_log.finalize_and_append_to_log()

    #if data.maps.doors.verbose:
    #    from memory.space import Space
    #    print(Space.heaps)
    #    print(Space.spaces)

    #from data.npc import NPC
    #sp = data.maps.get_npc(0x009, 0x15)
    #sp.print()
    # print('All Save Point NPCs:')
    # for npc_id in range(len(data.maps.npcs.npcs)):  # map_id in range(data.maps.MAP_COUNT):
    #     #count = data.maps.get_npc_count(map_id)
    #     #for n in range(count):
    #     npc = data.maps.npcs.npcs[npc_id]
    #     if npc.sprite == 111:
    #         map_id = data.maps.npc_maps[npc_id]
    #         #index = data.maps.get_npc_index(map_id, npc_id)
    #         first_npc_id = (data.maps.maps[map_id]["npcs_ptr"] - data.maps.maps[0]["npcs_ptr"]) // NPC.DATA_SIZE
    #         index = npc_id - first_npc_id + 0x10
    #         # npc.event_byte = 0x66 + npc.event_bit = 2 --> npc event bit 0x632.  Figure out the math.
    #         npc_bit = (npc.event_byte*8 + npc.event_bit) + 0x300
    #         #hex(npc.event_byte), ':', npc.event_bit, '(',
    #         try:
    #             event_tile = data.maps.get_event(map_id, npc.x, npc.y)
    #             event_addr = event_tile.event_address + 0xa0000
    #         except:
    #             event_addr = 0
    #         print('[', hex(map_id), ',', npc.x, ',', npc.y, ',', hex(index), ',', hex(npc_bit), ', ', hex(event_addr),']')

if __name__ == '__main__':
    main()
