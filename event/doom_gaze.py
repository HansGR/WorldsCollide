from event.event import *

class DoomGaze(Event):
    def name(self):
        return "Doom Gaze"

    def character_gate(self):
        return self.characters.SETZER # gate for airship option

    def init_rewards(self):
        self.reward = self.add_reward(RewardType.ESPER | RewardType.ITEM)

    def mod(self):
        self.magicite_npc_id = 0x12
        self.magicite_npc = self.maps.get_npc(0x11, self.magicite_npc_id)

        self.dialog_mod()
        if self.args.doom_gaze_no_escape:
            self.doom_gaze_battle_mod()

        if self.args.race:
            self.race_look_mod()

        if self.reward.type == RewardType.ESPER:
            self.esper_mod(self.reward.id)
        elif self.reward.type == RewardType.ITEM:
            self.item_mod(self.reward.id)

        self.log_reward(self.reward)

    def dialog_mod(self):
        space = Reserve(0xa00c2, 0xa00c4, "magicite popped out of doom gaze's mouth dialog", field.NOP())
        space.write(
            field.SetEventBit(event_bit.DEFEATED_DOOM_GAZE),
        )

    def doom_gaze_battle_mod(self):
        import instruction.asm as asm

        boss_pack_id = self.get_boss("Doom Gaze")
        boss_formation_id = self.enemies.packs.get_formations(boss_pack_id)[0]

        src = [
            Read(0x2e6f50, 0x2e6f57),   # copy load/store background and set 8 bit a register
            asm.LDA(0x04, asm.IMM8),    # load 0b0100 into a register for front attack
            asm.STA(0x11e3, asm.ABS),   # store battle type in the same place invoke_battle_type does
            asm.RTS(),
        ]
        space = Write(Bank.EE, src, "doom gaze set battle type")
        set_battle_type = space.start_address

        space = Reserve(0x2e6f46, 0x2e6f57, "doom gaze set formation", asm.NOP())
        space.write(
            asm.LDA(boss_formation_id, asm.IMM16),
            asm.STA(0x11e0, asm.ABS),   # store formation at $11e0 (low byte) and $11e1 (high byte)
            asm.JSR(set_battle_type, asm.ABS),
        )

        # assume only have to fight boss in doom gaze's place once (i.e. no escape and chase until defeated)
        # after the fight, set the doom gaze defeated event bit
        space = Reserve(0x2e019c, 0x2e01a2, "doom gaze defeated check for bahamut scene in airship", asm.NOP())
        space.write(
            asm.LDA(0x01, asm.IMM8),    # doom gaze defeated bit in event byte 1dd2
            asm.TSB(0x1dd2, asm.ABS),   # set doom gaze defeated event bit
        )

    def race_look_mod(self):
        # the magicite npc record stays vanilla for every kind (a baked
        # chest said "item here" in the rom); an item repaints it to the
        # chest at map load, and the receive flash picks its kind at
        # runtime.  the grant and dialog are already kind-blind (AddEsper/
        # AddItem and the receive dialogs compile to the same slot-driven
        # commands in race builds)
        from obfuscation import rewards
        slot = rewards.register_check(self.reward)

        self.race_repaint_npc_entrance(0x11, self.magicite_npc_id, slot, chest = True)

        src = [
            field.BranchIfRewardKindNot(slot, "esper", "NO_FLASH"),
            Read(0xa00d6, 0xa00d7),     # flash the screen white
            "NO_FLASH",
            Read(0xa00d8, 0xa00dd),     # leader animation, collision back on
            field.Branch(0xa00de),      # the receive call
        ]
        space = Write(Bank.CA, src, "doom gaze race receive flash")
        receive_flash = space.start_address
        space = Reserve(0xa00d6, 0xa00dd, "doom gaze receive flash branch", field.NOP())
        space.write(
            field.Branch(receive_flash),
        )

    def receive_reward_mod(self, reward_instructions):
        src = [
            reward_instructions,
            field.FinishCheck(),
            field.Return(),
        ]
        space = Write(Bank.CA, src, "doom gaze receive reward")
        receive_reward = space.start_address

        space = Reserve(0xa00de, 0xa00e2, "doom gaze receive magicite", field.NOP())
        space.write(
            field.Call(receive_reward),
        )

    def esper_mod(self, esper):
        self.receive_reward_mod([
            field.Dialog(self.espers.get_receive_esper_dialog(esper)),
            field.AddEsper(esper, sound_effect = False),
        ])

    def item_mod(self, item):
        if not self.args.race:
            # race builds keep the vanilla record and select the look at
            # runtime instead (race_look_mod)
            self.magicite_npc.sprite = 106
            self.magicite_npc.palette = 6
            self.magicite_npc.split_sprite = 1
            self.magicite_npc.direction = direction.DOWN

            space = Reserve(0xa00d6, 0xa00d7, "doom gaze flash screen white when receiving esper", field.NOP())

        self.receive_reward_mod([
            field.Dialog(self.items.get_receive_dialog(item)),
            field.AddItem(item, sound_effect = False),
        ])
