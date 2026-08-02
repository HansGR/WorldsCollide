from multiprocessing.sharedctypes import Value
from constants.commands import *
import random
import args

class Commands:
    def __init__(self, characters):
        self.characters = characters

    def mod_moogle_commands(self, command_list):
        from data.characters import Characters

        # Give the Moogles for Moogle Defense randomized commands
        # Copy the list minus any exclusions
        possible_moogle_commands = command_list.copy()
        # randomize commands for Moogles during Moogle Defense from the non-excluded set
        # Remove Morph to ensure only 1 character gets Morph
        # Remove Rage to avoid any issues with Randomized Atma weapon
        # Remove X-Magic as they won't have any Magic
        # Remove Blitz, SwdTech, Dance, and Lore because they won't have abilities within unless a party member does
        moogle_exclusions = [name_id["Morph"], name_id["Rage"], name_id["X Magic"], name_id["Blitz"], name_id["SwdTech"], name_id["Lore"], name_id["Dance"]]
        for exclude in moogle_exclusions:
            try:
                possible_moogle_commands.remove(exclude)
            except ValueError:
                pass
        if len(possible_moogle_commands) > 0:
            for index in range(Characters.FIRST_MOOGLE, Characters.LAST_MOOGLE + 1):
                self.characters[index].commands[1] = random.choice(possible_moogle_commands)

    def mod_commands(self):
        command_set = set(name_id[name] for name in RANDOM_POSSIBLE_COMMANDS)
        command_list = list(command_set)

        allowed_commands = command_set | set([name_id["Fight"], RANDOM_COMMAND, RANDOM_UNIQUE_COMMAND, NONE_COMMAND])

        # if morph was explicitly selected remove from available command list
        morph_id = name_id["Morph"]
        for command in args.character_commands:
            if command == morph_id:
                command_list.remove(morph_id)

        for exclude_command in args.random_exclude_commands:
            try:
                command_set.discard(exclude_command)
                command_list.remove(exclude_command)
            except ValueError:
                pass

        from data.characters import Characters
        self.mod_moogle_commands(command_list)

        # if suplex a train condition exists, guarantee blitz
        import objectives
        blitz_id = name_id["Blitz"]
        if objectives.suplex_train_condition_exists and blitz_id not in args.character_commands:
            # try to replace a random "Random" or "Random Unique" command with Blitz (even if blitz in excluded commands)
            possible_indices = []
            for index, command in enumerate(args.character_commands):
                if command == RANDOM_COMMAND or command == RANDOM_UNIQUE_COMMAND:
                    possible_indices.append(index)

            if not possible_indices:
                # suplex a train explicitly picked and all commands explicitly picked (but none are blitz)
                # force a random command to be blitz instead
                possible_indices = list(range(len(args.character_commands)))

            random_index = random.choice(possible_indices)
            args.character_commands[random_index] = blitz_id
            command_set.discard(blitz_id)

        for index, command in enumerate(args.character_commands):
            if command not in allowed_commands and (index != 0 or command != name_id["Morph"]) and (index != 12 or command != name_id["Leap"]):
                raise ValueError(f"Invalid character command {command}")
            elif command == RANDOM_COMMAND:
                args.character_commands[index] = random.choice(command_list)
                if args.character_commands[index] == morph_id:
                    command_list.remove(morph_id) # only one character gets morph
            elif command == NONE_COMMAND:
                args.character_commands[index] = name_id["None"]

            command_set.discard(args.character_commands[index])

        for index, command in enumerate(args.character_commands):
            if command == RANDOM_UNIQUE_COMMAND:
                args.character_commands[index] = random.choice(tuple(command_set))
                command_set.discard(args.character_commands[index])

        # apply the commands to the characters
        for index in range(len(args.character_commands[ : -2])):
            self.characters[index].commands[1] = args.character_commands[index]
        self.characters[Characters.GAU].commands[0] = args.character_commands[-2] # rage
        self.characters[Characters.GAU].commands[1] = args.character_commands[-1] # leap

    def full_random_characters(self):
        # the characters the -com flag controls: terra through mog, plus gau
        from data.characters import Characters
        return list(range(Characters.GAU + 1))

    def random_command_list(self):
        # commands available to random selection, minus the -rec exclusions
        command_list = [name_id[name] for name in RANDOM_POSSIBLE_COMMANDS]
        for exclude_command in args.random_exclude_commands:
            try:
                command_list.remove(exclude_command)
            except ValueError:
                pass
        return command_list

    def random_skills(self, characters, skill_counts, available):
        # fill each character's skill slots independently, commands may repeat between characters
        morph_id = name_id["Morph"]

        skills = {character : [] for character in characters}
        for character in characters:
            for _ in range(skill_counts[character]):
                # never give a character the same command twice
                candidates = [command for command in available if command not in skills[character]]
                if not candidates:
                    break

                command = random.choice(candidates)
                skills[character].append(command)
                if command == morph_id:
                    available.remove(morph_id) # only one character gets morph

        return skills

    def draft_skills(self, characters, skill_counts, available):
        # snake draft the skill slots so commands are unique for as long as they last,
        # refilling the available commands whenever they run out
        morph_id = name_id["Morph"]

        draft_order = list(characters)
        random.shuffle(draft_order)

        skills = {character : [] for character in characters}
        pool = list(available)
        for round_index in range(max(skill_counts.values(), default = 0)):
            round_order = [character for character in draft_order if skill_counts[character] > round_index]
            if round_index % 2:
                round_order.reverse() # snake back the other way every other round

            for character in round_order:
                # never give a character the same command twice
                candidates = [command for command in pool if command not in skills[character]]
                if not candidates:
                    # the pool ran out, or all that is left of it is already on this character.
                    # refill around whatever is left instead of replacing it, so a command which
                    # could not be handed out this turn is still waiting to be drafted later
                    pool.extend(available)
                    candidates = [command for command in pool if command not in skills[character]]
                    if not candidates:
                        continue

                command = random.choice(candidates)
                pool.remove(command)
                skills[character].append(command)
                if command == morph_id:
                    # only one character gets morph. dropping it from the available commands is
                    # enough to keep it out of the pool for good: a refill only happens once every
                    # pooled command is already on the drafting character, so morph can never be
                    # waiting in the pool at the moment a refill would add a second copy of it
                    available.remove(morph_id)

        return skills

    def guarantee_blitz(self, characters, skills):
        # if suplex a train condition exists, guarantee blitz
        import objectives
        blitz_id = name_id["Blitz"]

        if not objectives.suplex_train_condition_exists:
            return
        if any(blitz_id in skills[character] for character in characters):
            return

        # replace a random skill slot with blitz (even if blitz is in the excluded commands)
        possible_characters = [character for character in characters if skills[character]]
        if not possible_characters:
            return

        character = random.choice(possible_characters)
        skills[character][random.randrange(len(skills[character]))] = blitz_id

    def roll_common_commands(self, character):
        # roll the commands with a fixed menu position, in menu order
        from data.characters import Characters

        # gau has no fight command in vanilla, so halve his chance of getting one
        # to keep "gau doesn't always fight" true even at a 100% fight chance
        fight_range = 100 * (2 if character == Characters.GAU else 1)

        common = []
        if random.randrange(fight_range) < args.command_fight_percent:
            common.append(name_id["Fight"])
        if random.randrange(100) < args.command_magic_percent:
            common.append(name_id["Magic"])
        if random.randrange(100) < args.command_item_percent:
            common.append(name_id["Item"])
        return common

    def mod_full_random_commands(self):
        fight_id = name_id["Fight"]
        magic_id = name_id["Magic"]
        item_id = name_id["Item"]
        none_id = name_id["None"]

        available = self.random_command_list()
        self.mod_moogle_commands(available)

        characters = self.full_random_characters()

        common = {character : self.roll_common_commands(character) for character in characters}

        # every slot not taken by fight/magic/item is backfilled with a random skill
        skill_counts = {character : COMMAND_SLOT_COUNT - len(common[character]) for character in characters}

        if args.commands_random_mode == FULL_RANDOM_UNIQUE_MODE:
            skills = self.draft_skills(characters, skill_counts, available)
        else:
            skills = self.random_skills(characters, skill_counts, available)

        self.guarantee_blitz(characters, skills)

        # apply the commands to the characters in menu order: fight -> skills -> magic -> item
        for character in characters:
            commands = []
            if fight_id in common[character]:
                commands.append(fight_id)
            commands.extend(skills[character])
            if magic_id in common[character]:
                commands.append(magic_id)
            if item_id in common[character]:
                commands.append(item_id)
            commands.extend([none_id] * (COMMAND_SLOT_COUNT - len(commands)))

            self.characters[character].commands = commands

    def shuffle_full_random_commands(self):
        # commands are already random, so shuffle whole command sets between characters
        # instead of single slots to keep each character's menu order intact
        characters = self.full_random_characters()

        command_sets = [self.characters[character].commands for character in characters]
        random.shuffle(command_sets)

        for index, character in enumerate(characters):
            self.characters[character].commands = command_sets[index]

    def shuffle_commands(self):
        from data.characters import Characters

        commands = []
        for index in range(len(COMMAND_OPTIONS) - 1):
            commands.append(self.characters[index].commands[1])
        commands.append(self.characters[Characters.GAU].commands[0]) # rage

        random.shuffle(commands)

        for index in range(len(COMMAND_OPTIONS) - 1):
            self.characters[index].commands[1] = commands[index]
        self.characters[Characters.GAU].commands[0] = commands[-1] # rage

    def mod(self):
        import data.characters_asm as characters_asm
        from data.characters import Characters

        if args.commands:
            if args.commands_random_mode:
                self.mod_full_random_commands()
            else:
                self.mod_commands()
        if args.shuffle_commands:
            if args.commands_random_mode:
                self.shuffle_full_random_commands()
            else:
                self.shuffle_commands()

        if args.commands or args.shuffle_commands:
            characters_asm.update_morph_character(self.characters[ : Characters.CHARACTER_COUNT])

    def log(self):
        from log import section, format_option
        from data.characters import Characters

        if args.commands_random_mode:
            # every slot is randomized, so log each character's full command menu
            lcolumn = []
            for character in self.full_random_characters():
                commands = [id_name[command] for command in self.characters[character].commands
                            if command != name_id["None"]]
                lcolumn.append(format_option(Characters.DEFAULT_NAME[character].capitalize(), ", ".join(commands)))

            section("Commands", lcolumn, [])
            return

        lcolumn = []
        for index, option in enumerate(COMMAND_OPTIONS[ : -2]):
            lcolumn.append(format_option(option, id_name[self.characters[index].commands[1]]))
        lcolumn.append(format_option(COMMAND_OPTIONS[-2], id_name[self.characters[Characters.GAU].commands[0]]))
        lcolumn.append(format_option(COMMAND_OPTIONS[-1], id_name[self.characters[Characters.GAU].commands[1]]))

        section("Commands", lcolumn, [])
