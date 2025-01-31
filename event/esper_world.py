from event.event import *

class EsperWorld(Event):
    def name(self):
        return "Esper World"

    def init_event_bits(self, space):
        space.write(
            field.ClearEventBit(npc_bit.ESPER_WORLD_MADUIN),  # 0x337
            field.ClearEventBit(npc_bit.ESPER_WORLD_MADONNA)  # 0x357
        )

    def mod(self):
        self.map_outside = 0x0d9   # Esper world hub
        self.map_gate_cave = 0x0da   # Esper gate
        self.map_interiors = 0x0db   # interior houses & rooms

        self.cleanup_esper_world()
        self.add_ruination_exit()

    def add_ruination_exit(self):
        # Add the north exit from the Esper world gate room
        exit_id = 1562

        src = [
            field.FadeLoadMap(0x068, x=108, y=52, direction=direction.UP,
                              default_music=True, entrance_event=True, fade_in=True),
            field.Return()
        ]
        space = Write(Bank.CC, src, "Go to Narshe hub")
        self.go_to_hub = space.start_address

        from data.map_event import MapEvent
        new_event = MapEvent()
        new_event.x = 55
        new_event.y = 29
        new_event.event_address = self.go_to_hub - EVENT_CODE_START
        self.maps.add_event(0x0da, new_event)

    def cleanup_esper_world(self):
        # Turn off the entrance events for these rooms
        RETURN_ADDR = 0x5eb3
        self.maps.maps[self.map_outside]["entrance_event_address"] = RETURN_ADDR
        self.maps.maps[self.map_gate_cave]["entrance_event_address"] = RETURN_ADDR
        self.maps.maps[self.map_interiors]["entrance_event_address"] = RETURN_ADDR

        # Delete event tile in gate cave: 0xaa78f -- 0xaa7f4
        self.maps.delete_event(self.map_gate_cave, 56, 49)

        # Remove all NPCs from these maps:
        # outside map
        npc_ids = [i+0x10 for i in range(9, -1, -1)]
        for id in npc_ids:
            self.maps.remove_npc(self.map_outside, id)
        # gate cave
        npc_ids = [i+0x10 for i in range(18, -1, -1)]
        for id in npc_ids:
            self.maps.remove_npc(self.map_gate_cave, id)
        # interiors
        npc_ids = [i + 0x10 for i in range(8, -1, -1)]
        for id in npc_ids:
            self.maps.remove_npc(self.map_interiors, id)

        # Make door not interact in a funny way with characters
        from utils.compression import compress, decompress

        layer1_tilemap = 0x71  # layer1 tilemap for esper world cave
        tilemap_ptrs_start = 0x19cd90
        tilemap_ptr_addr = tilemap_ptrs_start + layer1_tilemap * self.rom.LONG_PTR_SIZE
        tilemap_addr_bytes = self.rom.get_bytes(tilemap_ptr_addr, self.rom.LONG_PTR_SIZE)
        tilemap_addr = int.from_bytes(tilemap_addr_bytes, byteorder="little")

        next_tilemap_ptr_addr = tilemap_ptr_addr + self.rom.LONG_PTR_SIZE
        next_tilemap_addr_bytes = self.rom.get_bytes(next_tilemap_ptr_addr, self.rom.LONG_PTR_SIZE)
        next_tilemap_addr = int.from_bytes(next_tilemap_addr_bytes, byteorder="little")

        tilemaps_start = 0x19d1b0
        tilemap_len = next_tilemap_addr - tilemap_addr
        tilemap = self.rom.get_bytes(tilemaps_start + tilemap_addr, tilemap_len)
        decompressed = decompress(tilemap)

        map_width = 64
        # Set tile at (54, 30) --> 0x47, and (56, 30) --> 0x49, like in Esper Cave final room door
        coordinates = [(54, 30), (56, 30)]  # coordinates to change
        new_tile = [0x47, 0x49]
        for i in range(len(coordinates)):
            decompressed[coordinates[i][0] + coordinates[i][1] * map_width] = new_tile[i]
            #print(decompressed[coordinates[i][0] + coordinates[i][1] * map_width])
        compressed = compress(decompressed)
        self.rom.set_bytes(tilemaps_start + tilemap_addr, compressed)

        ### This works, but looks funny for some reason.  Why?  They look identical except for Priority 1.
        # Instead, can we set tileset 0xf, tiles 0x1d, 0x1f to not priority-1?


        #print('Cleaned up Esper World')
