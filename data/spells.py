from data.spell import Spell
from data.spell_names import id_name, name_id
from data.ability_data import AbilityData
from data.structures import DataArray
from memory.space import Bank, Space, Reserve, Allocate, Free, Write, Read

class Spells:
    BLACK_MAGIC_COUNT = 24
    EFFECT_MAGIC_COUNT = 21
    WHITE_MAGIC_COUNT = 9
    SPELL_COUNT = BLACK_MAGIC_COUNT + EFFECT_MAGIC_COUNT + WHITE_MAGIC_COUNT

    NAMES_START = 0x26f567
    NAMES_END = 0x26f6e0
    NAME_SIZE = 7

    ABILITY_DATA_START = 0x046ac0
    ABILITY_DATA_END = 0x046db3

    # (default) order spells appear in menu going left to right, top to bottom
    # put white magic before black and effect magic
    import itertools
    spell_menu_order = itertools.chain(range(45, 54), range(45))

    def __init__(self, rom, args):
        self.rom = rom
        self.args = args

        self.name_data = DataArray(self.rom, self.NAMES_START, self.NAMES_END, self.NAME_SIZE)
        self.ability_data = DataArray(self.rom, self.ABILITY_DATA_START, self.ABILITY_DATA_END, AbilityData.DATA_SIZE)

        self.spells = []
        for spell_index in range(len(self.name_data)):
            spell = Spell(spell_index, self.name_data[spell_index], self.ability_data[spell_index])
            self.spells.append(spell)


    def get_id(self, name):
        return name_id[name]

    def get_name(self, id):
        if id == 0xff:
            return ""
        return self.spells[id].get_name()

    def get_random(self, count = 1, exclude = None):
        if exclude is None:
            exclude = []

        import random
        possible_spell_ids = [spell.id for spell in self.spells if spell.id not in exclude]
        count = min(len(possible_spell_ids), count)
        return random.sample(possible_spell_ids, count)

    def get_replacement(self, spell_id, exclude):
        ''' get a random spell from the same tier as the given spell_id '''
        import random
        from data.esper_spell_tiers import tiers

        same_tier = next((tier for tier in tiers if spell_id in tier), [])
        replacements = [i for i in same_tier if i not in exclude]
        replacement = random.choice(replacements) if len(replacements) else None
        return replacement

    def no_mp_scan(self):
        scan_id = name_id["Scan"]
        self.spells[scan_id].mp = 0

    def no_mp_warp(self):
        warp_id = name_id["Warp"]
        self.spells[warp_id].mp = 0

    def ultima_254_mp(self):
        ultima_id = name_id["Ultima"]
        self.spells[ultima_id].mp = 254

    def ultima_random_color(self):
        # Ultima spell animation color is controlled in 3 places:
        # 1. Ultima palette at Battle Animation Palettes ($D26000) index 113 and index 110
        #   --> Modifying palette 110 will affect other spells (Gem Dust, Storm)
        # https://www.ff6hacking.com/wiki/doku.php?id=ff3:ff3us:doc:asm:list:battle_animation_palette
        #
        # 2. Ultima spell pointers to palettes in Attack Animation Data ($D07FB2):
        # Ultima is spell index 20 in the attack animation data (data at $D0/80CA)
        #   --> palette bg1 @ offset + 0x07 = $D0/80D1.  vanilla value = 110.
        #   --> palette bg3 @ offset + 0x08 = $D0/80D2.  vanilla value = 113.
        # https://www.ff6hacking.com/wiki/doku.php?id=ff3:ff3us:doc:asm:fmt:attack_animation_data
        #
        # 3. Change the color modifications in the Battle Animation Scripts ($D00000):
        # Ultima bg1 is script pointer $00E7;  Ultima bg3 is script pointer $00E8.
        # https://www.ff6hacking.com/wiki/doku.php?id=ff3:ff3us:doc:asm:codes:battle_animation_script
        # Color appears to be in battle animation script, somewhere in here:
        # D0/56CB: AF 60                    set background color subtraction to 0 (red)  <--
        # D0/56CD: 89 0F                    loop start (15 times)
        # D0/56CF: B6 C2                    increase background color subtraction by 2 (blue) <-- fade (r,g) from bg by 2 steps each time.
        # D0/56D1: AE 42                    update (bg2) hdma scroll data (horizontal)
        # D0/56D3: 00                       [$00]
        # D0/56D4: 8A                       loop end
        # D0/56D5: 89 7E                    loop start (126 times)
        # D0/56D7: A3 16 31                 shift colors (1..7) of bg1 animation/esper palette left (3 loops per shift) <-- what does this do?
        # D0/56DA: AE 42                    update (bg2) hdma scroll data (horizontal)
        # D0/56DC: A6 00 00 01              move circle (+0,+0) and grow by 1
        # D0/56E0: F7 C0                    wait until scanline 192
        # D0/56E2: A7                       update circle
        # D0/56E3: 00                       [$00]
        # D0/56E4: 8A                       loop end

        # Strategy should probably be:
        # --> Identify several palettes that look good (red, orange, yellow, red, green, purple, black, white)
        # --> choose one randomly
        # --> set that palette in
        # --> adjust the bg color subtraction accordingly.

        # For now, let's just try randomly assigning the two palettes (range 0--239) and see what happens.
        import random
        ultima_palettes_addr = 0x1080D1
        space = Reserve(ultima_palettes_addr, ultima_palettes_addr+1, "Randomize Ultima Palettes")
        # Default values: 110, 113
        palette_choices = [
            [110, 113],  # blue (original)
            [163, 211],  # red   - [210, 211] cometty
            [223, 67],  # orange - 6 too red;  33 grey and orange;  [151, 75] is sparkly;  [128, 119] more muted
            [126, 55],  # yellow - 63 very white; 81 a little orange; 55;  165 black & gold; 185 has blue flecks;  [20, 55],
            [85, 49],    # green
            [179, 131],  # purple
            [94, 132],  # black/gray.  [88, 58] = black/yellow;  [155, 211] = black/red;
            [63, 54]  # white
        ]
        if False:
            new_palettes = random.choice(palette_choices)
        else:
            new_palettes = [random.randint(0, 239), random.randint(0, 239)]
        space.write(new_palettes)
        #print('Ultima palettes: ', new_palettes)

    def shuffle_mp(self):
        mp = []
        for spell in self.spells:
            mp.append(spell.mp)

        import random
        random.shuffle(mp)
        for spell in self.spells:
            spell.mp = mp.pop()

    def random_mp_value(self):
        import random
        for spell in self.spells:
            spell.mp = random.randint(self.args.magic_mp_random_value_min, self.args.magic_mp_random_value_max)

    def random_mp_percent(self):
        import random
        for spell in self.spells:
            mp_percent = random.randint(self.args.magic_mp_random_percent_min,
                                        self.args.magic_mp_random_percent_max) / 100.0
            value = int(spell.mp * mp_percent)
            spell.mp = max(min(value, 254), 0)

    def mod(self):
        if self.args.magic_mp_shuffle:
            self.shuffle_mp()
        elif self.args.magic_mp_random_value:
            self.random_mp_value()
        elif self.args.magic_mp_random_percent:
            self.random_mp_percent()

        # Apply No MP Scan after any MP shuffle/rando
        if self.args.scan_all:
            self.no_mp_scan()
        if self.args.warp_all:
            self.no_mp_warp()

        # Apply Ultima 254 MP after any MP shuffle/rando
        if self.args.ultima_254_mp:
            self.ultima_254_mp()

        # Randomize Ultima color
        if True:  # self.args.ultima_random_color:
            self.ultima_random_color()


    def write(self):
        if self.args.spoiler_log:
            self.log()
            
        for spell_index, spell in enumerate(self.spells):
            self.name_data[spell_index] = spell.name_data()
            self.ability_data[spell_index] = spell.ability_data()

        self.name_data.write()
        self.ability_data.write()

    def log(self):
        from log import section
        
        lcolumn = []
        for spell in self.spells:
            spell_name = spell.get_name()

            lcolumn.append(f"{spell_name:<{self.NAME_SIZE}} {spell.mp:>3} MP")
        
        section("Spells", lcolumn, [])

    def print(self):
        for spell in self.spells:
            spell.print()
