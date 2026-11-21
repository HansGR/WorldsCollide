from final_boss.final_boss import FinalBoss

class Grampaluma(FinalBoss):
    # dadaluma, giant. (so far he has only the looks: his stats, script and attacks are final kefka's)
    NAME = "Grampaluma"

    DADALUMA = "Dadaluma"
    LOWER = 40                              # pixels: his sprite is 81 high, and clear of the boxes at the top

    def enemies_mod(self, enemies):
        self.enemy(enemies).name = self.NAME

    def battle_mod(self):
        from data.bosses import name_enemy

        # dadaluma is 88 pixels wide, so he is not twice his size but the 1.45 times that fit
        self.giant_sprite_mod(name_enemy[self.DADALUMA], lower = self.LOWER)
