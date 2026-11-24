from memory.space import Reserve, Read

from final_boss.final_boss import FinalBoss, ABILITY_DATA_START

SPECIAL_ATTACK_GRAPHICS = 0xf37c0           # the blow an enemy's special attack is shown with, a byte for each enemy

class Juggernaut(FinalBoss):
    # tunnelarmr, giant: armor that blows do little to, and that answers magic. final kefka's stats
    # with much more defense and less magic defense, weak to bolt and water as tunnelarmr is
    #
    #   Havoc Wing  Drill, with the looks of tunnelarmr's
    #   Goner       Soul Burn: it takes from mp what it takes from hp
    #   HyperDrive  Crush, with the looks of io's
    #   Revenger    (mirrorcast in its place: he casts the esper that one of the party has equipped)
    NAME = "Juggernaut"
    DEFENSE, MAGIC_DEFENSE = 1.8, 0.75      # of final kefka's

    TUNNEL_ARMOR = "TunnelArmr"
    SPECIAL_NAME = "Drill"
    SHADOW_COLOR, SHADOW_ROWS = 1, 12
    SCALE = (4, 3)                          # his sprite is 95x59 pixels without its shadow: 127 wide is the most that fits
    LOWER = 40                              # pixels: clear of the boxes at the top, and lower still

    BOLT, WATER = 0x04, 0x80                # elements

    # the armors' attacks, where final kefka has fire 3, ice 3 and bolt 3
    LASERS = ["Atomic Ray", "Shrapnel", "Diffuser"]

    # hit by magic: one of these, at any hp
    MAGIC, X_MAGIC, LORE, SUMMON = 0x02, 0x17, 0x0c, 0x19       # commands
    MAGIC_ANSWERS = ["Missile", "Diffuser", "Atomic Ray"]

    ABILITY_NAMES = {
        "Goner"         : "Soul Burn",
        "HyperDrive"    : "Crush",
        "Revenger"      : "MirrorCast",     # (what his mirrorcast is named by: he does not use the attack)
    }
    GONER_TEXT = "MagiTek engine going critical!<wait 60 frames><end>"
    SOUL_BURN_POWER = 120                   # 12x rasp's
    SOUL_BURN_EFFECT = 0x47                 # a special effect that does nothing
    POWER_BYTE = 6                          # in an attack's data

    LAUNCHER = "Launcher"
    IO = "Io"                               # crush is his special attack

    # mirrorcast: the esper he does not cast (ragnarok changes its target into an item), and what
    # he does if there is none to cast. with palidor he jumps, and lands on one of the party
    NO_MIRROR_CASTS = {"Ragnarok" : 16}
    GOLEM_HP = 9999                         # the wall golem makes for him: the damage of physical attacks it takes

    # statuses final kefka is protected from and he is not: the party's espers set them on him
    # with mirrorcast (fenrir, phantom, carbunkl, zoneseek, kirin) and the party can
    STATUSES = ["image", "clear", "reflect", "safe", "shell", "regen", "seizure"]
    # (regen for kirin. the game takes one of regen and seizure being blocked for both, so he can be
    # sapped as well)
    FIX_VANISH_DOOM = True                  # (clear, without the fix: a spell that kills would not miss him)
    NO_MIRROR_CAST = "Diffuser"

    HIT_BY_COMMAND, NOT_CHARGING = 0x01, 0x15                   # script conditions

    def enemies_mod(self, enemies):
        self.tunnel_armor = enemies.get_enemy(self.TUNNEL_ARMOR)
        self.io = enemies.get_enemy(self.IO)
        juggernaut = self.enemy(enemies)
        juggernaut.name = self.NAME
        juggernaut.special_name = self.SPECIAL_NAME
        juggernaut.defense = min(round(juggernaut.defense * self.DEFENSE), 2 ** 8 - 1)
        juggernaut.magic_defense = min(round(juggernaut.magic_defense * self.MAGIC_DEFENSE), 2 ** 8 - 1)
        juggernaut.weak_elements |= self.BOLT | self.WATER
        for status in self.STATUSES:
            setattr(juggernaut.status_immunities, status, 0)

    def scripts_mod(self, scripts):
        # (his battle program is written out in final_boss/README.md: keep it up to date with this)
        import data.enemy_script_commands as ai_instr
        from data.spell_names import name_id

        special, train, nothing = (name_id[name] for name in ["Special", "Train", "Nothing"])
        script = scripts.get_script(self.ENEMY)

        # above 53% hp, every other turn
        fire, ice, bolt = (name_id[name] for name in self.LASERS)
        script.replace(ai_instr.RandomAttack(name_id["Fire 3"], train, special), ai_instr.RandomAttack(fire, train, special))
        script.replace(ai_instr.RandomAttack(name_id["Ice 3"], train, special), ai_instr.RandomAttack(ice, train, special))
        script.replace(ai_instr.RandomAttack(name_id["Bolt 3"], nothing, special), ai_instr.RandomAttack(bolt, nothing, special))

        # at 53% hp and below, the turns after goner (soul burn): mirrorcast for revenger, and the
        # launcher in one roll of the last
        from data.enemy_script_custom_commands import MIRROR_CAST
        scripts.enemy_script_custom_commands.command_attacks_mod(
            {}, mirror_cast = (list(self.NO_MIRROR_CASTS.values()), name_id[self.NO_MIRROR_CAST], self.enemy_id, name_id["Revenger"]))
        revenger, launcher = name_id["Revenger"], name_id[self.LAUNCHER]
        script.replace(ai_instr.RandomAttack(special, train, revenger), ai_instr.RandomAttack(special, train, MIRROR_CAST))
        script.replace(ai_instr.RandomAttack(train, special, revenger), ai_instr.RandomAttack(train, special, MIRROR_CAST))
        script.replace(ai_instr.RandomAttack(special, special, nothing), ai_instr.RandomAttack(special, launcher, nothing))

        # hit by a spell (magic, x-magic, a lore or an esper): he answers, before what else he does
        # when he is hit and after what he does when he dies. not while he charges up, as kefka's
        instructions = script.instructions
        counters = instructions.index(ai_instr.EndIf(), instructions.index(ai_instr.EndMainLoop()))
        answers = [name_id[name] for name in self.MAGIC_ANSWERS]
        answer = []
        for commands in ((self.MAGIC, self.X_MAGIC), (self.LORE, self.SUMMON)):
            answer += [
                ai_instr.If(self.HIT_BY_COMMAND, *commands),
                ai_instr.If(self.NOT_CHARGING, 0x00, 0x00),
                ai_instr.RandomAttack(*answers),
                ai_instr.EndIf(),
            ]
        script.insert(counters + 1, answer)

    def data_mod(self, data):
        from data.spell_names import name_id

        self.rename_abilities(data, self.ABILITY_NAMES)
        self.goner_text_mod(data, self.GONER_TEXT, room = True)

        # soul burn: goner with 12x the power of rasp, which takes as much from mp as from hp
        goner = ABILITY_DATA_START + name_id["Goner"] * 14
        data.rom.set_bytes(goner + self.POWER_BYTE, [self.SOUL_BURN_POWER])
        self.mp_damage_mod(data, name_id["Goner"], self.SOUL_BURN_EFFECT)

    def battle_mod(self):
        self.giant_sprite_mod(self.tunnel_armor, self.SHADOW_COLOR, self.SHADOW_ROWS,
                              scale = self.SCALE, lower = self.LOWER,
                              palette = self.chrome(self.monster_palette(self.tunnel_armor)))
        self.golem_mod(self.GOLEM_HP)

        # his special attack is shown as tunnelarmr's is
        graphic = Read(SPECIAL_ATTACK_GRAPHICS + self.tunnel_armor, SPECIAL_ATTACK_GRAPHICS + self.tunnel_armor)
        space = Reserve(SPECIAL_ATTACK_GRAPHICS + self.enemy_id, SPECIAL_ATTACK_GRAPHICS + self.enemy_id, "final kefka special attack graphic")
        space.write(graphic)

        # with palidor's mirrorcast he is carried off, and lands on one of the party
        self.carried_jump_mod()

        # crush (hyperdrive) is shown as io's special attack is
        from data.spell_names import name_id
        self.attack_special_animation_mod(name_id["HyperDrive"], self.io)

        # he charges up before soul burn as final kefka does before goner, without the laughing head:
        # it is a picture of nothing
        HEAD_PIXELS, PALETTE_COLORS = 32, 8
        self.goner_sprite_mod([[0] * HEAD_PIXELS for _ in range(HEAD_PIXELS)], [0] * PALETTE_COLORS)

    @staticmethod
    def chrome(palette):
        # tunnelarmr's palette in chrome: his purple body (colors 3 to 7) in a dark cerulean chrome, and
        # his wheels and claws (8 to 11, and 14: olive) in bright chrome with a little blue. the red
        # of the mark on his nose (12 and 15), the white and the dark outline stay
        BODY, WHEELS = range(3, 8), [8, 9, 10, 11, 14]
        DARK, BRIGHT = 0.90, 1.25
        BODY_TINT, WHEELS_TINT = (0.45, 1.05, 1.30), (0.94, 0.98, 1.10)
        colors = list(palette)
        for index, (red, green, blue) in enumerate(palette):
            if index in BODY or index in WHEELS:
                body = index in BODY
                brightness = (0.30 * red + 0.59 * green + 0.11 * blue) * (DARK if body else BRIGHT)
                colors[index] = tuple(min(max(round(brightness * tint), 0), 31) for tint in (BODY_TINT if body else WHEELS_TINT))
        return colors
