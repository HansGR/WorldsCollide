from copy import deepcopy

from event.event import *

class EsperWorld(Event):
    def name(self):
        return "Esper World"

    def init_event_bits(self, space):
        space.write(
            field.ClearEventBit(npc_bit.ESPER_WORLD_MADUIN),  # 0x337
            field.ClearEventBit(npc_bit.ESPER_WORLD_MADONNA)  # 0x357
        )

        if self.args.ruination_mode:
            # Clear all warp point NPC bits to ensure they start hidden
            # These bits control visibility of warp point NPCs in the Esper World
            # and must be cleared at game start so warp points only appear after activation
            from data.warps import AVAILABLE_NPC_BITS
            for bit in AVAILABLE_NPC_BITS:
                space.write(
                    field.ClearEventBit(bit)
                )

    def mod(self):
        self.map_outside = 0x0d9   # Esper world hub
        self.map_gate_cave = 0x0da   # Esper gate
        self.map_interiors = 0x0db   # interior houses & rooms

        self.cleanup_esper_world()
        self.add_ruination_exit()

        if self.args.ruination_mode:
            self.add_save_point()

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

    def add_save_point(self):
        from data.map_event import MapEvent
        X = 55
        Y = 44

        # Copy the save point NPC from map 0x06b (Narshe school) at npc_id 0x10:    [0x06b, 60, 32, 0x10, 0x690, 0xc9aeb],
        save_npc = deepcopy(self.maps.get_npc(0x06b, 0x10))
        save_npc.x = X
        save_npc.y = Y
        self.maps.append_npc(self.map_gate_cave, save_npc)

        # Copy the save point event tile from map 0x009 at (8, 6)
        save_event_src = self.maps.get_event(0x06b, 60, 32)
        save_event = MapEvent()
        save_event.x = X
        save_event.y = Y
        save_event.event_address = save_event_src.event_address
        self.maps.add_event(self.map_gate_cave, save_event)

    def cleanup_esper_world(self):
        # Replace the vanilla entrance events for these rooms. In ruination mode,
        # point them at the shared party-interaction-pointer subroutine so NPC talk
        # events are re-bound whenever the player enters (needed after loading a
        # save, since field RAM pointers aren't preserved). Otherwise, point at
        # a bare Return.
        RETURN_ADDR = 0x5eb3
        if self.args.ruination_mode:
            from event.ruination import SET_PARTY_INTERACTION_POINTERS
            entrance_addr = SET_PARTY_INTERACTION_POINTERS - EVENT_CODE_START
        else:
            entrance_addr = RETURN_ADDR
        self.maps.maps[self.map_outside]["entrance_event_address"] = entrance_addr
        self.maps.maps[self.map_gate_cave]["entrance_event_address"] = entrance_addr
        self.maps.maps[self.map_interiors]["entrance_event_address"] = entrance_addr

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
        # Nevermind, it was just the boulder NPCs showing through.


        #print('Cleaned up Esper World')
