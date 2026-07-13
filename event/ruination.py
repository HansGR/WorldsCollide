"""Ruination mode: event-side machinery.

The map/reward *generator* that used to live here (RuinationBranch,
ruination_map, ~5,700 lines) was replaced by the v2 planner
(doors/plan/ruination/, planned in the Data phase; Events binds the plan
via event/ruination_bind.py) and deleted in the Stage E2 cutover. What
remains is the event-side half: the start-game script, party interaction
scripts, the y-party-switch subroutines, chocobo stable disabling, and
the ferry network.
"""
from event.event import *
from data.characters import Characters
import random

ESPER_GATE_MAPID = 0x0da


def ruination_start_game_mod(dialogs, party):
    # Write the event that starts the game in ruination mode

    # Dialog IDs $0590/$0591 sit in the vanilla Maduin/Madonna esper-world
    # conversation block, which never plays in ruination mode. See ARCHIVE.md
    # "Ruination Mode — Dialog ID Reservations" for the complete map.
    ruination_start_1 = 0x0590
    if party >= 2:
        dialogs.set_text(ruination_start_1, "After Kefka broke the world, we woke up here.<wait 60 frames><end>")
    else:
        dialogs.set_text(ruination_start_1, "After Kefka broke the world, I woke up here.<wait 60 frames><end>")
    ruination_start_2 = 0x0591
    dialogs.set_text(ruination_start_2, "This new world is dark and full of monsters.<wait 30 frames> Let's find our friends and bring hope to the darkness.<end>")

    src = [
        field.LoadMap(ESPER_GATE_MAPID, direction.DOWN, default_music=False,
                        x=55, y=33, entrance_event=True),
    ]

    # Only create/position/show entities for party slots that have actual characters.
    # Operating on empty party slots can alias to wrong characters due to stale data.
    if party >= 2:
        src += [field.CreateEntity(field_entity.PARTY1)]
    if party >= 3:
        src += [field.CreateEntity(field_entity.PARTY2)]
    if party >= 4:
        src += [field.CreateEntity(field_entity.PARTY3)]

    src += [
        field.EntityAct(field_entity.PARTY0, True,
                        field_entity.SetPosition(54, 31),
                        field_entity.AnimateKnockedOut(),
                        field_entity.SetSpriteLayer(2),
                        field_entity.SetSpeed(field_entity.Speed.NORMAL),
                        ),
    ]
    if party >= 2:
        src += [
            field.EntityAct(field_entity.PARTY1, True,
                            field_entity.SetPosition(56, 32),
                            field_entity.AnimateKnockedOut(),
                            field_entity.SetSpeed(field_entity.Speed.NORMAL),
                            ),
        ]
    if party >= 3:
        src += [
            field.EntityAct(field_entity.PARTY2, True,
                            field_entity.SetPosition(53, 33),
                            field_entity.AnimateKnockedOut(),
                            field_entity.SetSpeed(field_entity.Speed.NORMAL),
                            ),
        ]
    if party >= 4:
        src += [
            field.EntityAct(field_entity.PARTY3, True,
                            field_entity.SetPosition(55, 35),
                            field_entity.AnimateKnockedOut(),
                            field_entity.SetSpeed(field_entity.Speed.NORMAL),
                            ),
        ]

    src += [field.ShowEntity(field_entity.PARTY0)]
    if party >= 2:
        src += [field.ShowEntity(field_entity.PARTY1)]
    if party >= 3:
        src += [field.ShowEntity(field_entity.PARTY2)]
    if party >= 4:
        src += [field.ShowEntity(field_entity.PARTY3)]

    src += [
        field.RefreshEntities(),
        field.Dialog(ruination_start_1, wait_for_input=False, inside_text_box=False, top_of_screen=False),
        field.HoldScreen(),
        field.FadeInScreen(speed=8),
        field.EntityAct(field_entity.PARTY0, True,
                        field_entity.Pause(60),
                        field_entity.AnimateKneeling(),
                        field_entity.Pause(20),
                        field_entity.AnimateStandingHeadDown(),
                        field_entity.Pause(10),
                        # Shaking head (see e.g. CA/FCC6)
                        field_entity.AnimateTiltHeadLeft(),
                        field_entity.Pause(8),
                        field_entity.AnimateTiltHeadRight(),
                        field_entity.Pause(15),
                        #field_entity.AnimateTiltHeadLeft(),
                        #field_entity.Pause(8),
                        #field_entity.AnimateTiltHeadRight(),
                        #field_entity.Pause(8),
                        ),
        field.Dialog(ruination_start_2, wait_for_input=False, inside_text_box=False, top_of_screen=False),
    ]
    # Animate party assembling, based on number of characters
    if party == 1:
        # Just animate main character
        src += [
            field.EntityAct(field_entity.PARTY0, True,
                            field_entity.Move(direction.DOWN, 1),
                            field_entity.Move(direction.RIGHT, 1),
                            field_entity.AnimateStandingFront(),
                            field_entity.Pause(2),
                            field_entity.AnimateCloseEyes(),
                            field_entity.Pause(2),
                            field_entity.AnimateStandingFront(),
                            field_entity.Pause(2),
                            field_entity.AnimateCloseEyes(),
                            field_entity.Pause(2),
                            field_entity.AnimateStandingFront(),
                            ),
        ]
    elif party == 2:
        # Animate character 1 picking up character 2
        src += [
            field.EntityAct(field_entity.PARTY0, True,
                            field_entity.Move(direction.DOWN, 1),
                            field_entity.Move(direction.RIGHT, 1),
                            field_entity.AnimateKneelingRight(),
                            ),
            field.EntityAct(field_entity.PARTY0, False,
                            field_entity.Pause(4),
                            field_entity.Turn(direction.RIGHT),
                            field_entity.AnimateAttackRight(),
                            field_entity.Pause(4),
                            field_entity.Turn(direction.DOWN),
                            ),
            field.EntityAct(field_entity.PARTY1, True,
                            field_entity.AnimateKneeling(),
                            field_entity.Pause(8),
                            field_entity.Turn(direction.LEFT),
                            field_entity.AnimateHandsUp(),
                            field_entity.AnimateAttack(),
                            field_entity.Pause(4),
                            field_entity.Move(direction.DOWN, 1),
                            field_entity.Turn(direction.LEFT)
                            ),
            field.DisableEntityCollision(field_entity.PARTY1),
            field.EntityAct(field_entity.PARTY0, False,
                            field_entity.AnimateStandingHeadDown(),
                            field_entity.Pause(4),
                            field_entity.AnimateStandingFront(),
                            field_entity.Pause(4),
                            field_entity.Move(direction.DOWN, 1),
                            ),
            field.EntityAct(field_entity.PARTY1, True,
                            field_entity.AnimateFaceLeftHeadDown(),
                            field_entity.Pause(4),
                            field_entity.Turn(direction.LEFT),
                            field_entity.Pause(4),
                            field_entity.Move(direction.LEFT, 1),
                            field_entity.Hide(),
                            ),

        ]
    elif party == 3:
        # Animate character 1 waking up character 2, picking up character 3
        src += [
            field.EntityAct(field_entity.PARTY0, True,
                            field_entity.Move(direction.DOWN, 1),
                            field_entity.Move(direction.RIGHT, 1),
                            field_entity.AnimateKneelingRight(),
                            ),
            field.EntityAct(field_entity.PARTY0, False,
                            field_entity.Pause(4),
                            field_entity.Move(direction.DOWN, 1),
                            field_entity.Move(direction.LEFT, 1),
                            field_entity.AnimateKneeling(),
                            field_entity.Pause(4),
                            field_entity.Turn(direction.LEFT),
                            field_entity.AnimateAttack(),
                            field_entity.Pause(4),
                            field_entity.Move(direction.RIGHT, 1),
                            field_entity.Move(direction.UP, 1),
                            field_entity.Turn(direction.DOWN),
                            ),
            field.EntityAct(field_entity.PARTY1, False,
                            field_entity.AnimateKneeling(),
                            field_entity.Pause(8),
                            field_entity.Turn(direction.LEFT),
                            field_entity.AnimateHandsUp(),
                            field_entity.Pause(1),
                            field_entity.AnimateAttack(),
                            field_entity.Pause(16),
                            field_entity.Move(direction.DOWN, 1),
                            field_entity.Turn(direction.LEFT)
                            ),
            field.EntityAct(field_entity.PARTY2, True,
                            field_entity.Pause(16),
                            field_entity.AnimateKneeling(),
                            field_entity.Pause(4),
                            field_entity.AnimateStandingHeadDown(),
                            field_entity.Pause(4),
                            field_entity.AnimateTiltHeadLeft(),
                            field_entity.Pause(1),
                            field_entity.AnimateTiltHeadRight(),
                            field_entity.Pause(1),
                            field_entity.AnimateTiltHeadLeft(),
                            field_entity.Pause(1),
                            field_entity.AnimateTiltHeadRight(),
                            field_entity.Pause(1),
                            field_entity.AnimateTiltHeadLeft(),
                            field_entity.Pause(1),
                            field_entity.AnimateTiltHeadRight(),
                            field_entity.Pause(4),
                            field_entity.Move(direction.RIGHT, 1),
                            ),
            field.DisableEntityCollision(field_entity.PARTY1),
            field.DisableEntityCollision(field_entity.PARTY2),
            field.EntityAct(field_entity.PARTY0, False,
                            field_entity.AnimateStandingHeadDown(),
                            field_entity.Pause(4),
                            field_entity.AnimateStandingFront(),
                            field_entity.Pause(4),
                            field_entity.Move(direction.DOWN, 1),
                            ),
            field.EntityAct(field_entity.PARTY1, False,
                            field_entity.AnimateFaceLeftHeadDown(),
                            field_entity.Pause(4),
                            field_entity.Turn(direction.LEFT),
                            field_entity.Pause(4),
                            field_entity.Move(direction.LEFT, 1),
                            field_entity.Hide(),
                            ),
            field.EntityAct(field_entity.PARTY2, True,
                            field_entity.AnimateFaceRightHeadDown(),
                            field_entity.Pause(4),
                            field_entity.Turn(direction.RIGHT),
                            field_entity.Pause(4),
                            field_entity.Move(direction.RIGHT, 1),
                            field_entity.Hide(),
                            ),

        ]
    elif party == 4:
        # Animate character 1 waking up character 2, picking up character 3;  character 4 wakes themselves up.
        src += [
            field.EntityAct(field_entity.PARTY0, True,
                            field_entity.Move(direction.DOWN, 1),
                            field_entity.Move(direction.RIGHT, 1),
                            field_entity.AnimateKneelingRight(),
                            ),
            field.EntityAct(field_entity.PARTY0, False,
                            field_entity.Pause(4),
                            field_entity.Move(direction.DOWN, 1),
                            field_entity.Move(direction.LEFT, 1),
                            field_entity.AnimateKneeling(),
                            field_entity.Pause(4),
                            field_entity.Turn(direction.LEFT),
                            field_entity.AnimateAttack(),
                            field_entity.Pause(4),
                            field_entity.Move(direction.RIGHT, 1),
                            field_entity.Move(direction.UP, 1),
                            field_entity.Turn(direction.DOWN),
                            ),
            field.EntityAct(field_entity.PARTY1, False,
                            field_entity.AnimateKneeling(),
                            field_entity.Pause(8),
                            field_entity.Turn(direction.LEFT),
                            field_entity.AnimateHandsUp(),
                            field_entity.Pause(1),
                            field_entity.AnimateAttack(),
                            field_entity.Pause(16),
                            field_entity.Move(direction.DOWN, 1),
                            field_entity.Turn(direction.LEFT)
                            ),
            field.EntityAct(field_entity.PARTY2, False,
                            field_entity.Pause(16),
                            field_entity.AnimateKneeling(),
                            field_entity.Pause(4),
                            field_entity.AnimateStandingHeadDown(),
                            field_entity.Pause(4),
                            field_entity.AnimateTiltHeadLeft(),
                            field_entity.Pause(1),
                            field_entity.AnimateTiltHeadRight(),
                            field_entity.Pause(1),
                            field_entity.AnimateTiltHeadLeft(),
                            field_entity.Pause(1),
                            field_entity.AnimateTiltHeadRight(),
                            field_entity.Pause(1),
                            field_entity.AnimateTiltHeadLeft(),
                            field_entity.Pause(1),
                            field_entity.AnimateTiltHeadRight(),
                            field_entity.Pause(4),
                            field_entity.Move(direction.RIGHT, 1),
                            ),
            field.EntityAct(field_entity.PARTY3, True,
                            field_entity.Pause(20),
                            field_entity.AnimateSurprised(),
                            field_entity.Pause(1),
                            field_entity.AnimateKneeling(),
                            field_entity.Pause(2),
                            field_entity.AnimateFrontRightHandUp(),
                            field_entity.Pause(4),
                            field_entity.AnimateFrontRightHandWaving(),
                            field_entity.Pause(4),
                            field_entity.Move(direction.UP, 1),
                            ),
            field.WaitForEntityAct(field_entity.PARTY2),
            field.DisableEntityCollision(field_entity.PARTY0),
            field.DisableEntityCollision(field_entity.PARTY1),
            field.DisableEntityCollision(field_entity.PARTY2),
            field.DisableEntityCollision(field_entity.PARTY3),
            field.EntityAct(field_entity.PARTY0, False,
                            field_entity.AnimateStandingHeadDown(),
                            field_entity.Pause(4),
                            field_entity.AnimateStandingFront(),
                            field_entity.Pause(4),
                            field_entity.Move(direction.DOWN, 1),
                            ),
            field.EntityAct(field_entity.PARTY1, False,
                            field_entity.AnimateFaceLeftHeadDown(),
                            field_entity.Pause(4),
                            field_entity.Turn(direction.LEFT),
                            field_entity.Pause(4),
                            field_entity.Move(direction.LEFT, 1),
                            field_entity.Hide(),
                            ),
            field.EntityAct(field_entity.PARTY2, False,
                            field_entity.AnimateFaceRightHeadDown(),
                            field_entity.Pause(4),
                            field_entity.Turn(direction.RIGHT),
                            field_entity.Pause(4),
                            field_entity.Move(direction.RIGHT, 1),
                            field_entity.Hide(),
                            ),
            field.EntityAct(field_entity.PARTY3, True,
                            field_entity.Turn(direction.UP),
                            field_entity.Pause(8),
                            field_entity.Move(direction.UP, 1),
                            field_entity.Hide(),
                            ),
            field.EnableEntityCollision(field_entity.PARTY0),

        ]

    # Only hide party entities that were actually created
    if party >= 2:
        src += [field.HideEntity(field_entity.PARTY1)]
    if party >= 3:
        src += [field.HideEntity(field_entity.PARTY2)]
    if party >= 4:
        src += [field.HideEntity(field_entity.PARTY3)]

    src += [
        field.EntityAct(field_entity.PARTY0, True,
                        field_entity.SetSpriteLayer(0),
                        ),

        field.RefreshEntities(),
        field.FreeScreen(),
        field.Return(),
    ]
    space = Write(Bank.CC, src, "start game ruination")
    return space.start_address


# --- Party Interaction Scripts (talking to inactive party leaders) ---

# Dialog IDs for character airship quotes (vanilla WoR airship dialog).
# Order matches character IDs 0-13: Terra, Locke, Cyan, Shadow, Edgar, Sabin,
# Celes, Strago, Relm, Setzer, Mog, Gau, Gogo, Umaro.
CHARACTER_AIRSHIP_DIALOG_IDS = [
    0x0B94, 0x0B95, 0x0B96, 0x0B97,  # Terra, Locke, Cyan, Shadow
    0x0B98, 0x0B99, 0x0B9A, 0x0B9B,  # Edgar, Sabin, Celes, Strago
    0x0B9C, 0x0B9D, 0x068B, 0x068D,  # Relm, Setzer, Mog, Gau
    0x068F, 0x0690,                    # Gogo, Umaro
]

# Per-character dialog choices for party interaction. One is randomly selected
# on each compile and written over the vanilla airship quote dialog slot.
# Sourced from memorable vanilla FF6 dialog lines for each character.
from constants.entities import (
    TERRA, LOCKE, CYAN, SHADOW, EDGAR, SABIN, CELES, STRAGO, RELM, SETZER,
    MOG, GAU, GOGO, UMARO,
)
CHARACTER_DIALOG_CHOICES = {
    TERRA: [
        # introspective, searching for meaning/love, determined
        "General Leo...<line>I believe I understand what you were trying to say.<end>",  # edited
        "I know what love is...!<end>",
        #"I'll do it!<end>",
        "People only seem to want power.<line>Do they really want to be like me?<end>",
        #"I'm hardly...normal...<end>",
        #"I can do it...<line>But why do I feel so wretched?<end>",
        "I'm all right.<line>I'm sure peace is within our grasp!<end>",
        "We must fight for those who aren't even born yet!<end>",  # Now I must go to war.<line>
        #"I want to know what love is...<line>now!<end>",
        "I can fight!<end>",
        #"Come with me!<end>",
        #"Everyone's calling me.<end>",
    ],
    LOCKE: [
        # treasure hunter, protective, devoted
        "I PREFER the term treasure hunting!<end>",
        #"That's TREASURE HUNTER!<end>",
        "I'll protect you!<end>",
        "Trust me! You'll be fine!<end>",
        "As long as there're people who need to be protected, I'll fight!<end>",
        "I have learned to celebrate life... and the living.<end>",  # <line>
        "Let's go!<line>We have work to do!!<end>",
        #"We haven't a second to lose!<end>",
        #"I promised I'd protect her.<line>I WILL NOT back out on my word.<end>",
    ],
    CYAN: [
        # honorable samurai, formal speech
        #"What an amazing device!<end>",
        "Thou musn't give up the fight!<end>",
        #"I am <CYAN>,<line>retainer to the King of Doma.<line>I am your worst nightmare...<end>",
        "My family lives on inside of me.<end>",
        "I will avenge the people of Doma!!<end>",
        "I shall go with you!<end>",
    ],
    SHADOW: [
        # mysterious loner, terse
        "...<end>",
        "The Reaper is always just a step behind me...<end>",
        #"Leave 'em alone.<end>",
        "We meet again...<end>",
        "I know what friendship is...<line>and family...<end>",
        #"Go! There are people counting on you!<end>",
        "I can't help you.<line>You must look within for answers.<end>",
    ],
    EDGAR: [
        # charming king, flirtatious, witty
        "If something happens to me, all the world's women will grieve!<end>",  # <line>
        "It is my dream to build a kingdom in which I can guarantee freedom, and dignity.<end>", # <line>
        #"First of all, your beauty<line>has captivated me!<end>",
        #"Guess my technique's getting a bit rusty...<end>",
        #"He'd slit his mama's throat for a nickel!<end>",
        "It's time to break into Kefka's domain!<end>",
        "I finally think we're gonna pull this off!<end>",
        #"Bravo, Figaro!!!<end>",
        "You can't keep track of 'em all!<end>",
    ],
    SABIN: [
        # strong, earnest, bear-like
        "Think a 'bear' like me could help you in your fight?<end>",
        "Riiiiiight!<end>",
        "Let me have at it!<end>",
        #"Then let's just bust through!<end>",
        "Master Duncan's techniques mustn't fail me.<end>",
        "You think the end of the world was gonna do me in?<end>", # <line>
        "Now I know why I have these stupid muscles!<end>",
        "I have come to experience anew the love of my brother!<end>", # <line>
        "Can't wage war on an empty stomach!<end>",
        "...smash Kefka, and deliver peace unto the world! All right, count me in!<end>",
    ],
    CELES: [
        # former general, strong-willed, emotional depth
        "I'm a soldier, not some love-starved twit!<end>",
        "I'm free...<line>The Empire can't control me!<end>",
        "I've met someone who can accept me<line>for what I am.<end>",
        "I'm glad I made it this far... I feel I have a lot to live for...<end>", # <line>
        #"I think you've been hustled,<line>Mr. Gambler.<end>",
        "I'm a GENERAL, not some opera floozy!<end>",
        "Come on, everybody!<line>We have to work together!<end>",
        #"He's alive...<line><LOCKE>'s still alive!!!<end>",
        "I'll make you proud of me, Granddad...<end>",
    ],
    STRAGO: [
        # old sage, grandfather figure
        #"I have a special little Granddaughter!<end>",
        "Hey everyone! Let me see the light in your eyes! The old man, here, hasn't given up yet!<end>", # <line> #<line>
        "I wanted to show my enemy the true meaning of the word, 'hero'!<end>",  # <line>
        "Fool! I may be old,<line>but I'm not powerless!<end>",
        #"I owe you for saving <RELM>.<line>I'll help you find your Espers.<end>",
        "In all my travels,<line>and in all my years...<end>",
    ],
    RELM: [
        # sassy young painter
        "Let's do it!<line>Let's go get that madman!<end>",
        #"And I have a brave Grandpa who'll<line>stand by me through it all.<end>",
        "Who is this puffed up aerobics instructor, anyway?<end>", #<line>
        "Did you think I was gonna check out<line>before you, old man?!<end>",
        "Hey! Did you see me? I was awesome!<end>",
        "I'm coming along, too.<end>",
        "What a fuddy duddy...<end>",
        "Aaack! I'm gonna paint your portrait!<end>",
    ],
    SETZER: [
        # gambler, risk-taker, romantic
        "My life is a chip in your pile.<line>Ante up!<end>",
        "My friend's airship...<line>and her love!<end>",
        "Something good will come of it all!<end>",
        "Nothing to lose but my life...<end>",
        "When things fall, they fall!<line>It's all a matter of fate...<end>",
        #"There's nothing like flying!<end>",
        "I'm starting to feel lucky!!<end>",
        "Sometimes in life you just have to<line>FEEL your way through a situation!<end>",
    ],
    MOG: [
        # cute moogle
        "Kupoppo!!<end>",
        "I'm your boss, kupo!<line>You're gonna join us, kupo!!!<end>",
        "Kupo!<end>",
        #"I have my friends here!<end>",
    ],
    GAU: [
        # wild boy, broken speech, heartfelt
        "You my friends!<line>Me uwaooo all of you!<end>",
        "<GAU>...<line><GAU> do his best!<end>",
        "<GAU> hit hard!!!<end>",
        #"<GAU> become stronger on the Veldt.<end>",
        "Fffatherrr...alive...<line>H...a...p...p...y...<end>",
        "<GAU> find short cut!<end>",
        "Awoooo...!<end>",
    ],
    GOGO: [
        # mysterious mimic
        "This should be fun.<line>When do we leave?<end>",
        "You seek to save the world? Then I guess that means I shall save the world as well.<end>",
        "Lead on! I will copy your every move.<end>",
        #"I have been idle for too many years... Perhaps I ought to mimic you.<end>",
        "...<end>",
    ],
    UMARO: [
        # barely speaks
        "Uhhhh...<end>",
        "Oooh...<end>",
        "Ughaaa!<end>",
    ],
}

# Repurpose vanilla "Change party members?" dialog (0x0528 = 1320) for the choice menu.
PARTY_INTERACT_CHOICE_DIALOG = 1320

# Maps character ID -> ROM address of that character's party interaction event script.
# Populated by create_party_interaction_scripts(); read by RecruitAndSelectParty and
# NarsheWob/Start to emit ChangeNPCEventAddress instructions.
PARTY_INTERACTION_SCRIPT_ADDRS = {}

# ROM address of the shared "set all party interaction NPC pointers" subroutine.
# Populated by create_party_interaction_scripts() (runs before the event mod loop).
# Callers import this lazily (inside a method) and invoke it via field.Call, or
# assign it as a map's entrance_event_address (after subtracting EVENT_CODE_START).
SET_PARTY_INTERACTION_POINTERS = None


def create_party_interaction_scripts(dialogs):
    """Create per-character event scripts for party interaction in ruination mode.

    When the player talks to an inactive party's leader, the script:
      1. Shows the leader's airship quote dialog
      2. Offers a 3-option choice: Join forces / Swap members / Do nothing
      3. Runs the appropriate party formation sequence

    Also creates a shared finishing subroutine used by all 14 scripts.

    Args:
        dialogs: The Dialogs object for setting dialog text.
    """
    from instruction.field.functions import (
        REFRESH_CHARACTERS_AND_SELECT_PARTY,
        REFRESH_CHARACTERS_AND_SELECT_TWO_PARTIES,
    )
    from constants.entities import CHARACTER_COUNT

    # Set the choice dialog text.
    dialogs.set_text(PARTY_INTERACT_CHOICE_DIALOG,
                     "<choice> Join forces<line>"
                     "<choice> Swap members<line>"
                     "<choice> Do nothing<end>")

    # Shared finishing subroutine: called (via Branch) after SelectParties returns.
    finish_src = [
        field.FinalizeBranchRecruit(),
        field.RefreshEntities(),
        field.UpdatePartyLeader(),
        field.FadeInScreen(),
        field.WaitForFade(),
        field.FreeMovement(),
        field.Return(),
    ]
    space = Write(Bank.CA, finish_src, "party interact finish subroutine")
    finish_addr = space.start_address

    # Randomly select and write a dialog line for each character.
    for char_id in range(CHARACTER_COUNT):
        choices = CHARACTER_DIALOG_CHOICES.get(char_id)
        if choices:
            dialog_id = CHARACTER_AIRSHIP_DIALOG_IDS[char_id]
            char_name = Characters.DEFAULT_NAME[char_id]
            dialogs.set_text(dialog_id, f"<{char_name}>: {random.choice(choices)}")

    # Create one event script per character.
    for char_id in range(CHARACTER_COUNT):
        char_dialog = CHARACTER_AIRSHIP_DIALOG_IDS[char_id]
        join_arg = char_id | 0x10   # 0b0001cccc: include party, merge into 1
        swap_arg = char_id | 0x30   # 0b0011cccc: include party, 2-party swap

        src = [
            field.Dialog(char_dialog),
            field.DialogBranch(PARTY_INTERACT_CHOICE_DIALOG,
                               dest1="JOIN", dest2="SWAP", dest3=field.RETURN),

            "JOIN",
            field.SetupBranchRecruit(join_arg),
            field.Call(REFRESH_CHARACTERS_AND_SELECT_PARTY),
            field.Branch(finish_addr),

            "SWAP",
            field.SetupBranchRecruit(swap_arg),
            field.Call(REFRESH_CHARACTERS_AND_SELECT_TWO_PARTIES),
            field.Branch(finish_addr),
        ]
        space = Write(Bank.CA, src, f"party interact script char {char_id}")
        PARTY_INTERACTION_SCRIPT_ADDRS[char_id] = space.start_address

    # Free the vanilla airship event scripts that we replaced.
    # CA/3F13-CA/3F82 (112 bytes, 8 per character).
    Free(0xa3f13, 0xa3f82)

    # Write the shared subroutine that repoints every recruited character's
    # NPC talk event to its party-interaction script. Runs after the per-character
    # scripts above so PARTY_INTERACTION_SCRIPT_ADDRS is fully populated. Must
    # happen before the event.mod() loop so callers (NarsheWob, EsperWorld)
    # can read SET_PARTY_INTERACTION_POINTERS.
    _write_set_party_interaction_pointers_subroutine()


def _write_set_party_interaction_pointers_subroutine():
    """Write the 'set all party interaction NPC pointers' subroutine to Bank.CA once.

    For each of the 14 characters, emits:
        if character_recruited(c): ChangeNPCEventAddress(c, PARTY_INTERACTION_SCRIPT_ADDRS[c])
    followed by a Return so the subroutine can be invoked via field.Call or used
    as a map entrance_event. Stores the full SNES address in the module-level
    SET_PARTY_INTERACTION_POINTERS.
    """
    from constants.entities import CHARACTER_COUNT
    global SET_PARTY_INTERACTION_POINTERS

    src = []
    for char_id in range(CHARACTER_COUNT):
        addr = PARTY_INTERACTION_SCRIPT_ADDRS[char_id]
        src += [
            field.BranchIfEventBitClear(event_bit.character_recruited(char_id), f"SKIP_{char_id}"),
            field.ChangeNPCEventAddress(char_id, addr),
            f"SKIP_{char_id}",
        ]
    src.append(field.Return())
    space = Write(Bank.CA, src, "set party interaction pointers subroutine")
    SET_PARTY_INTERACTION_POINTERS = space.start_address


# ROM addresses of the shared y-party-switch save/disable and restore subroutines.
# Populated by create_y_party_switch_subroutines() (runs before the event mod loop).
# Callers import these lazily (inside a method) and invoke them via field.Call, or
# assign one as a map event's event_address (after subtracting EVENT_CODE_START).
DISABLE_Y_PARTY_SWITCH = None
RESTORE_Y_PARTY_SWITCH = None


def create_y_party_switch_subroutines():
    """Write the shared y-party-switch save/disable and restore subroutines once.

    Several ruination-mode events (doma wob, fanatics tower, floating continent,
    narshe moogle defense) make dynamic map edits that break if the player presses
    "y" to switch parties mid-event. Each disables y-party switching when its scene
    begins and restores it at the end, remembering whether it was on in the
    SAVED_Y_PARTY_SWITCHING event bit. The scenes never overlap, so one pair of
    subroutines (and one save bit) serves all of them.

    Stores the SNES addresses in the module-level DISABLE_Y_PARTY_SWITCH /
    RESTORE_Y_PARTY_SWITCH. Each ends in Return so it can be invoked via field.Call
    or used as a map event's event_address (after subtracting EVENT_CODE_START).
    """
    global DISABLE_Y_PARTY_SWITCH, RESTORE_Y_PARTY_SWITCH

    # Save ENABLE_Y_PARTY_SWITCHING to SAVED_Y_PARTY_SWITCHING, then clear it.
    src = [
        field.BranchIfEventBitSet(event_bit.ENABLE_Y_PARTY_SWITCHING, "Y_WAS_ON"),
        field.ClearEventBit(event_bit.SAVED_Y_PARTY_SWITCHING),
        field.Branch("DONE"),
        "Y_WAS_ON",
        field.SetEventBit(event_bit.SAVED_Y_PARTY_SWITCHING),
        "DONE",
        field.ClearEventBit(event_bit.ENABLE_Y_PARTY_SWITCHING),
        field.Return(),
    ]
    space = Write(Bank.CB, src, "save and disable y-party switching")
    DISABLE_Y_PARTY_SWITCH = space.start_address

    # Restore ENABLE_Y_PARTY_SWITCHING from SAVED_Y_PARTY_SWITCHING.
    src = [
        field.BranchIfEventBitSet(event_bit.SAVED_Y_PARTY_SWITCHING, "Y_WAS_ON"),
        field.ClearEventBit(event_bit.ENABLE_Y_PARTY_SWITCHING),
        field.Branch("DONE"),
        "Y_WAS_ON",
        field.SetEventBit(event_bit.ENABLE_Y_PARTY_SWITCHING),
        "DONE",
        field.ClearEventBit(event_bit.SAVED_Y_PARTY_SWITCHING),
        field.Return(),
    ]
    space = Write(Bank.CB, src, "restore y-party switching")
    RESTORE_Y_PARTY_SWITCH = space.start_address


def disable_chocobo_stables(rom, dialogs, args):
    """
    Disables the in-town chocobo stables for ruination mode.
    Changes the chocobo keeper dialogs to explain chocobos won't go outside,
    and patches the event code to just display the dialog and return (no choices).

    Args:
        rom: The ROM object to modify
        dialogs: The Dialogs object to update dialog text
        args: Command line arguments (for debug flag)
    """
    # Chocobo stable event addresses and their dialog IDs
    # Format: (event_address, dialog_id, description)
    chocobo_stables = [
        (0xa7a36, 0x0B8E, "South Figaro chocobo"),
        (0xa8fb4, 0x0B8E, "Nikeah chocobo"),  # Shares dialog with South Figaro
        (0xb44cd, 0x0113, "Jidoor chocobo"),
    ]

    disabled_message = "The chocobos won't go outside anymore.<end>"

    # Track which dialogs we've already updated
    updated_dialogs = set()

    for event_addr, dialog_id, description in chocobo_stables:
        # Update dialog text (only once per unique dialog ID)
        if dialog_id not in updated_dialogs:
            dialogs.set_text(dialog_id, disabled_message)
            updated_dialogs.add(dialog_id)

            if args.debug:
                print(f"Updated dialog {dialog_id:#x} for {description}")

        # Patch event code to: display dialog (4B), return (FE)
        # Format: 4B [dialog_id_lo] [dialog_id_hi] FE
        event_bytes = bytes([0x4B, dialog_id & 0xFF, dialog_id >> 8, 0xFE])
        rom.set_bytes(event_addr, event_bytes)

        if args.debug:
            print(f"Disabled {description} at {event_addr:#x}")


# Ferry-port descriptors used by fix_ferry_connections.
#   npc_event_addr  - the field-event slot the NPC's talk script enters at.
#   dest_map / dest_spawn / dest_dir - where the player materialises after travel.
#   wor_dock        - the airship-park tile on the WoR overworld for the boat anim.
# Albrook adds a few extra fields because we promote a generic NPC into a sailor:
#   sailor_map / sailor_npc_id - which NPC slot we promote
#   sailor_npc_bit             - the visibility bit that must be ON for the NPC
#   sailor_sprite              - sprite to assign (54 = sailor)
FERRY_PORTS = {
    'SouthFigaro': {
        'display':        'South Figaro',
        'npc_event_addr': 0xa77d7,
        'dest_map':       0x5b,  'dest_spawn': (12, 11), 'dest_dir': direction.LEFT,
        'wor_dock':       (113, 96),
    },
    'Nikeah': {
        'display':        'Nikeah',
        'npc_event_addr': 0xa8cbb,
        'dest_map':       0xbb,  'dest_spawn': (24, 11), 'dest_dir': direction.DOWN,
        'wor_dock':       (147, 77),
    },
    'Albrook': {
        'display':        'Albrook',
        'npc_event_addr': 0xbd1f3,
        'dest_map':       0x14c, 'dest_spawn': (28, 7),  'dest_dir': direction.LEFT,
        'wor_dock':       (141, 210),
        'sailor_map':     0x14c, 'sailor_npc_id': 0x22,
        'sailor_npc_bit': 0x565, 'sailor_sprite': 54,
    },
}

# Each port's NPC has a single owned dialog ID; we rewrite its text to whatever
# prompt makes sense (1-destination "X-bound ferry" or 2-destination "Where to?").
FERRY_PROMPT_DIALOG = {
    'SouthFigaro': 812,    # vanilla: "Nikeah-bound ferry..."
    'Nikeah':      810,    # vanilla: "South Figaro-bound ferry..."
    'Albrook':     1925,   # vanilla: Leo cargo-ship line ($0785)
}

# Per-port flavor dialog shown before the ferry prompt while the sea boss
# (event_bit.FINISHED_NARSHE_BATTLE) is undefeated. IDs sit in the vanilla
# Maduin/Madonna esper-world conversation block, which never plays in ruination.
# Placed in the gap between limited_heals (1467-1470) and SPRING_DIALOG_BASE
# (1480-1495) — outside WARP_DIALOG_IDS (1426-1460). See ARCHIVE.md
# "Ruination Mode — Dialog ID Reservations" for the full Maduin-block layout.
FERRY_FLAVOR_DIALOG = {
    'SouthFigaro': 0x05BF,  # 1471
    'Nikeah':      0x05C0,  # 1472
    'Albrook':     0x05C1,  # 1473
}

FERRY_FLAVOR_TOWN1_TEXT = (
    "We sent out a ship, but it was destroyed by a terrible monster!<end>"
)

# {town1} is replaced with the display name of the chosen TOWN1 port.
FERRY_FLAVOR_OTHER_TEXTS = [
    "A sailor from {town1} washed up... his ship was wrecked with all hands!<end>",
    "The waterways are guarded by a great beast! Can you help us?<end>",
]

# Vanilla "stay" return target — CA/5EB3 is just a single Return.
FERRY_STAY_RETURN_ADDR = 0xa5eb3

FERRY_DISABLED_MESSAGE = (
    "Some of us went out to map the sea, but no one returned.<end>"
)


def _ferry_disabled_patch(dialog_id):
    """4-byte field-event sequence: Display dialog, Return."""
    return bytes([0x4B, dialog_id & 0xFF, dialog_id >> 8, 0xFE])


def _ferry_build_prompt(src_port, destinations):
    """Return dialog text for the src_port sailor offering the given destinations."""
    if len(destinations) == 1:
        dst = FERRY_PORTS[destinations[0]]['display']
        return (
            f"{dst}-bound ferry."
            f"<line><choice> (Still need to shop.)"
            f"<line><choice> (Hop aboard?)<end>"
        )
    dst1 = FERRY_PORTS[destinations[0]]['display']
    dst2 = FERRY_PORTS[destinations[1]]['display']
    return (
        f"Where to?"
        f"<line><choice> (Still need to shop.)"
        f"<line><choice> ({dst1})"
        f"<line><choice> ({dst2})<end>"
    )


def _ferry_build_trip(src_port, dst_port, boss_pack_id=None):
    """Allocate a Bank.CA subroutine that runs the boat-trip animation."""
    src = FERRY_PORTS[src_port]
    dst = FERRY_PORTS[dst_port]

    # Do some math to determine route for animation.  Elbow is at (223, 200).
    elbow = [228, 205]  # [223, 200].  Change destinations to be w.r.t elbow.
    ANIMATION_XY = {
        'SouthFigaro': [-12, 0, direction.RIGHT],
        'Nikeah': [12, 0, direction.LEFT],
        'Albrook': [0, 11, direction.UP],
    }

    delta_xy_1 = [-ANIMATION_XY[src_port][a] for a in range(2)]  # first part of journey (positive is right/down)
    delta_xy_2 = [ANIMATION_XY[dst_port][a] for a in range(2)]  # second part of journey

    # Helper functions
    get_dir = lambda x: [direction.RIGHT, direction.LEFT, direction.DOWN, direction.UP][
        [x[0] > 0, x[0] < 0, x[1] > 0, x[1] < 0].index(True)]
    get_distance = lambda x: abs(x[x.index(0) - 1])

    code = [
        # Begin sea journey
        field.FadeOutSong(8),
        field.FadeOutScreen(),
        field.StartSong(0x3a),  # "Tide"
        field.SetEventBit(event_bit.TEMP_SONG_OVERRIDE),
        field.LoadMap(map_id=0x001, x=ANIMATION_XY[src_port][0] + elbow[0], y=ANIMATION_XY[src_port][1] + elbow[1],
                      direction=ANIMATION_XY[src_port][2], default_music=False, entrance_event=False, airship=False,
                      fade_in=True),
        world.SetSpeed(field_entity.Speed.SLOW),
        world.BecomeShip(),
        world.HideMinimap(),
    ]

    # Go to elbow
    dist = get_distance(delta_xy_1)
    d_ix = get_dir(delta_xy_1)
    while dist > 8:
        code += [
            #vehicle.MoveForward(direction=get_dir(delta_xy_1), distance=8)  # This is the wrong code.  Need something more like field_entity.Move codes
            field_entity.Move(direction=d_ix, distance=8)
        ]
        dist -= 8
    if dist > 0:
        code += [
            field_entity.Move(direction=d_ix, distance=dist)
        ]
    # Sea Battle?  We don't have a background for it (0x0d = raft, 0x29 = airship wor).  Might add some nice danger.
    # Can we capture an unused boss & have it trigger 3/8 of the time, once?
    # We are using the "Kefka (Narshe)" boss for this, since Kefka@Narshe event is not used in Ruination.
    #   Ultros/Chupon --> Sealed Gate event
    #   DoomGaze --> Falcon event
    #   Kefka@Narshe --> Sea boss
    # So we can set event_bit.FINISHED_NARSHE_BATTLE to track it.
    #SHIP_BOSS_BATTLE_PROBABILITY = 0.375
    #skip_boss_chance = int(SHIP_BOSS_BATTLE_PROBABILITY * 255)
    #print(f'USING SEA BOSS BATTLE ID: {boss_pack_id}')
    if boss_pack_id is not None:
        code += [
            world.BranchIfEventBitSet(event_bit.FINISHED_NARSHE_BATTLE, "SKIP_BATTLE"),
            #vehicle.BranchProbability(skip_boss_chance, "SKIP_BATTLE"),
            #vehicle.InvokeBattle(pack=boss_pack_id, background=0x0d),  # Vehicle.InvokeBattle wasn't working.
            world.FadeLoadMap(map_id=0x009, direction=0, default_music=False, x=0, y=0, entrance_event=False,
                              fade_in=False),
            field.InvokeBattleType(pack=boss_pack_id, battle_type=field.BattleType.FRONT, background=0x0d),
            field.SetEventBit(event_bit.FINISHED_NARSHE_BATTLE),
            field.StartSong(0x3a),  # "Tide"
            field.LoadMap(map_id=0x001, x=elbow[0], y=elbow[1], direction=ANIMATION_XY[src_port][2],
                          default_music=False, entrance_event=False, airship=False, fade_in=True),
            world.SetSpeed(field_entity.Speed.SLOW),
            world.BecomeShip(),
            "SKIP_BATTLE",
        ]

    # Complete journey
    dist = get_distance(delta_xy_2)
    d_ix = get_dir(delta_xy_2)
    while dist > 8:
        code += [
            field_entity.Move(direction=d_ix, distance=8)
        ]
        dist -= 8
    if dist > 0:
        code += [
            field_entity.Move(direction=d_ix, distance=dist)
        ]

    code += [
        # Airship move for safety
        vehicle.SetEventBit(event_bit.TEMP_SONG_OVERRIDE),
        vehicle.LoadMap(0x01, direction.DOWN, default_music=False,
                        x=src['wor_dock'][0], y=src['wor_dock'][1],
                        fade_in=False, airship=True),
        vehicle.SetPosition(dst['wor_dock'][0], dst['wor_dock'][1]),
        vehicle.ClearEventBit(event_bit.TEMP_SONG_OVERRIDE),
        vehicle.FadeLoadMap(dst['dest_map'], dst['dest_dir'], default_music=True,
                            x=dst['dest_spawn'][0], y=dst['dest_spawn'][1],
                            fade_in=True, entrance_event=True),
        field.SetParentMap(0x01, direction.DOWN,
                           x=dst['wor_dock'][0], y=dst['wor_dock'][1] - 1),
        field.Return(),
    ]
    return Write(Bank.CA, code, f"ruin ferry {src_port}->{dst_port}").start_address


def _ferry_install_disabled(rom, dialogs):
    """Disable every port's NPC: each shows the disabled message and returns."""
    for port_name in FERRY_PORTS:
        dialog_id = FERRY_PROMPT_DIALOG[port_name]
        dialogs.set_text(dialog_id, FERRY_DISABLED_MESSAGE)
        rom.set_bytes(FERRY_PORTS[port_name]['npc_event_addr'],
                      _ferry_disabled_patch(dialog_id))


def _ferry_install_enabled(rom, dialogs, maps, mapped, args, boss_pack_id=None):
    """For each pair of mapped ports, build a trip subroutine and dispatch event."""
    # Promote the Albrook NPC if Albrook is on the network. Sprite is set here;
    # the visibility bit is flipped via init_event_bits in event/albrook_wob.py
    # (see Events.ruination_mod ordering — fix_ferry_connections runs before the
    # init_event_bits loop, so the bit-flip cannot live here).
    if 'Albrook' in mapped:
        port = FERRY_PORTS['Albrook']
        maps.get_npc(port['sailor_map'], port['sailor_npc_id']).sprite = port['sailor_sprite']

    # Pre-boss flavor dialog: pick one mapped port as TOWN1 (the "we sent out a
    # ship..." sailor); the other(s) get the alternative lines naming TOWN1.
    # When all three ports are mapped, the two non-TOWN1 sailors get distinct
    # alternative lines (one each, shuffled). Only mapped ports get text written.
    town1_port = random.choice(mapped)
    town1_display = FERRY_PORTS[town1_port]['display']
    other_ports = [p for p in mapped if p != town1_port]
    if len(other_ports) >= 2:
        other_texts = random.sample(FERRY_FLAVOR_OTHER_TEXTS, len(other_ports))
    else:
        other_texts = [random.choice(FERRY_FLAVOR_OTHER_TEXTS)]
    other_text_for = dict(zip(other_ports, other_texts))
    flavor_dialog = {}
    for port in mapped:
        flavor_id = FERRY_FLAVOR_DIALOG[port]
        if port == town1_port:
            text = FERRY_FLAVOR_TOWN1_TEXT
        else:
            text = other_text_for[port].format(town1=town1_display)
        dialogs.set_text(flavor_id, text)
        flavor_dialog[port] = flavor_id

    # Build all ordered trip subroutines we will need.
    trips = {}
    for src in mapped:
        for dst in mapped:
            if src == dst:
                continue
            trips[(src, dst)] = _ferry_build_trip(src, dst, boss_pack_id)

    # For each port, build a dispatch event (DialogBranch with stay + 1 or 2 boats)
    # and patch the NPC's event slot with a Branch into it.
    for src in mapped:
        destinations = [p for p in mapped if p != src]
        prompt_text = _ferry_build_prompt(src, destinations)
        dialog_id = FERRY_PROMPT_DIALOG[src]
        dialogs.set_text(dialog_id, prompt_text)

        dest1 = trips[(src, destinations[0])]
        dest2 = trips[(src, destinations[1])] if len(destinations) == 2 else None

        # DialogBranch returns (Dialog, _DialogBranch, Return). Choice 1 is the
        # "stay" option (matches vanilla "Still need to shop."), so we route it
        # to the bare-Return stub at FERRY_STAY_RETURN_ADDR.
        # Pre-boss: show flavor dialog before the prompt; skip once the sea boss
        # is defeated (event_bit.FINISHED_NARSHE_BATTLE).
        dispatch_code = [
            field.BranchIfEventBitSet(event_bit.FINISHED_NARSHE_BATTLE, "FERRY_PROMPT"),
            field.Dialog(flavor_dialog[src]),
            "FERRY_PROMPT",
            field.DialogBranch(dialog_id=dialog_id, dest1=FERRY_STAY_RETURN_ADDR,
                               dest2=dest1, dest3=dest2),
        ]
        space = Write(Bank.CA, dispatch_code, f"ruin ferry dispatch {src}")
        dispatch_addr = space.start_address

        # field.Branch is BranchIfEventBitClear(ALWAYS_CLEAR, dest) = 6 bytes.
        # The vanilla event slots all have >=12 bytes available (verified for
        # SF 0xa77d7=21B, Nikeah 0xa8cbb=31B, Albrook 0xbd1f3=18B).
        #patch = field.Branch(dispatch_addr)
        #opcode, patch_args = patch(None)
        #patch_bytes = bytes([opcode]) + bytes(patch_args)
        #rom.set_bytes(FERRY_PORTS[src]['npc_event_addr'], patch_bytes)
        space = Reserve(FERRY_PORTS[src]['npc_event_addr'], FERRY_PORTS[src]['npc_event_addr']+5, f"ruin ferry dispatch hook {src}")
        space.write(field.Branch(dispatch_addr))

    if args.debug:
        for (src, dst), addr in trips.items():
            print(f"Ferry: trip {src}->{dst} at {addr:#x}")


def fix_ferry_connections(rom, dialogs, maps, ruin_map, args, boss_pack_id=None):
    """Wire up the SF / Nikeah / Albrook ferry network for ruination mode.

    If 0 or 1 of the three ports has any reachable rooms on the map, every
    sailor shows a disabled message. If 2 or 3 are mapped, each mapped sailor
    offers travel to every other mapped port. The Albrook NPC is a generic
    sprite-16 NPC on map 0x14C that we promote to sprite 54 (sailor) and make
    visible via npc_bit 0x565 (the latter via init_event_bits in
    event/albrook_wob.py).

    Uses the rooms actually placed in each branch (not ruin_map.AreasUsed),
    because distribution can tag an area with a branch whose rooms already
    lived elsewhere — leaving the ferry enabled when a port has no reachable
    rooms on the map.
    """
    actual_areas_used = ruin_map.compute_actual_areas_used()
    mapped = [p for p in FERRY_PORTS if p in actual_areas_used]

    if args.debug:
        print(f"Ferry: mapped ports = {mapped}")

    if len(mapped) < 2:
        _ferry_install_disabled(rom, dialogs)
        if args.debug:
            print("Ferry: <2 ports mapped - all sailors disabled")
        return

    _ferry_install_enabled(rom, dialogs, maps, mapped, args, boss_pack_id)
