from memory.space import Bank, Space, Reserve, Allocate, Free, Write, Read
import data.direction as direction

import data.event_bit as event_bit
import data.event_word as event_word
import data.npc_bit as npc_bit
import data.battle_bit as battle_bit
import data.dialog_id as dialog_id

import instruction.asm as asm
import instruction.field as field
import instruction.field.entity as field_entity
import instruction.world as world
import instruction.vehicle as vehicle

from instruction.event import EVENT_CODE_START
from event.event_reward import RewardType, Reward

class Event():
    def __init__(self, events, rom, args, dialogs, characters, items, maps, enemies, espers, shops):
        self.events = events
        self.rom = rom
        self.args = args
        self.dialogs = dialogs
        self.characters = characters
        self.items = items
        self.maps = maps
        self.enemies = enemies
        self.espers = espers
        self.shops = shops
        self.rewards = []

        self.rewards_log = []
        self.changes_log = []

    def name(self):
        raise NotImplementedError(self.__class__.__name__ + " event name")

    def character_gate(self):
        return None

    def characters_required(self):
        return 1

    def add_reward(self, possible_types):
        new_reward = Reward(self, possible_types)
        self.rewards.append(new_reward)
        return new_reward

    def init_rewards(self):
        pass

    def init_event_bits(self, space):
        pass

    def race_slot(self, reward):
        """Race builds: the reward's slot in the masked reward table -
        registered the first time any mod asks for it, the same value
        after, so mods may ask in any order (an entrance or song hook
        written before the reward mod runs gets the same slot)."""
        from obfuscation import rewards
        slots = self.__dict__.setdefault("_race_slots", {})
        if reward not in slots:
            slots[reward] = rewards.register_check(reward)
        return slots[reward]

    def race_decoy_npc(self, map_id, npc_id, slot, **repaint_arms):
        """Race builds: give a check npc record the kind-neutral decoy
        sprite (the one every esper/item build bakes) and chain the
        entrance repaint that restores the real look at map load - see
        race_repaint_npc_entrance for the arms."""
        npc = self.maps.get_npc(map_id, npc_id)
        npc.sprite = self.characters.get_random_esper_item_sprite()
        npc.palette = self.characters.get_palette(npc.sprite)
        self.race_repaint_npc_entrance(map_id, npc_id, slot, **repaint_arms)

    # vanilla-wc's object looks for non-character rewards: the magicite
    # shard (esper checks) and the treasure chest (item checks at sites
    # that show one).  sprite/palette/direction as every non-race
    # esper_mod/item_mod bakes them; the split-sprite record flag is
    # applied at runtime instead (field.SetSplitSprite)
    MAGICITE_SPRITE, MAGICITE_PALETTE = 91, 2
    CHEST_SPRITE, CHEST_PALETTE = 106, 6

    def race_magicite_look_src(self, npc_id):
        import data.direction as direction
        return [
            field.SetSprite(npc_id, self.MAGICITE_SPRITE),
            field.SetPalette(npc_id, self.MAGICITE_PALETTE),
            field.SetSplitSprite(npc_id, direction.UP),
        ]

    def race_chest_look_src(self, npc_id):
        import data.direction as direction
        return [
            field.SetSprite(npc_id, self.CHEST_SPRITE),
            field.SetPalette(npc_id, self.CHEST_PALETTE),
            field.SetSplitSprite(npc_id, direction.DOWN),
        ]

    def race_repaint_npc_entrance(self, map_id, npc_id, slot, palette = True,
                                  magicite = False, chest = False):
        """Race builds: chain an entrance event onto the map's existing
        one that repaints a check npc at load time to what its kind's
        non-race build would have baked: the reward character's sprite
        for a character, and optionally the magicite shard for an esper
        (`magicite=True`) or the treasure chest for an item
        (`chest=True`) at sites whose non-race builds show them.  The
        npc record itself stays kind- and id-blind in the rom.
        `palette=False` repaints only the sprite (for npcs whose palette
        is scene state, like the ancient castle's gray statue)."""
        old_entrance = self.maps.get_entrance_event(map_id)
        src = [
            field.BranchIfRewardKindNot(slot, "character", "NOT_CHARACTER"),
            field.SetRewardSprite(npc_id, slot),
        ]
        if palette:
            src += [
                field.SetRewardPalette(npc_id, slot),
            ]
        if magicite or chest:
            src += [
                field.Branch("NPC_DONE"),
                "NOT_CHARACTER",
            ]
            if magicite:
                src += [
                    field.BranchIfRewardKindNot(slot, "esper", "NOT_ESPER"),
                    *self.race_magicite_look_src(npc_id),
                    field.Branch("NPC_DONE"),
                    "NOT_ESPER",
                ]
            if chest:
                src += [
                    field.BranchIfRewardKindNot(slot, "item", "NPC_DONE"),
                    *self.race_chest_look_src(npc_id),
                ]
        else:
            src += [
                "NOT_CHARACTER",
            ]
        src += [
            "NPC_DONE",
            field.Branch(EVENT_CODE_START + old_entrance),
        ]
        space = Write(Bank.CA, src, f"{self.name()} race npc repaint entrance")
        self.maps.set_entrance_event(map_id, space.start_address - EVENT_CODE_START)

    def get_boss(self, original_boss_name, log_change = True):
        pack_id = self.enemies.get_event_boss(original_boss_name)

        if (self.args.boss_battles_shuffle or self.args.boss_battles_random) and log_change:
            boss_name = self.enemies.packs.get_name(pack_id)
            self.log_change(original_boss_name, boss_name)
        return pack_id

    # return the boss in place of the given boss_name
    # example
    # get_replacement_formation("Goddess")
    # if you fight Ultros in the Goddess location, return Ultros
    def get_replacement_formation(self, boss_name):
        from data.bosses import pack_name
        replacement = self.get_boss(boss_name, False)
        location_boss = pack_name[replacement]
        formation_id = self.enemies.formations.get_id(location_boss)
        return self.enemies.formations.formations[formation_id]

    def log_reward(self, reward, prefix = "", suffix = ""):
        reward_string = prefix
        if reward.type == RewardType.CHARACTER:
            reward_string += self.characters.get_name(reward.id)
        elif reward.type == RewardType.ESPER:
            reward_string += self.espers.get_name(reward.id)
        elif reward.type == RewardType.ITEM:
            reward_string += self.items.get_name(reward.id)
        self.rewards_log.append(reward_string + suffix)

    def log_change(self, original, new):
        self.changes_log.append(f"    {original:<14} -> {new}")

    def log_string(self):
        log_string = f"{self.name():<30}"
        if self.rewards_log:
            log_string += f" {', '.join(self.rewards_log)}"
        if self.changes_log:
            log_string += '\n' + '\n'.join(self.changes_log)
        return log_string

    def mod(self):
        raise NotImplementedError(self.__class__.__name__ + " event must implement mod")
