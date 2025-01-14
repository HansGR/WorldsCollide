from event.event import *

class EsperMountain(Event):
    def __init__(self, events, rom, args, dialogs, characters, items, maps, enemies, espers, shops):
        super().__init__(events, rom, args, dialogs, characters, items, maps, enemies, espers, shops)
        self.DOOR_RANDOMIZE = (args.door_randomize_esper_mountain
                          or args.door_randomize_all
                          or args.door_randomize_crossworld
                          or args.door_randomize_dungeon_crawl
                          or args.door_randomize_each)

    def name(self):
        return "Esper Mountain"

    def character_gate(self):
        return self.characters.RELM

    def init_rewards(self):
        self.reward = self.add_reward(RewardType.CHARACTER | RewardType.ESPER | RewardType.ITEM)

    def init_event_bits(self, space):
        space.write(
            field.SetEventBit(event_bit.ESPER_MOUNTAIN_ACCESSIBLE),
            field.SetEventBit(event_bit.FOUND_ESPERS_ESPER_MOUNTAIN),
        )
        if self.args.character_gating:
            space.write(
                field.SetEventBit(event_bit.ESPER_MOUNTAIN_GATED),
            )
        else:
            space.write(
                field.ClearEventBit(event_bit.ESPER_MOUNTAIN_GATED),
            )

    def mod(self):
        self.entrance_relm_npc_id = 0x1c
        self.entrance_relm_npc = self.maps.get_npc(0x177, self.entrance_relm_npc_id)

        self.outside1_relm_npc_id = 0x10
        self.outside1_relm_npc = self.maps.get_npc(0x175, self.outside1_relm_npc_id)

        self.outside2_relm_npc_id = 0x11
        self.outside2_relm_npc = self.maps.get_npc(0x174, self.outside2_relm_npc_id)

        self.statue_room_relm_npc_id = 0x11
        self.statue_room_relm_npc = self.maps.get_npc(0x173, self.statue_room_relm_npc_id)

        self.entrance_event_mod()
        self.relm_following_mod()
        self.statues_mod()
        self.ultros_battle_mod()
        self.esper_event_mod()

        if self.reward.type == RewardType.CHARACTER:
            self.character_mod(self.reward.id)
        elif self.reward.type == RewardType.ESPER:
            self.esper_mod(self.reward.id)
        elif self.reward.type == RewardType.ITEM:
            self.item_mod(self.reward.id)

        self.log_reward(self.reward)

        if self.DOOR_RANDOMIZE:
            self.door_rando_mod()

    def entrance_event_mod(self):
        src = [
            Read(0xbf2a2, 0xbf2b3), # copy old entrance event
        ]
        if self.args.character_gating:
            src += [
                field.ReturnIfEventBitSet(event_bit.DEFEATED_ULTROS_ESPER_MOUNTAIN),
                field.ReturnIfEventBitClear(event_bit.character_recruited(self.character_gate())),
                field.ClearEventBit(event_bit.ESPER_MOUNTAIN_GATED),
            ]
        src += [
            field.Return(),
        ]
        space = Write(Bank.CB, src, "esper mountain entrance event")
        entrance_event = space.start_address

        space = Reserve(0xbf2a2, 0xbf2b3, "esper mountain entrance event branch", field.NOP())
        space.write(
            field.Branch(entrance_event),
        )

    def relm_following_mod(self):
        # relm following events are skipped if found espers
        # found espers are used in a number of other places so change the requirement to ultros battle
        space = Reserve(0xbef1c, 0xbef1c, "relm following requirement")
        space.write(event_bit.ESPER_MOUNTAIN_GATED)

        space = Reserve(0xbef44, 0xbef44, "relm following requirement")
        space.write(event_bit.ESPER_MOUNTAIN_GATED)

        space = Reserve(0xbef72, 0xbef72, "relm following requirement")
        space.write(event_bit.ESPER_MOUNTAIN_GATED)

    def statues_mod(self):
        # delete statues event tile
        self.maps.delete_event(0x173, 15, 20)

        # add a new tile south of existing ultros event tile so player cannot go around the event
        src = [
            field.ReturnIfEventBitSet(event_bit.ESPER_MOUNTAIN_GATED),
            field.EntityAct(field_entity.PARTY0, True,
                field_entity.Move(direction.UP, 1),
            ),
            field.Return(),
        ]
        space = Write(Bank.CB, src, "esper mountain south ultros event tile")
        south_ultros_event_tile = space.start_address

        from data.map_event import MapEvent
        new_event = MapEvent()
        new_event.x = 15
        new_event.y = 23
        new_event.event_address = south_ultros_event_tile - EVENT_CODE_START
        self.maps.add_event(0x173, new_event)

        space = Reserve(0xbefa5, 0xbefaa, "esper mountain ultros statues requirement", field.NOP())
        space.write(
            field.ReturnIfEventBitSet(event_bit.ESPER_MOUNTAIN_GATED),
        )

        space = Reserve(0xbefc2, 0xbf0c6, "esper mountain ultros statues scene", field.NOP())
        space.write(
            field.SetEventBit(event_bit.ESPER_MOUNTAIN_GATED),
            field.Branch(space.end_address + 1), # skip nops
        )

        space = Reserve(0xbf0d3, 0xbf0d3, "esper mountain reload statue map after ultros scene")
        space.write(15) # change x pos to where event happens

    def ultros_battle_mod(self):
        boss_pack_id = self.get_boss("Ultros 3")

        space = Reserve(0xbf0c7, 0xbf0cd, "esper mountain invoke battle ultros", field.NOP())
        space.write(
            field.InvokeBattle(boss_pack_id),
        )

        space = Reserve(0x10bd7b, 0x10be2a, "esper mountain ultros battle relm appears")
        space.clear(0xfd)
        space.write(0xff)

    def esper_event_mod(self):
        # delete event which triggers scene with espers and thamasa (0xbf2b5)
        self.maps.delete_event(0x177, 15, 17)

    def character_mod(self, character):
        self.entrance_relm_npc.sprite = character
        self.entrance_relm_npc.palette = self.characters.get_palette(character)

        self.outside1_relm_npc.sprite = character
        self.outside1_relm_npc.palette = self.characters.get_palette(character)

        self.outside2_relm_npc.sprite = character
        self.outside2_relm_npc.palette = self.characters.get_palette(character)

        self.statue_room_relm_npc.sprite = character
        self.statue_room_relm_npc.palette = self.characters.get_palette(character)

        space = Reserve(0xbf0d9, 0xbf167, "esper mountain finish ultros scene", field.NOP())
        space.write(
            field.RecruitAndSelectParty(character),

            field.SetEventBit(event_bit.DEFEATED_ULTROS_ESPER_MOUNTAIN),
            field.FadeInScreen(),
            field.FinishCheck(),
            field.Return(),
        )

    def relm_npc_mod(self):
        random_sprite = self.characters.get_random_esper_item_sprite()

        self.entrance_relm_npc.sprite = random_sprite
        self.entrance_relm_npc.palette = self.characters.get_palette(random_sprite)

        self.outside1_relm_npc.sprite = random_sprite
        self.outside1_relm_npc.palette = self.characters.get_palette(random_sprite)

        self.outside2_relm_npc.sprite = random_sprite
        self.outside2_relm_npc.palette = self.characters.get_palette(random_sprite)

        self.statue_room_relm_npc.sprite = random_sprite
        self.statue_room_relm_npc.palette = self.characters.get_palette(random_sprite)

    def esper_item_mod(self, esper_item_instructions):
        self.relm_npc_mod()

        space = Reserve(0xbf0d9, 0xbf167, "esper mountain finish ultros scene", field.NOP())
        space.write(
            field.SetEventBit(event_bit.DEFEATED_ULTROS_ESPER_MOUNTAIN),
            field.FadeInScreen(),

            esper_item_instructions,
            field.FinishCheck(),

            field.Return(),
        )

    def esper_mod(self, esper):
        self.esper_item_mod([
            field.AddEsper(esper),
            field.Dialog(self.espers.get_receive_esper_dialog(esper)),
        ])

    def item_mod(self, item):
        self.esper_item_mod([
            field.AddItem(item),
            field.Dialog(self.items.get_receive_dialog(item)),
        ])

    def door_rando_mod(self):
        # (1) Trapdoors in Esper Mountain: remove the check to see if the boss has been defeated yet.
        # e.g. "CB/EE8F: C0    If ($1E80($097) [$1E92, bit 7] is clear), branch to $CA5EB3 (simply returns)
        space = Reserve(0x0bee8f, 0x0bee94, "esper mountain trapdoor boss check 1", field.NOP())
        space = Reserve(0x0beebe, 0x0beec3, "esper mountain trapdoor boss check 2", field.NOP())
        space = Reserve(0x0beeec, 0x0beef1, "esper mountain trapdoor boss check 3", field.NOP())

        # (2) Need to add NPCs to block exits while the animation is playing.
        from data.npc import CreateInvisibleBlockNPCs

        # (2a) Room #1
        map_id = 0x177
        door_locations = [[60, 16], [42, 26], [55, 32], [48, 9]]

        npc_id = CreateInvisibleBlockNPCs(self.maps, map_id, door_locations, self.entrance_relm_npc)
        #print('NPCs created 1: ', [hex(a) for a in npc_id])

        # Insert code to animation to create/delete them as needed
        patch_in = [0xbef28, 0xbef2b]  # set event bit, create relm npc
        src = [
            Read(patch_in[0], patch_in[1]),
        ]
        for i in range(len(npc_id)):
            src += [
                field.CreateEntity(npc_id[i]),
                field.ShowEntity(npc_id[i]),
            ]
        src += [field.Return()]
        space_create = Write(Bank.CB, src, "create NPCs esper mountain 1")
        #print('Create NPCs 1 src:', src)

        space = Reserve(patch_in[0], patch_in[1], "patch create npcs esper mtn 1", field.NOP())
        space.write(field.Call(space_create.start_address))

        patch_out = [0xbef3e, 0xbef41]  # set event bit, clear event bit
        src = [
            Read(patch_out[0], patch_out[1]),
        ]
        for i in range(len(npc_id)):
            src += [
                field.DeleteEntity(npc_id[i]),
                field.HideEntity(npc_id[i]),
            ]
        src += [field.Return()]
        space_delete = Write(Bank.CB, src, "delete NPCs esper mountain 1")
        #print('Delete NPCs 1 src:', src)

        space = Reserve(patch_out[0], patch_out[1], "patch delete npcs esper mtn 1", field.NOP())
        space.write(field.Call(space_delete.start_address))


        # (2b) Room 2
        map_id = 0x175
        door_locations = [[16, 23], [25, 15]]
        npc_id = CreateInvisibleBlockNPCs(self.maps, map_id, door_locations, self.outside1_relm_npc)
        #print('NPCs created 2: ', npc_id)

        # Insert code to animation to create/delete them as needed
        patch_in = [0xbef50, 0xbef53]  # set event bit, create relm npc
        src = [
            Read(patch_in[0], patch_in[1]),
        ]
        for i in range(len(npc_id)):
            src += [
                field.CreateEntity(npc_id[i]),
                field.ShowEntity(npc_id[i]),
            ]
        src += [field.Return()]
        space_create = Write(Bank.CB, src, "create NPCs esper mountain 2")
        #print('Create NPCs 2src:', src)

        space = Reserve(patch_in[0], patch_in[1], "patch create npcs esper mtn 2", field.NOP())
        space.write(field.Call(space_create.start_address))

        patch_out = [0xbef6c, 0xbef6f]  # set event bit, clear event bit
        src = [
            Read(patch_out[0], patch_out[1]),
        ]
        for i in range(len(npc_id)):
            src += [
                field.DeleteEntity(npc_id[i]),
                field.HideEntity(npc_id[i]),
            ]
        src += [field.Return()]
        space_delete = Write(Bank.CB, src, "delete NPCs esper mountain 2")
        #print('Delete NPCs 2 src:', src)

        space = Reserve(patch_out[0], patch_out[1], "patch delete npcs esper mtn 2", field.NOP())
        space.write(field.Call(space_delete.start_address))


        # (2c) Room 3 (same map as Room 1)
        map_id = 0x177
        door_locations = [[42, 63], [53, 62]]

        npc_id = CreateInvisibleBlockNPCs(self.maps, map_id, door_locations, self.entrance_relm_npc)
        #print('NPCs created 3: ', [hex(a) for a in npc_id])

        # Insert code to animation to create/delete them as needed
        patch_in = [0xbef7e, 0xbef81]  # set event bit, create relm npc
        src = [
            Read(patch_in[0], patch_in[1]),
        ]
        for i in range(len(npc_id)):
            src += [
                field.CreateEntity(npc_id[i]),
                field.ShowEntity(npc_id[i]),
            ]
        src += [field.Return()]
        space_create = Write(Bank.CB, src, "create NPCs esper mountain 1")
        #print('Create NPCs 3 src:', src)

        space = Reserve(patch_in[0], patch_in[1], "patch create npcs esper mtn 3", field.NOP())
        space.write(field.Call(space_create.start_address))

        patch_out = [0xbefa0, 0xbefa3]  # set event bit, clear event bit
        src = [
            Read(patch_out[0], patch_out[1]),
        ]
        for i in range(len(npc_id)):
            src += [
                field.DeleteEntity(npc_id[i]),
                field.HideEntity(npc_id[i]),
            ]
        src += [field.Return()]
        space_delete = Write(Bank.CB, src, "delete NPCs esper mountain 3")
        #print('Delete NPCs 3 src:', src)

        space = Reserve(patch_out[0], patch_out[1], "patch delete npcs esper mtn 3", field.NOP())
        space.write(field.Call(space_delete.start_address))


