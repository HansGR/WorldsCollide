from final_boss.final_boss import FinalBoss, HELPERS

class Grampaluma(FinalBoss):
    # dadaluma, giant, who calls in two iron fists as dadaluma does. (a prototype: his stats, attacks
    # and the rest of his script are final kefka's, and the iron fists are as they are in zozo)
    NAME = "Grampaluma"

    DADALUMA = "Dadaluma"
    HELPER = "Iron Fist"

    # dadaluma is 88x56 pixels. the monsters of the formation share 16x16 tiles of graphics: he has
    # the top 16x10 (125x80 pixels: 1.43 times his size), and the iron fists 6x6 each under him
    TILES = (16, 10)
    HELPER_TILES = (6, 6)

    # on the screen, (x, y) in steps of 8 pixels: he is clear of the boxes at the top
    POSITION = (0, 7)
    HELPER_POSITIONS = [(15, 5), (15, 12)]

    CALL_TIME = 30                          # he calls them when they are gone and his timer is above this
    CALL_ANIMATION = 3

    def enemies_mod(self, enemies):
        self.enemy(enemies).name = self.NAME
        self.helpers_mod(enemies, enemies.get_enemy(self.HELPER), self.HELPER_POSITIONS, self.POSITION)

    def scripts_mod(self, scripts):
        import data.enemy_script_commands as ai_instr

        script = scripts.get_script(self.ENEMY)
        intro_end = script.instructions.index(ai_instr.EndIf())
        script.insert(intro_end + 1, [
            ai_instr.If(0x0b, self.CALL_TIME, 0x00),    # if his timer is above this
            ai_instr.Misc(0x00, 0x00),                  # reset his timer
            ai_instr.If(0x12, HELPERS, 0x00),           # if the helpers are dead or not in the battle
            ai_instr.ChangeEnemies(self.CALL_ANIMATION, 0x00, HELPERS),     # bring them in
            ai_instr.EndIf(),
        ])

    def battle_mod(self):
        from data.bosses import name_enemy

        width, height = self.TILES
        dadaluma = name_enemy[self.DADALUMA]
        sprite, _ = self.enemy_sprite(dadaluma)
        self.giant_sprite_mod(dadaluma, scale = (height * 8, len(sprite)))
        self.helpers_layout_mod(self.TILES, self.HELPER_TILES, len(self.HELPER_POSITIONS))
