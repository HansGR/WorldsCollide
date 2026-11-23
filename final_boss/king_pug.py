from final_boss.final_boss import FinalBoss

class KingPug(FinalBoss):
    # pug (the green one), giant. (so far he has only the looks: his stats, script and attacks are
    # final kefka's)
    NAME = "King Pug"

    PUG = "Pug"
    SCALE = (3, 1)                          # pug is 32x32 pixels: 96x96
    LOWER = 32                              # pixels: clear of the boxes at the top

    def enemies_mod(self, enemies):
        self.pug = enemies.get_enemy(self.PUG)
        self.enemy(enemies).name = self.NAME

    def battle_mod(self):
        self.giant_sprite_mod(self.pug, scale = self.SCALE, lower = self.LOWER)
