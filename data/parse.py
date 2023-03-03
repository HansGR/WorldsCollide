from instruction import field

def delete_nops(src):
    # Remove No Operation (NOPs, 0xfd) commands from a source string
    sp = simple_parser(src)
    out = []
    for o, p in sp:
        # print('\t', hex(o)[2:], [hex(a)[2:] for a in p])
        if isinstance(o, int):
            if o != 0xfd:
                out.append(o)
                out.extend(p)
        else:
            if o.opcode != 0xfd:
                out.append(o)
    return out

def simple_parser(src):
    while len(src) > 0:
        opcode = src.pop(0)
        if isinstance(opcode, int):
            split = OP_LENGTH[opcode]

            if split == 'var':
                if opcode < 0x35:
                    # Character action queues; search for termination (0xff)
                    split = src.index(0xff)+1

                elif opcode == 0x73 or opcode == 0x74:
                    # Replace background; get split from tile size
                    tilesize = src[2]*src[3]
                    split = 4 + tilesize

                elif opcode == 0xb0:
                    # Repeating block of commands; look for 0xb1 (terminate) or 0xbc (terminate if event bit is set, 2 params)
                    inds = [len(src) for i in range(2)]
                    if 0xb1 in src:
                        inds[0] = src.index(0xb1)+1
                    if 0xbc in src:
                        inds[1] = src.index(0xbc)+3
                    split = min(inds)

                elif opcode == 0xb6:
                    # Dialog box with choices; there's no way to determine how many options there are locally in the event,
                    # and most of them are 2.  Here's hoping.
                    num_options = 2
                    split = 3*num_options

                else:
                    raise Exception('Unimplemented variable opcode: ', opcode)

            params = src[:split]
            src = src[split:]

        else:
            # This is probably a Field class object.  just move on.
            params = []

        yield opcode, params

OP_LENGTH = {
    #0x00-34: 0, # Begin action queue for a character
    0x35: 1, # Pause event until a character's action queue has finished executing
    0x36: 1, # Prevent a character from passing through sprites
    0x37: 2, # Assign a different sprite to a character
    0x38: 0, # Prevent the camera from following a character
    0x39: 0, # Allow the camera to follow a character
    0x3A: 0, # Allow player to move while the event is executing
    0x3B: 0, # I believe this clears several flags for the leader of your party.
    0x3C: 4, # Temporarily reorganize party for event
    0x3D: 1, # Creates an object
    0x3E: 1, # Deletes an object
    0x3F: 2, # Add or remove a character from a party.
    0x40: 2, # Assign properties
    0x41: 1, # Show a sprite on the field.
    0x42: 1, # Hide a sprite on the field.
    0x43: 2, # Assign a palette to a character
    0x44: 2, # Place character on vehicle
    0x45: 0, # Refreshes objects, apparently.
    0x46: 1, # Switch current party
    0x47: 0, # Make character in slot 0 the lead character
    0x48: 2, # Display a text box, but continue event without waiting for player to dismiss the text box
    0x49: 0, # Wait until previous text box is dismissed before continuing event. Useful after text has been shown with command 48
    0x4B: 2, # Display a text box, wait until text box is dismissed to continue event
    0x4C: 2, # Center screen on party and invoke a battle with a particular background.
    0x4D: 2, # Invoke a battle with a particular background.
    0x4E: 0, # Labeled as "Invoke battle, random encounter as determined by zone" by the original document.  Testing it, I'm not sure.
    0x4F: 0, # Returns you to the position where you last saved the game. Alternately, it returns you to the title screen if you have not saved the game.
    0x50: 1, # Tints the background with a chosen colour
    0x51: 3, # Tints parts of the background within a certain colour range with a chosen colour
    0x52: 1, # Tints all sprites with a chosen colour
    0x53: 3, # Tints parts of sprites within a certain colour range with a chosen colour
    0x54: 0, # If the screen is currently flashing, or the colour component has been increased, return it to normal
    0x55: 1, # Flash the screen with a particular colour, #
    0x56: 1, # Increase the colour component for a particular colour, # works like flashing, but the colour change stays on screen)
    0x57: 1, # Decrease the colour component for a particular colour. The inverse of command 56
    0x58: 1, # Shake the screen
    0x59: 1, # Unfade the screen at a specific speed
    0x5A: 1, # Fade the screen at a specific speed
    0x5C: 0, # Pause event execution until fade in or fade out is complete
    0x5D: 2, # Scroll layer 1.  Sprites will move with layer 1
    0x5E: 2, # Scroll layer 2
    0x5F: 2, # Scroll layer 3
    0x60: 2, # Give objects on a certain palette a different palette
    0x61: 3, # Colorize a colour range to a specific colour
    0x62: 1, # Mosaic the screen
    0x63: 1, # Create a spotlight around the character
    0x6A: 5, # Fade out, and load a new map
    0x6B: 5, # Load a new map
    0x6C: 5, # Set the world map and position the party will be returned to when they exit to the world map
    0x70: 2, # Same as 5D?  If you have any further insight please let me know
    0x71: 2, # Same as 5E?  If you have any further insight please let me know
    0x72: 2, # Same as 5F?  If you have any further insight please let me know
    0x73: 'var', # Replace a portion of the background.  The background will refresh immediately after the command is executed
    0x74: 'var', # Replace a portion of the background.  The background will not refresh immediately after the command is executed.
    0x75: 0, # Reloads the background.  Useful if it has been modified with command 74
    0x77: 1, # Perform level averaging on a character
    0x78: 1, # Allow a character to pass through sprites
    0x79: 2, # Place a party on a map
    0x7A: 4, # Cause a character to activate a different event when spoken to
    0x7B: 0, # Lets the screen snap back to the current party in a multiparty battle.
    0x7C: 1, # Cause a character to activate an event when touched
    0x7E: 2, # Move party to a position and fade in the screen
    0x7F: 2, # Assign a name to a character
    0x80: 1, # Add an item to your inventory
    0x82: 0, # Set party 1 as the backup party.
    0x84: 2, # Give Gil to the party
    0x85: 2, # Take Gil from the party
    0x86: 1, # Gives Esper to the party
    0x87: 1, # Take Esper from party
    0x88: 3, # Removes status ailments from a character
    0x89: 3, # Inflict status ailments on a character
    0x8A: 3, # Toggle status ailments on a character
    0x8B: 2, # Add or subtract an amount from a character's HP
    0x8C: 2, # Boost a character's MP to maximum
    0x8D: 1, # Remove all equipment from a character and place it in your inventory
    0x8E: 0, # Invoke a battle based on the chest opened.
    0x8F: 0, # Unlocks all of Cyan's SwdTech skills
    0x90: 0, # Unlock Bum Rush
    0x91: 0, # Pause the event for 15 units.
    0x92: 0, # Pause the event for 30 units.
    0x93: 0, # Pause the event for 45 units.
    0x94: 0, # Pause the event for 60 units.
    0x95: 0, # Pause the event for 120 units.
    0x96: 0, # Unfades the screen.
    0x97: 0, # Fades the screen.
    0x98: 1, # Call the name change screen for a character.
    0x99: 3, # Call the screen to select a party
    0x9A: 0, # Invoke the screen where you select an item to bet at the Coliseum.
    0x9B: 1, # Invoke a shop screen
    0x9C: 1, # Give a character optimum equipment
    0x9D: 0, # Invoke the screen before the final battle where you choose your party order
    0xA0: 5, # Invoke a timer
    0xA1: 1, # Use this to reset a timer, clearing it from the display and preventing it from triggering
    0xA2: 0, # Unknown, but used, command.
    0xA6: 0, # Eliminate the rotating pyramid
    0xA7: 1, # Create a rotating pyramid around a character
    0xA8: 0, # Show the cutscene where the Floating Continent flies into the sky
    0xA9: 0, # Show the title screen
    0xAA: 0, # Show the scene with Magitek Armour walking through the snowfields
    0xAB: 0, # Show the game loading screen
    0xAC: 0, # Fade in the screen after loading a new game
    0xAD: 0, # Show world getting torn apart
    0xAE: 0, # Shows the mine cart escape from the Magitek facility
    0xAF: 0, # Start a Coliseum battle
    0xB0: 'var', # Repeat a sequence of event commands
    0xB1: 0, # Denotes the end of a block of repeating commands
    0xB2: 3, # Jump to an address in the event code
    0xB3: 4, # Jump to an address in the event code multiple times.
    0xB4: 1, # Pause execution of the event for a small amount of time
    0xB5: 1, # Pause execution of the event for an amount of time x15
    0xB6: 'var', # This is meant to be placed after a dialog box that gives the player multiple choices.  This will jump to different events
    0xB7: 4, # Branch to an address if a battle related event bit is clear
    0xB8: 1, # Set a battle related event bit
    0xB9: 1, # Clear a battle related event bit
    0xBA: 1, # Play one of the mode 7 ending cutscenes
    0xBB: 1, # Wait for a predetermined part of the ending theme
    0xBC: 2, # Stop repeating a block of commands
    0xBD: 3, # Pseudo randomly jump to an address 50% of the time
    0xBE: 0, # Branch based on the current "CaseWord" bits.
    0xBF: 0, # Show airship flying sideways over land
    0xC0: 5, # Branch to an address based on event bits:
    0xC1: 7,
    0xC2: 9,
    0xC3: 11,
    0xC4: 13,
    0xC5: 15,
    0xC6: 17,
    0xC7: 19,
    0xC8: 5,
    0xC9: 7,
    0xCA: 9,
    0xCB: 11,
    0xCC: 13,
    0xCD: 15,
    0xCE: 17,
    0xCF: 19,
    0xD0: 1,  # Set / clear event bits
    0xD1: 1,
    0xD2: 1,
    0xD3: 1,
    0xD4: 1,
    0xD5: 1,
    0xD6: 1,
    0xD7: 1,
    0xD8: 1,
    0xD9: 1,
    0xDA: 1,
    0xDB: 1,
    0xDC: 1,
    0xDD: 1,
    0xDE: 0, # Set CaseWord bits depending on who is in the party
    0xE0: 0, # Set CaseWord bits depending on who has been encountered so far
    0xE1: 0, # Set CaseWord bits depending on who is available on the airship
    0xE2: 0, # Set CaseWord bits depending on who is in the lead of the current party
    0xE3: 0, # Set CaseWord bits depending on who is in any of the three parties
    0xE4: 0, # Set CaseWord bits depending on which party is currently active
    0xE8: 3, # Set the value of an event word
    0xE9: 3, # Increment the value in an event word
    0xEA: 3, # Decrement the value in an event word
    0xEB: 3, # Compare the value in a word to another value, and store the results in the CaseWord
    0xEF: 2, # Start playing a song at a specific volume
    0xF0: 1, # Start playing a song
    0xF1: 2, # Fade in a song
    0xF2: 1, # Fade out a song
    0xF3: 1, # Fade in the song that was previously playing before the song that is currently playing
    0xF4: 1, # Play a sound effect
    0xF5: 3, # Play a sound effect that is unbalanced between the left and right speaker, #
    0xF6: 3, # Various music related commands including affecting pitch/tempo/volume/etc. for currently playing sound effects/music,
    0xF7: 0, # Transitions one song to another
    0xF9: 1, # Wait until a predetermined point in the song
    0xFA: 0, # Wait until the current song fades out or ends before continuing
    0xFB: 0, # According to the event dump, this applies some sort of special effect to the sound effect. I don't hear it though
    0xFD: 0, # Does nothing
    0xFE: 0, # Return from the subroutine if you are in a subroutine.  End the event and return control to the player if you are notable
    0xFF: 0 # End a script started with a command from $00 to $34
}
for i in range(0x35):
    OP_LENGTH[i] = 'var'