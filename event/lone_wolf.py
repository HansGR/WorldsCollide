from event.event import *

class LoneWolf(Event):
    def name(self):
        return "Lone Wolf"

    def character_gate(self):
        return self.characters.MOG

    def init_rewards(self):
        if self.args.no_free_characters_espers:
            self.reward1 = self.add_reward(RewardType.ITEM)
        else:
            self.reward1 = self.add_reward(RewardType.CHARACTER | RewardType.ESPER | RewardType.ITEM)
        
        self.reward2 = self.add_reward(RewardType.ITEM)

    def init_event_bits(self, space):
        space.write(
            field.ClearEventBit(event_bit.GOT_BOTH_REWARDS_LONE_WOLF),
            field.ClearEventBit(npc_bit.MOG_MOOGLE_ROOM_WOR),
        )

    def mod(self):
        # In ruination mode, Lone Wolf event is on Narshe WoB instead of Tritoch Peak
        if self.args.ruination_mode:
            NARSHE_WOB_MAP = 0x014
            # Lone Wolf is at map-local index 25 (0x19), but npc_id is offset by 0x10
            # So npc_id = 0x19 + 0x10 = 0x29
            NARSHE_WOB_LONE_WOLF_NPC_ID = 0x29

            # Load Narshe WoB Lone Wolf for property copying in ruination_mod()
            self.lone_wolf_npc_id = NARSHE_WOB_LONE_WOLF_NPC_ID
            self.lone_wolf_npc = self.maps.get_npc(NARSHE_WOB_MAP, self.lone_wolf_npc_id)

            # DON'T initialize self.mog_npc here - ruination_mod() will set it
            # after creating the WoR Tritoch Peak cliff scene NPCs
        else:
            self.mog_npc_id = 0x1c
            self.mog_npc = self.maps.get_npc(0x017, self.mog_npc_id)

            self.lone_wolf_npc_id = 0x1b
            self.lone_wolf_npc = self.maps.get_npc(0x017, self.lone_wolf_npc_id)

        self.mog_moogle_room_npc_id = 0x10
        self.mog_moogle_room_npc = self.maps.get_npc(0x02c, self.mog_moogle_room_npc_id)

        # invisible npc blocking bridge until player chooses either mog or lone wolf
        self.invisible_bridge_block_npc_id = 0x1d

        if self.args.ruination_mode:
            self.ruination_mod()  # Edit npc data prior to other modifications

        self.dialog_mod()
        self.chase_mod()

        if self.reward1.type == RewardType.CHARACTER:
            self.character_mod(self.reward1.id)
        elif self.reward1.type == RewardType.ESPER:
            self.esper_mod(self.reward1.id)
        elif self.reward1.type == RewardType.ITEM:
            self.item_mod(self.reward1.id)
        self.alternative_item_mod()
        self.finish_check_mod()

        self.moogle_room_entrance_event_mod()
        self.moogle_room_reward_mod()

        self.log_reward(self.reward1)
        self.log_reward(self.reward2)

    def dialog_mod(self):
        space = Reserve(0xcd3ef, 0xcd3f1, "lone wolf G'whoa! I've been made!", field.NOP())
        space = Reserve(0xcd407, 0xcd409, "I am lone wolf, the pickpocket!", field.NOP())
        space = Reserve(0xcd437, 0xcd439, "lone wolf outside treasure room G'heh!", field.NOP())
        space = Reserve(0xcd4a1, 0xcd4a3, "lone wolf Persistent, aren't you!", field.NOP())
        space = Reserve(0xcd54c, 0xcd54e, "lone wolf mog stands dialog Kupo!!", field.NOP())
        space = Reserve(0xcd560, 0xcd562, "lone wolf G'heh! Got a wild one, here", field.NOP())
        space = Reserve(0xcd5a0, 0xcd5a2, "lone wolf kupo before mog falls", field.NOP())
        space = Reserve(0xcd608, 0xcd60a, "lone wolf Thankupo!", field.NOP())

    def chase_mod(self):
        if self.args.character_gating:
            space = Reserve(0xcd3d4, 0xcd3db, "lone wolf saw maduin die and not started lone wolf requirements")
            space.write(
                field.ReturnIfAny([event_bit.character_recruited(self.character_gate()), False, event_bit.CHASING_LONE_WOLF1, True]),
            )

        space = Reserve(0xcd3f3, 0xcd3f4, "lone wolf pauses before beginning to exit", field.NOP())
        space.write(field.Pause(0.5)) # shorten from 1.5 seconds
        space = Reserve(0xcd402, 0xcd402, "lone wolf pauses before turning right")
        space.write(field.Pause(0.5)) # shorten from 2 seconds

    def character_music_mod(self, character):
        from music.song_utils import get_character_theme
        src = [
            field.StartSong(get_character_theme(character)),
        ]
        space = Reserve(0xcd606, 0xcd607, "Play Song Mog")
        space.write(src)

    def character_mod(self, character):
        self.character_music_mod(character)
        self.mog_npc.sprite = character
        self.mog_npc.palette = self.characters.get_palette(character)

        space = Reserve(0xcd5e5, 0xcd5f3, "lone wolf create char and make available", field.NOP())
        space.write(
            field.CreateEntity(character),
            field.RecruitCharacter(character),
        )

        # move lone wolf falling up to make room for adding character
        # skip copying lone wolf take this dialog at [0xcd693,0xcd695]
        space = Reserve(0xcd61b, 0xcd67b, "lone wolf mog dialog and naming", field.NOP())
        if self.args.ruination_mode:
            # Rewrite explicitly with updated NPC IDs (copy_from would use old hardcoded $1C/$1B)
            # Range 1 (0xcd67c-0xcd692): Mog/character celebration animation
            space.write(
                field.EntityAct(self.mog_npc_id, True,
                    field_entity.AnimateHighJump(),
                    field_entity.Turn(direction.RIGHT),
                ),
                field.EntityAct(self.mog_npc_id, True,
                    field_entity.Turn(direction.UP),
                ),
                field.EntityAct(self.mog_npc_id, True,
                    field_entity.Turn(direction.LEFT),
                ),
                field.EntityAct(self.mog_npc_id, True,
                    field_entity.Turn(direction.DOWN),
                ),
                field.EntityAct(self.mog_npc_id, True,
                    field_entity.AnimateFrontRightHandUp(),
                ),
                field.Pause(1.5),
                # Range 2 (0xcd696-0xcd6bf): Lone Wolf falls off cliff
                field.DisableEntityCollision(self.lone_wolf_npc_id),
                field.PlaySoundEffect(186),
                field.EntityAct(self.lone_wolf_npc_id, True,
                    field_entity.SetSpriteLayer(3),
                    field_entity.DisableWalkingAnimation(),
                    field_entity.SetSpeed(field_entity.Speed.FAST),
                    field_entity.Turn(direction.RIGHT),
                    field_entity.AnimateHighJump(),
                    field_entity.Move(direction.RIGHT, 2),
                    field_entity.SetSpeed(field_entity.Speed.FASTEST),
                    field_entity.Move(direction.DOWN, 4),
                ),
                field.HideEntity(self.lone_wolf_npc_id),
                field.RefreshEntities(),
                field.EnableEntityCollision(self.lone_wolf_npc_id),
                field.EntityAct(field_entity.PARTY0, False,
                    field_entity.SetSpeed(field_entity.Speed.NORMAL),
                    field_entity.MoveDiagonal(direction.RIGHT, 1, direction.DOWN, 1),
                    field_entity.Move(direction.RIGHT, 2),
                ),
                field.EntityAct(self.mog_npc_id, True,
                    field_entity.SetSpeed(field_entity.Speed.NORMAL),
                    field_entity.Move(direction.RIGHT, 4),
                ),
                field.Pause(2.0),
                field.EntityAct(field_entity.PARTY0, False,
                    field_entity.Turn(direction.UP),
                ),
                field.EntityAct(self.mog_npc_id, True,
                    field_entity.Turn(direction.DOWN),
                ),
                field.Pause(0.5),
            )
        else:
            space.copy_from(0xcd67c, 0xcd692)
            space.copy_from(0xcd696, 0xcd6bf)
        space.write(
            field.Branch(space.end_address + 1), # skip nops
        )

        if self.args.ruination_mode is not None:
            from event.ruination import PARTY_INTERACTION_SCRIPT_ADDRS
            branch_refresh_src = [
                field.ChangeNPCEventAddress(character, PARTY_INTERACTION_SCRIPT_ADDRS[character]),
                field.SetupBranchRecruit(character),
                field.Call(field.REFRESH_CHARACTERS_AND_SELECT_PARTY),
                field.FinalizeBranchRecruit(),
                field.Return(),
            ]
            branch_refresh = Write(Bank.CC, branch_refresh_src, "lone wolf branch-aware refresh")
            refresh_addr = branch_refresh.start_address
        else:
            refresh_addr = field.REFRESH_CHARACTERS_AND_SELECT_PARTY

        space = Reserve(0xcd67c, 0xcd696, "lone wolf add char", field.NOP())
        space.write(
            field.Call(refresh_addr),
            field.HideEntity(self.mog_npc_id),
            field.HideEntity(self.invisible_bridge_block_npc_id),
            field.ClearEventBit(event_bit.TEMP_SONG_OVERRIDE),
            field.SetEventBit(npc_bit.MOG_MOOGLE_ROOM_WOR),
            field.SetEventBit(event_bit.RECRUITED_MOG_WOB),
            field.RefreshEntities(),
            field.FadeInScreen(),
            field.Branch(0xcd6dd), # skip nops
        )

    def esper_item_mod(self, add_esper_item, sound_dialog_esper_item):
        space = Reserve(0xcd5df, 0xcd5f3, "lone wolf assign character properties", field.NOP())
        space = Reserve(0xcd693, 0xcd695, "char chosen dialog before lone wolf falls", field.NOP())

        space = Reserve(0xcd61b, 0xcd67b, "lone wolf add esper/item", field.NOP())
        space.write(
            add_esper_item,
            field.SetEventBit(npc_bit.MOG_MOOGLE_ROOM_WOR),
            field.Branch(space.end_address + 1), # skip nops
        )

        space = Reserve(0xcd6bf, 0xcd6c3, "lone wolf add esper/item dialog", field.NOP())
        space.write(
            sound_dialog_esper_item,
        )

    def esper_mod(self, esper):
        self.mog_npc.sprite = self.characters.get_random_esper_item_sprite()
        self.mog_npc.palette = self.characters.get_palette(self.mog_npc.sprite)

        self.esper_item_mod([
            field.AddEsper(esper, sound_effect = False),
        ],
        [
            field.PlaySoundEffect(141),
            field.Dialog(self.espers.get_receive_esper_dialog(esper)),
        ])

    def item_mod(self, item):
        self.mog_npc.sprite = self.characters.get_random_esper_item_sprite()
        self.mog_npc.palette = self.characters.get_palette(self.mog_npc.sprite)

        self.esper_item_mod([
            field.AddItem(item, sound_effect = False),
        ],
        [
            field.PlaySoundEffect(141),
            field.Dialog(self.items.get_receive_dialog(item)),
        ])

    def alternative_item_mod(self):
        # item lone wolf will give as a reward for not picking self.reward1
        import data.text
        item_name = data.text.convert(self.items.get_name(self.reward2.id), data.text.TEXT1) # item names are stored as TEXT2, dialogs are TEXT1

        self.dialogs.set_text(1765, "<line><     >Grrrr…<line><     >You'll never get this<line><     >“" + item_name + "”!<end>")
        self.dialogs.set_text(1742, "<line><      >Got “" + item_name + "”!<end>")

        space = Reserve(0xcd59f, 0xcd59f, "lone wolf item received", field.NOP())
        space.write(
            self.reward2.id,
        )

        space = Reserve(0xcd5be, 0xcd5c0, "item chosen dialog before lone wolf falls", field.NOP())
        space.write(
            field.SetEventBit(npc_bit.MOG_MOOGLE_ROOM_WOR),
        )

        # add pause after lone wolf jumps to wait for falling sound effect
        src = [
            field.HideEntity(self.lone_wolf_npc_id),
            field.RefreshEntities(),
            field.HideEntity(self.invisible_bridge_block_npc_id),
            field.RefreshEntities(),
            field.Return(),
        ]
        space = Write(Bank.CC, src, "lone wolf hide lone wolf and remove bridge block")
        hide_npcs = space.start_address

        space = Reserve(0xcd5d1, 0xcd5d6, "lone wolf hide npcs after fall", field.NOP())
        space.write(
            field.Call(hide_npcs),
            field.Pause(1.5),
        )

    def finish_check_mod(self):
        src = [
            field.ClearEventBit(npc_bit.LONE_WOLF_MOG_NARSHE_CLIFF),
            field.ClearEventBit(npc_bit.LONE_WOLF_NARSHE_CLIFF_BRIDGE),
            field.FinishCheck(),
            field.Return(),
        ]
        space = Write(Bank.CC, src, "lone wolf finish check")
        finish_check = space.start_address

        space = Reserve(0xcd6dd, 0xcd6e0, "lone wolf finish saving mog", field.NOP())
        space.write(
            field.Call(finish_check),
        )

        space = Reserve(0xcd5d7, 0xcd5da, "lone wolf finish saving gold hairpin", field.NOP())
        space.write(
            field.Call(finish_check),
        )

    def moogle_room_character_mod(self, character):
        src = [
            field.RecruitAndSelectParty(character),

            field.HideEntity(self.mog_moogle_room_npc_id),
            field.ClearEventBit(npc_bit.MOG_MOOGLE_ROOM_WOR),
            field.SetEventBit(event_bit.GOT_BOTH_REWARDS_LONE_WOLF),
            field.RefreshEntities(),
            field.FadeInScreen(),
            field.FinishCheck(),
            field.Return(),
        ]
        space = Write(Bank.CC, src, "lone wolf moogle room npc character reward")
        return space.start_address

    def moogle_room_esper_item_mod(self, esper_item_instructions):
        src = [
            esper_item_instructions,

            field.FadeOutScreen(),
            field.WaitForFade(),
            field.HideEntity(self.mog_moogle_room_npc_id),
            field.ClearEventBit(npc_bit.MOG_MOOGLE_ROOM_WOR),
            field.SetEventBit(event_bit.GOT_BOTH_REWARDS_LONE_WOLF),
            field.FadeInScreen(),
            field.FinishCheck(),
            field.Return(),
        ]
        space = Write(Bank.CC, src, "lone wolf moogle room npc esper/item reward")
        return space.start_address

    def moogle_room_esper_mod(self, esper):
        return self.moogle_room_esper_item_mod([
            field.AddEsper(esper),
            field.Dialog(self.espers.get_receive_esper_dialog(esper)),
        ])

    def moogle_room_item_mod(self, item):
        return self.moogle_room_esper_item_mod([
            field.AddItem(item),
            field.Dialog(self.items.get_receive_dialog(item)),
        ])

    def moogle_room_reward_mod(self):
        receive_reward = field.RETURN
        if self.reward1.type == RewardType.CHARACTER:
            receive_reward = self.moogle_room_character_mod(self.reward1.id)
        elif self.reward1.type == RewardType.ESPER:
            receive_reward = self.moogle_room_esper_mod(self.reward1.id)
        elif self.reward1.type == RewardType.ITEM:
            receive_reward = self.moogle_room_item_mod(self.reward1.id)

        src = [
            field.BranchIfEventBitSet(event_bit.RECRUITED_MOG_WOB, "LONE_WOLF_FELL"),
            field.EntityAct(self.mog_moogle_room_npc_id, True,
                field_entity.AnimateSurprised(),
                field_entity.Pause(8),
                field_entity.AnimateStandingFront(),
            ),
            field.Call(receive_reward),
            field.Return(),

            "LONE_WOLF_FELL",
            field.DisableEntityCollision(self.mog_moogle_room_npc_id),
            field.EntityAct(self.mog_moogle_room_npc_id, True,
                field_entity.AnimateLowJump(),
                field_entity.Pause(8),
                field_entity.SetSpeed(field_entity.Speed.FASTEST),
                field_entity.Move(direction.DOWN, 8),
            ),
            field.AddItem(self.reward2.id),
            field.Dialog(1742),
            field.HideEntity(self.mog_moogle_room_npc_id),
            field.ClearEventBit(npc_bit.MOG_MOOGLE_ROOM_WOR),
            field.SetEventBit(event_bit.GOT_BOTH_REWARDS_LONE_WOLF),
            field.FinishCheck(),
            field.Return(),
        ]
        space = Write(Bank.CC, src, "lone wolf npc event second reward not chosen")
        npc_event = space.start_address

        space = Reserve(0xc396c, 0xc3970, "lone wolf npc not saved second reward", field.NOP())
        space.write(
            field.Call(npc_event),
            field.Return(),
        )

    def moogle_room_entrance_event_mod(self):
        # initialize mog npc to match the npc that was on the cliff with lone wolf
        self.mog_moogle_room_npc.sprite = self.mog_npc.sprite
        self.mog_moogle_room_npc.palette = self.mog_npc.palette

        # if mog npc is here (i.e. finished lone wolf event and haven't received the second reward yet)
        # and if did not choose to save lone wolf on cliff
        # change mog npc to lone wolf
        src = [
            field.ReturnIfEventBitClear(npc_bit.MOG_MOOGLE_ROOM_WOR),
            field.ReturnIfEventBitClear(event_bit.RECRUITED_MOG_WOB),
            field.SetSprite(self.mog_moogle_room_npc_id, self.lone_wolf_npc.sprite),
            field.SetPalette(self.mog_moogle_room_npc_id, self.lone_wolf_npc.palette),
            field.RefreshEntities(),
            field.Return(),
        ]
        space = Write(Bank.CC, src, "lone wolf new moogle room entrance event")

        self.maps.set_entrance_event(0x02c, space.start_address - EVENT_CODE_START)

    def ruination_mod(self):
        """
        Ruination mode moves Lone Wolf event from WoB to WoR for both locations:
        1. Initial chase: Narshe WoB -> Narshe WoR
        2. Cliff scene: Tritoch Peak WoB -> Tritoch Peak WoR
        """
        NARSHE_WOB_MAP = 0x014
        NARSHE_WOR_MAP = 0x020
        NARSHE_TREASURE_MAP = 0x01e
        TRITOCH_WOB_MAP = 0x017
        TRITOCH_WOR_MAP = 0x023

        # Tritoch Peak original NPC IDs (for copying the cliff scene to WoR)
        tritoch_lone_wolf_npc_id = 0x1b
        tritoch_mog_npc_id = 0x1c

        # Narshe WoR NPC IDs
        narshe_wor_lone_wolf_npc_id = 0x10
        narshe_wor_treasurehouse_npc_id = 0x14

        # (1) Edit entrance event for Narshe treasure house
        # Entrance event: 0xc395a:  just handles which song is playing.
        # Tile event: (79, 17, 0xcd3ce)
        space = Reserve(0xcd3ce, 0xcd3d3, "Remove Lone Wolf world check", field.NOP())

        # Exit tile event: (79, 18, 0xc3933).  Since we're not using Narshe WOB, just delete the event tile & change exit to go to Narshe WOR
        self.maps.delete_event(map_id=NARSHE_TREASURE_MAP, x=79, y=18)
        treasure_exit_id = 128
        treasure_exit = self.maps.get_exit(treasure_exit_id)
        treasure_exit.dest_map = NARSHE_WOR_MAP

        # (2) Remove lock from Narshe treasure house
        treasure_blocker = self.maps.get_npc(map_id=NARSHE_WOR_MAP, npc_id=narshe_wor_treasurehouse_npc_id)
        treasure_blocker.event_byte = npc_bit.event_byte(npc_bit.ALWAYS_OFF)
        treasure_blocker.event_bit = npc_bit.event_bit(npc_bit.ALWAYS_OFF)

        # (3) Move Lone Wolf initial chase event from Narshe WoB to Narshe WoR
        # Move event tile from (49, 37) on WoB to same position on WoR
        # Event script address: 0xcd424
        old_event = self.maps.get_event(map_id=NARSHE_WOB_MAP, x=49, y=37)

        from data.map_event import MapEvent
        new_event = MapEvent()
        new_event.x = old_event.x
        new_event.y = old_event.y
        new_event.event_address = old_event.event_address

        self.maps.add_event(map_id=NARSHE_WOR_MAP, new_event=new_event)
        self.maps.delete_event(map_id=NARSHE_WOB_MAP, x=old_event.x, y=old_event.y)

        # (3a) Update event script to reference correct WoR NPC ID
        # The event script has 5 references to the NPC that need updating
        space = Reserve(0xcd42d, 0xcd42e, "Edit Lone Wolf NPC_ID 1", narshe_wor_lone_wolf_npc_id)
        space = Reserve(0xcd43b, 0xcd43b, "Edit Lone Wolf NPC_ID 2", narshe_wor_lone_wolf_npc_id)
        space = Reserve(0xcd443, 0xcd443, "Edit Lone Wolf NPC_ID 3", narshe_wor_lone_wolf_npc_id)
        space = Reserve(0xcd44d, 0xcd44d, "Edit Lone Wolf NPC_ID 4", narshe_wor_lone_wolf_npc_id)
        space = Reserve(0xcd454, 0xcd454, "Edit Lone Wolf NPC_ID 5", narshe_wor_lone_wolf_npc_id)

        # (3b) Setup Lone Wolf NPC on Narshe WoR
        # Copy all properties from Narshe WoB Lone Wolf (self.lone_wolf_npc loaded at line 34)
        narshe_wor_lone_wolf = self.maps.get_npc(map_id=NARSHE_WOR_MAP, npc_id=narshe_wor_lone_wolf_npc_id)

        # Copy all visual and behavioral properties
        narshe_wor_lone_wolf.sprite = self.lone_wolf_npc.sprite                    # 56 (Lone Wolf sprite)
        narshe_wor_lone_wolf.palette = self.lone_wolf_npc.palette                  # 4
        narshe_wor_lone_wolf.direction = self.lone_wolf_npc.direction              # 0 (UP)
        narshe_wor_lone_wolf.no_face_on_trigger = self.lone_wolf_npc.no_face_on_trigger
        narshe_wor_lone_wolf.speed = self.lone_wolf_npc.speed                      # 3 (FASTEST)
        narshe_wor_lone_wolf.movement = self.lone_wolf_npc.movement                # 0 (NO_MOVE)
        narshe_wor_lone_wolf.split_sprite = self.lone_wolf_npc.split_sprite
        narshe_wor_lone_wolf.const_sprite = self.lone_wolf_npc.const_sprite
        narshe_wor_lone_wolf.vehicle = self.lone_wolf_npc.vehicle
        narshe_wor_lone_wolf.event_address = self.lone_wolf_npc.event_address      # 0x5eb3 (just return - chase triggered by event tile)
        narshe_wor_lone_wolf.map_layer = self.lone_wolf_npc.map_layer
        narshe_wor_lone_wolf.background_scrolls = self.lone_wolf_npc.background_scrolls
        narshe_wor_lone_wolf.background_layer = self.lone_wolf_npc.background_layer
        narshe_wor_lone_wolf.unknown1 = self.lone_wolf_npc.unknown1
        narshe_wor_lone_wolf.unknown2 = self.lone_wolf_npc.unknown2

        # Override position and visibility for WoR location
        narshe_wor_lone_wolf.x = 49                                                # Same x as WoB
        narshe_wor_lone_wolf.y = 32                                                # Same y as WoB
        narshe_wor_lone_wolf.event_bit = npc_bit.event_bit(0x63f)                 # Same npc_bit as WoB
        narshe_wor_lone_wolf.event_byte = npc_bit.event_byte(0x63f)

        # (4) Add 2nd lone wolf event to WOR Narshe?  Skip for now, due to randomized maps.
        # (5) Add 3rd lone wolf event to WOR Narshe?  Skip for now, due to randomized maps.

        # (6) Move cliff scene from Tritoch Peak WoB to WoR
        # This is SEPARATE from the Narshe chase - it's the Mog/Lone Wolf choice on the cliff

        # Copy Lone Wolf cliff NPC (0x1b on WoB -> new ID on WoR)
        tritoch_lone_wolf_npc = self.maps.get_npc(map_id=TRITOCH_WOB_MAP, npc_id=tritoch_lone_wolf_npc_id)
        tritoch_wor_lone_wolf_npc_id = self.maps.append_npc(map_id=TRITOCH_WOR_MAP, new_npc=tritoch_lone_wolf_npc)
        self.maps.remove_npc(map_id=TRITOCH_WOB_MAP, npc_id=tritoch_lone_wolf_npc_id)

        # Copy Mog cliff NPC (0x1c on WoB -> new ID on WoR)
        tritoch_mog_npc = self.maps.get_npc(map_id=TRITOCH_WOB_MAP, npc_id=tritoch_mog_npc_id)
        tritoch_wor_mog_npc_id = self.maps.append_npc(map_id=TRITOCH_WOR_MAP, new_npc=tritoch_mog_npc)
        self.maps.remove_npc(map_id=TRITOCH_WOB_MAP, npc_id=tritoch_mog_npc_id)

        # IMPORTANT: Update instance variables to point to Tritoch WoR NPCs
        # These are used by character_mod(), esper_mod(), item_mod(), and other methods
        # that modify the cliff scene reward and animations
        self.lone_wolf_npc_id = tritoch_wor_lone_wolf_npc_id
        self.mog_npc_id = tritoch_wor_mog_npc_id
        self.lone_wolf_npc = self.maps.get_npc(map_id=TRITOCH_WOR_MAP, npc_id=tritoch_wor_lone_wolf_npc_id)
        self.mog_npc = self.maps.get_npc(map_id=TRITOCH_WOR_MAP, npc_id=tritoch_wor_mog_npc_id)
        self.mog_npc.x = 9   # Patch some data? showed up in the wrong spot & looking weird
        self.mog_npc.y = 16
        self.mog_npc.split_sprite = 0
        self.mog_npc.event_address = 0x2d5df  # tritoch_mog_npc.event_address  # 0xcd5df

        # Copy bridge animation NPC (runs across bridge during cliff scene)
        lonewolf_bridge_npc_id = 0x1a
        lonewolf_bridge_npc = self.maps.get_npc(map_id=TRITOCH_WOB_MAP, npc_id=lonewolf_bridge_npc_id)
        wor_lonewolf_bridge_npc_id = self.maps.append_npc(map_id=TRITOCH_WOR_MAP, new_npc=lonewolf_bridge_npc)
        self.maps.remove_npc(map_id=TRITOCH_WOB_MAP, npc_id=lonewolf_bridge_npc_id)

        # Copy invisible bridge blocker NPC (blocks bridge until player chooses mog or lone wolf)
        #bridge_block_npc_id = 0x1d
        #bridge_block_npc = self.maps.get_npc(map_id=TRITOCH_WOB_MAP, npc_id=bridge_block_npc_id)
        from data.npc import InvisibleBlockNPC
        bridge_block_npc = InvisibleBlockNPC(14, 20)
        bridge_block_npc.event_bit = npc_bit.event_bit(0x641)
        bridge_block_npc.event_byte = npc_bit.event_byte(0x641)
        wor_bridge_block_npc_id = self.maps.append_npc(map_id=TRITOCH_WOR_MAP, new_npc=bridge_block_npc)
        #self.maps.remove_npc(map_id=TRITOCH_WOB_MAP, npc_id=bridge_block_npc_id)
        self.invisible_bridge_block_npc_id = wor_bridge_block_npc_id
        #bridge_block_wor_npc = self.maps.get_npc(map_id=TRITOCH_WOR_MAP, npc_id=wor_bridge_block_npc_id)


        # (6a) Move Tritoch Peak cliff scene event tiles from WoB to WoR
        # These event tiles trigger the animations and dialog for the cliff scene
        event_tile_xy = [(22, 20, 0xcd4a8),
                         (8, 18, 0xcd4dd),
                         (9, 18, 0xcd4fe),
                         (10, 18, 0xcd4f1),
                         (8, 19, 0xcd523),
                         (10, 19, 0xcd523),
                         (9, 20, 0xcd523)]
        for xy in event_tile_xy:
            old_event = self.maps.get_event(map_id=TRITOCH_WOB_MAP, x=xy[0], y=xy[1])
            new_event = MapEvent()
            new_event.x = old_event.x
            new_event.y = old_event.y
            new_event.event_address = old_event.event_address
            self.maps.add_event(map_id=TRITOCH_WOR_MAP, new_event=new_event)
            self.maps.delete_event(map_id=TRITOCH_WOB_MAP, x=old_event.x, y=old_event.y)

        # (6b) Update cliff scene event scripts to reference WoR NPC IDs
        # Event scripts contain hardcoded NPC IDs that need to be updated after copying to WoR

        # Update bridge NPC references (6 locations in event script)
        addresses = [0xcd4b1, 0xcd4b3, 0xcd4b5, 0xcd4b9, 0xcd4c0, 0xcd4c5]
        for i, addr in enumerate(addresses):
            space = Reserve(addr, addr, "edit lone wolf bridge animation " + str(i), wor_lonewolf_bridge_npc_id)

        # Update bridge blocker NPC references (3 locations in event script)
        # 0xcd588: Create object, 0xcd58a: Show object, 0xcd6db: Hide object
        bridge_block_addresses = [0xcd588, 0xcd58a, 0xcd6db]
        for i, addr in enumerate(bridge_block_addresses):
            space = Reserve(addr, addr, "edit lone wolf bridge blocker " + str(i), wor_bridge_block_npc_id)

        # Update Mog NPC references (26 locations in event script)
        # Note: addresses 0xcd67c-0xcd68d are in the range that character_mod() overwrites,
        # so skip them if the reward is a character to avoid space conflicts
        self.mog_addresses = [0xcd4cc, 0xcd4d0, 0xcd4d4, 0xcd514, 0xcd538, 0xcd53f, 0xcd543, 0xcd548, 0xcd54f, 0xcd557,
                         0xcd573, 0xcd5ab, 0xcd5b5, 0xcd591, 0xcd5fc,
                         # 0xcD61F, 0xcD626, 0xcD62A, 0xcD62F, 0xcD648, 0xcD674,
                         0xcd67c, 0xcd681, 0xcd685, 0xcd689, 0xcd68d,
                         0xcd6b1, 0xcd6bb, 0xcd6c4, 0xcd6ca, 0xcd6cb, 0xcd6d4]
        # Addresses that conflict with character_mod()'s Reserve(0xcd67c, 0xcd696)
        char_mod_conflict_range = range(0xcd67c, 0xcd697)
        for i, addr in enumerate(self.mog_addresses):
            if self.reward1.type == RewardType.CHARACTER and addr in char_mod_conflict_range:
                continue  # Skip - character_mod() will overwrite this entire section
            space = Reserve(addr, addr, "edit lone wolf mog animation " + str(i), tritoch_wor_mog_npc_id)

        # Update Lone Wolf NPC references (12 locations in event script)
        self.lonewolf_addresses = [0xcd4ce, 0xcd4d2, 0xcd566, 0xcd569, 0xcd58f, 0xcd5c2, 0xcd5c5, 0xcd5dc,
                              0xcd697, 0xcd69a, 0xcd6a7, 0xcd6aa]
        for i, addr in enumerate(self.lonewolf_addresses):
            space = Reserve(addr, addr, "edit lone wolf animation " + str(i), tritoch_wor_lone_wolf_npc_id)

        # (6c) Simplify cliff scene entry condition
        # In ruination mode, only require seeing the first Narshe chase animation
        # (instead of all three chase scenes from vanilla WoB)
        space = Reserve(0xcd4a8, 0xcd4af, "edit entry condition for LoneWolf", field.NOP())
        space.write(field.BranchIfAny([event_bit.CHASING_LONE_WOLF1, False, 0x23D, True],
                                      field.RETURN))
