from final_boss.final_boss import FinalBoss

class Negarapa(FinalBoss):
    # nerapa, giant
    NAME = "Negarapa"
    NERAPA = "Nerapa"
    SCALE = (7, 4)                          # her sprite is 64 pixels high: twice that fills the mold, and her head would be behind the boxes at the top
    LOWER = 16                              # pixels: clear of the boxes at the top

    def enemies_mod(self, enemies):
        self.nerapa = enemies.get_enemy(self.NERAPA)
        negarapa = self.enemy(enemies)
        negarapa.name = self.NAME

    def battle_mod(self):
        self.giant_sprite_mod(self.nerapa, scale = self.SCALE, lower = self.LOWER)
