from data.event_exit_info import *
from data.rooms import exit_world, shared_oneways
from data.parse import delete_nops, branch_parser, get_branch_code
from instruction import field
import instruction.field.entity as field_entity

from memory.space import Allocate, Bank, Free, Write, Reserve
from data.map_exit_extra import exit_data as exit_partner
from data.map_event import MapEvent
from event.switchyard import SummonAirship

# NOTES:
# To be comprehensive, we should treat this the same way we treat exits:
#   - load all vanilla connections from the ROM at initialization
#   - Make any modifications in mod()
#   - write all connections at the end (just before writing exits, presumably, since this acts on exits, not the ROM)
# This will be a little tricky because:
#   - changing one connection shouldn't leave a 'hanging' connection.  Will have to be careful about this.
#       just double up on connections for doors? might be smart. in-->out for every possible in.  Only change outs.
#   - have to document world & event data somewhere.
#       - can look for event tiles directly
#       - world bit is metadata: currently included in room_data, but that's not single-valued.
#           - TO DO: ADD WORLD DATA FOR EVERY ROOM!
#           - not being single valued doesn't matter for this: doubled-up rooms never change worlds.

class Transitions:
    FREE_MEMORY = False
    verbose = False

    def __init__(self, mapping, rom, exit_data, event_data, include_script_data=None):
        self.transitions = []
        self.rom = rom
        self.include_script_data = include_script_data
        if self.include_script_data is None:
            self.include_script_data = {}

        for m in mapping:
            # Check reasons to overwrite this transition
            flags = [(3000 > m[0] >= 2000) and (m[0] != m[1] - 1000),  # connecting two unequal one-ways...
                     m[0] in exit_event_patch,                 # modifications to exit script
                     m[1] - 1000 in entrance_event_patch,      # modifications to entrance script
                     (1500 <= m[0] < 2000),                    # connecting a one-way acting as a door
                     (m[0] < 1500),                            # connecting a door acting as a one-way
                     (6000 < m[1])                             # connecting to the exit of a door acting as a one-way
                     ]
            # If a shared_oneway, only write the lowest-valued one
            soo_flag = True
            if m[0] in shared_oneways:
                soo_flag = m[0] < min(shared_oneways[m[0]])

            if flags.count(True) > 0 and soo_flag:
                if self.verbose:
                    print('Making new transition: ', m[0], m[1])
                new_trans = Transition(m[0], m[1], rom, exit_data, event_data)
                self.transitions.append(new_trans)

        if self.FREE_MEMORY:
            self.free()

        if self.verbose:
            print('Number of Transitions = ', len(self.transitions))
            hexify = lambda src: [hex(a)[2:] for a in src]
            for t in self.transitions:
                print(t.exit.id, '-->', hexify(t.exit.exit_code))
                print(t.entr.id, '-->', hexify(t.entr.entr_code))

        self.mod()  # Modify the code after loading all transitions


    def free(self):
        # Free previous event data space to be overwritten (after all are modified)
        for t in self.transitions:
            # Note: only need to free from exits (entrances are freed as part of this)
            Free(t.exit.event_addr, t.exit.event_addr + t.exit.event_length - 1)
            print('\n\tFreed addresses: ', hex(t.exit.event_addr), hex(t.exit.event_addr + t.exit.event_length - 1))

    def mod(self):
        # Modify the event code to accomodate custom changes
        # Check for other event patches & implement if found
        for t in self.transitions:
            # Initialize source codes
            if t.exit.use_jmp:
                # If writing as subroutine: we want map load command only from exit
                src = [t.exit.exit_code[-1]]
            else:
                src = t.exit.exit_code

            if t.entr.use_jmp:
                # If writing as subroutine: we want map load command from exit + Call Entrance Script + return command
                src_end = t.entr.entr_code[:5] + [0xb2] + \
                          list((t.entr.event_addr + t.entr.event_split + 5 - EVENT_CODE_START).to_bytes(3,"little")) + \
                          [0xfe]
            else:
                src_end = t.entr.entr_code

            # Run event patches.  Do entrance events first (to avoid conflict if both adding & removing same status)
            if t.entr.id in entrance_event_patch.keys():
                [src, src_end] = entrance_event_patch[t.entr.id](src, src_end)
            if t.exit.id in exit_event_patch.keys():
                [src, src_end] = exit_event_patch[t.exit.id](src, src_end)

            # Perform common event patches
            ex_patch = []
            en_patch = []
            t.patches = [False, False, False, False, False, False, False]
            if t.exit.is_char_hidden and not t.entr.is_char_hidden:
                t.patches[0] = 'unhide'
                # Character is hidden during the transition (command [0x42, 0x31]) and not unhidden later.
                # Add a "Show object 31" line ("0x41 0x31", two bytes)
                en_patch += [0x41, 0x31]  # [field.ShowEntity(field_entity.PARTY0)]   #
            if t.exit.is_song_override_on and not t.entr.is_song_override_on:
                t.patches[1] = 'unsong'
                # Song override bit is on in the exit but not cleared in the entrance.
                # Add a "clear $1E80($1CC)" (song override) before transition
                ex_patch += [0xd3, 0xcc]  # [field.ClearEventBit(event_bit.TEMP_SONG_OVERRIDE)]  #
            if t.exit.is_screen_hold_on != t.entr.is_screen_hold_on:
                if t.exit.is_screen_hold_on:
                    t.patches[2] = 'hold_off'
                    # Hold screen bit is set (command 0x38) in the exit but not freed (command 0x39) in the entrance
                    # Add a "0x39 Free Screen" before transition
                    ex_patch += [0x39]  # [field.FreeScreen()]  #
                elif t.entr.is_screen_hold_on:
                    t.patches[2] = 'hold_on'
                    # Hold screen bit is expected to be set (command 0x38) in the entrance
                    # Add a "0x38 Hold Screen" before transition
                    ex_patch += [0x38]  # [field.HoldScreen()]  #
            if t.exit.world != t.entr.world:
                # include code to set the appropriate world:
                if t.entr.world == 0:
                    t.patches[3] = 'WoB'
                    # Set world bit to WoB: [0xd1, 0xa4]
                    ex_patch += [0xd1, 0xa4]  # [field.ClearEventBit(0xa4)]
                elif t.entr.world == 1:
                    t.patches[3] = 'WoR'
                    # Set world bit to WoR: [0xd0, 0xa4]
                    ex_patch += [0xd0, 0xa4]  # [field.SetEventBit(0xa4)]
            if t.exit.is_on_raft != t.entr.is_on_raft:
                # include code to set the appropriate raft graphic
                if t.exit.is_on_raft:
                    t.patches[4] = 'remove'
                    # Call "remove raft" subroutine (CB/04AA)
                    en_patch += [0xb2, 0xaa, 0x04, 0x01]  # [field.Call(0xb04aa)]
                elif t.entr.is_on_raft:
                    t.patches[4] = 'add'
                    # Call "place on raft" subroutine (CB/050F)
                    en_patch += [0xb2, 0x0f, 0x05, 0x01]  # [field.Call(0xb050f)]

            # Include code for required event bit states
            entr_bits = {}
            if t.entr.id in require_event_bit.keys():
                entr_bits = require_event_bit[t.entr.id]
            if len(entr_bits) > 0:
                t.patches[5] = 'bit'
                for k in entr_bits.keys():
                    if entr_bits[k]:
                        t.patches[5] += '_set' + hex(k)[2:]
                        bitsrc = [field.SetEventBit(k)]
                    else:
                        t.patches[5] += '_clear' + hex(k)[2:]
                        bitsrc = [field.ClearEventBit(k)]
                    ex_patch += [bitsrc[0].opcode] + bitsrc[0].args

            if t.exit.id in self.include_script_data.keys():
                # This is attempting to look at an event script, read it, build a branch code based on what it says, and then load the door.
                # Instead, I think we should just call the script, followed by loading the door.

                # This is an event tile behaving as a door that needs to call an event script for its partner.
                #this_addr = self.call_script_addr[t.exit.id]

                # Instead instead, just include the required data here.
                this_data = self.include_script_data[t.exit.id]

                # srcdata = self.rom.get_bytes(this_addr, 6)
                # if self.verbose:
                #     print([hex(a) for a in srcdata])
                # [comm_type, is_set, ebit, branch_addr] = branch_parser(srcdata)
                # if self.verbose:
                #     print(comm_type, is_set, ebit, branch_addr)
                #
                # if branch_addr == 0x5eb3:
                #     # This is a "Return if event bit CONDITION" call.  Swap the condition and branch to the next line.
                #     branch_addr = this_addr + 6
                #     is_set = not is_set
                #
                # branch_src = get_branch_code(ebit, is_set, branch_addr + EVENT_CODE_START, map_id=t.exit.dest_location[0])
                # if self.verbose:
                #     print('ZAP ZAP ZAP: ', [branch_src[0].opcode] + branch_src[0].args)
                # ex_patch += [branch_src[0].opcode] + branch_src[0].args

                #branch_src = get_branch_code(event_bit.ALWAYS_CLEAR, is_set=False, branch_addr=this_addr, map_id=t.exit.dest_location[0])
                #ex_patch += [branch_src[0].opcode] + branch_src[0].args

                branch_src = this_data[0] # convert command script to bits?

                if this_data[1]:
                    # Include before load map
                    ex_patch += branch_src
                else:
                    # Include after load map
                    en_patch += branch_src

                if self.verbose:
                    #print(t.exit.id, t.entr.id, ' incl. branch to ', hex(this_addr))
                    print_src = []
                    for b in branch_src:
                        if isinstance(b, str) or isinstance(b, int):
                            print_src += [b]
                        else:
                            print_src += [b.__str__()]
                    print(t.exit.id, t.entr.id, ' incl. addl. data ', print_src)

            # Check if updated parent map is required
            if t.exit.do_update_parent_map:
                t.patches[6] = 'update'
                this_dir = t.exit.partner_destination[3]
                bitsrc = [field.SetParentMap(map_id=t.exit.world,
                                             x=t.exit.partner_destination[1] + direction.xy_shift_parent_map(this_dir)[0],
                                             y=t.exit.partner_destination[2] + direction.xy_shift_parent_map(this_dir)[1],
                                             direction=this_dir)]
                en_patch += [bitsrc[0].opcode] + bitsrc[0].args

            # Add patched lines before map transition
            src = src[:-1] + ex_patch + src[-1:]

            # Add patched lines after map transition
            src_end = src_end[:5] + en_patch + src_end[5:]

            if t.entr.dest_location[0] in [0x0, 0x1]:
                # This is loading to a world map.  Summon the airship, and make everything happen before that.
                get_airship_src = SummonAirship(t.entr.dest_location[0], t.entr.dest_location[1], t.entr.dest_location[2], bytes=True)
                #print([hex(a)[2:] for a in get_airship_src])
                src = src[:-1] + en_patch + get_airship_src
            else:
                # Combine events
                src.extend(src_end)

            # Delete NOPs, if requested, to save space
            # Note there is the possibility for conflict with event_address_patch - be careful!
            if False:
                src = delete_nops(src)

            # Save the modified source code
            t.src = src

    def write(self, maps):
        # Write modified events to the ROM
        for t in self.transitions:
            # Allocate space
            src_len = 0
            for s in t.src:
                if isinstance(s, int):
                    src_len += 1
                elif isinstance(s, str):
                    pass
                else:
                    src_len += s.__len__()
            space = Allocate(Bank.CC, src_len, "Exit Event Randomize: " + str(t.exit.id) + " --> " + str(t.entr.id))
            new_event_address = space.start_address

            # Check for event address patches & implement if found
            if t.exit.id in event_address_patch.keys() and not t.exit.use_jmp:
                t.src = event_address_patch[t.exit.id](t.src, new_event_address)

            space.write(t.src)
            bit_src = space.rom.get_bytes(new_event_address, src_len)

            if self.verbose:
                addr = [t.exit.event_addr, t.entr.event_addr]
                for i in range(len(addr)):
                    if addr[i] is not None:
                        addr[i] = str(hex(addr[i]))
                print('Writing: ', t.exit.id, ' --> ', t.entr.id,
                      ':\n\toriginal memory addresses: ', str(addr[0]), ', ', str(addr[1]),
                      '\n\tpatches applied: ', t.patches,
                      '\n\tuse jump method: ', t.exit.use_jmp,
                      '\n\tbitstring: ', [hex(s)[2:] for s in bit_src])  # t.src
                print('\n\tnew memory address: ', hex(new_event_address))

            if t.exit.use_jmp:
                # Overwrite the Load Map command with a CALL SUBROUTINE & RETURN & NOP (B2 XX XX XX FE FD)
                if t.exit.location[0] <= 0x2:
                    # There doesn't appear to be an overworld "Call" routine (straight goto).
                    # The closest is an overworld branch, which requires 7 bits.  Jmp commands must fit in 6.
                    print('Warning: cannot use JMP routines on world map! ', t.exit.id ,' --> ', t.entr.id, '!')

                jump_src = [0xb2] + list((new_event_address - EVENT_CODE_START).to_bytes(3, "little")) + [0xfe, 0xfd]
                self.rom.set_bytes(t.exit.event_addr + t.exit.event_split - 1, jump_src)

                if t.exit.id in multi_events.keys():
                    # Patch sister event transitions
                    for me in multi_events[t.exit.id]:
                        this_addr = event_exit_info[me][0]
                        this_split = event_exit_info[me][2]
                        self.rom.set_bytes(this_addr + this_split - 1, jump_src)

            elif t.exit.event_addr is not None:
                if t.exit.location[1] == 'NPC':
                    # This is an NPC event.  (see e.g. Cid/Minecart entrance).  NPC ID is stored in location[2]
                    npc = maps.get_npc(t.exit.location[0], t.exit.location[2] + 0x10)
                    # print('Cid index = ', self.get_npc_index(0x110, 0 + 0x10))
                    npc.set_event_address(new_event_address)
                    # cid.print()

                else:
                    # Update the MapEvent.event_address = Address(Event1a)
                    this_event = maps.get_event(t.exit.location[0], t.exit.location[1], t.exit.location[2])
                    this_event.event_address = new_event_address - EVENT_CODE_START

                    if t.exit.id in multi_events.keys():
                        # Other tiles must also be updated to point to the event at the appropriate offset
                        for le in multi_events[t.exit.id]:
                            le_addr = event_exit_info[le][0]
                            le_mxy = event_exit_info[le][5]  # [map_id, x, y]
                            le_event = maps.get_event(le_mxy[0], le_mxy[1], le_mxy[2])  # get event using [map_id, x, y] data
                            le_event.event_address = new_event_address + (le_addr - t.exit.event_addr) - EVENT_CODE_START

            else:
                # Create a new MapEvent for this event
                new_event = MapEvent()
                new_event.x = t.exit.location[1]
                new_event.y = t.exit.location[2]
                new_event.event_address = new_event_address - EVENT_CODE_START
                maps.add_event(t.exit.location[0], new_event)
                if self.verbose:
                    print('Added new map event: ', t.exit.location[0], new_event.x, new_event.y, hex(new_event_address))

                # Note that if this is a door acting as a one-way, the door itself is not actually used.


class Transition:
    def __init__(self, exit_id, entr_id, rom, exit_data, event_data):
        # Import exit
        self.exit = EventExit(exit_id, rom, exit_data, event_data, is_event=(1500 < exit_id < 4000) )

        # Import entrance
        if 4000 > entr_id >= 3000:
            # This is a pit associated with an event transition
            self.entr = EventExit(entr_id - 1000, rom, exit_data, event_data, is_event=True)
        elif 1500 <= entr_id < 2000:
            # This is an event tile behaving as a normal door.
            partner_id = exit_partner[entr_id][0]
            if 1500 <= partner_id < 2000:
                # If the vanilla partner is also an event tile, we can use its event code.
                self.entr = EventExit(entr_id, rom, exit_data, event_data, is_event=True, use_event_info=partner_id)
            else:
                # The vanilla partner is a normal door.  Construct the exit script the same way we do for doors.
                self.entr = EventExit(entr_id, rom, exit_data, event_data, is_event=False)
        elif entr_id > 6000:
            # This is the one-way exit of a normal door acting as a one-way.
            self.entr = EventExit(entr_id, rom, exit_data, event_data, is_event=False)
        else:
            # This is a normal door
            self.entr = EventExit(entr_id, rom, exit_data, event_data, is_event=False)


class EventExit:
    event_addr = None
    event_length = 0
    event_split = 0
    is_char_hidden = False
    is_song_override_on = False
    is_screen_hold_on = False
    is_on_raft = False
    description = ''
    location = []
    dest_location = []
    world = -1
    use_jmp = False
    do_update_parent_map = False

    exit_code = [0x6a]
    entr_code = []  # [exit_location[2], exit_location[6] << 4, exit_location[0], exit_location[1], 0x80, 0xfe]

    def __init__(self, ID, rom=[], exit_data=[], event_data=[], is_event=True, use_event_info=None):
        self.id = ID

        if is_event:
            if use_event_info:
                event_info = event_data[use_event_info]
            else:
                event_info = event_data[ID]

            # Data structure: event_exit_info[id] = ...
            #   [original address, event bit length, split point, transition state, description, location, method]
            #   transition state = [is_chararacter_hidden, is_song_override_on, is_screen_hold_on]
            #   location = [map_id, x, y]
            self.event_addr = event_info[0]
            self.event_length = event_info[1]
            self.event_split = event_info[2]
            self.is_char_hidden = event_info[3][0]
            self.is_song_override_on = event_info[3][1]
            self.is_screen_hold_on = event_info[3][2]
            self.is_on_raft = event_info[3][3]
            self.do_update_parent_map = event_info[3][4]
            self.description = event_info[4]
            self.location = event_info[5]
            self.method = event_info[6]
            self.world = exit_world[ID]
            if self.method == 'JMP':
                self.use_jmp = True

            #print(self.id, self.event_addr, self.event_length, self.event_split)
            self.exit_code = rom.get_bytes(self.event_addr, self.event_split)  # First half of event
            self.entr_code = rom.get_bytes(self.event_addr + self.event_split,
                                           self.event_length - self.event_split)  # Second half of event

            dest_map = self.entr_code[0] + (((self.entr_code[1] % 0x10) % 0x4) << 8)  # extract destination map_id
            self.dest_location = [dest_map, self.entr_code[2], self.entr_code[3]]  # [map_id, x, y]

            # Get partner connection info for Update Parent Map
            if self.do_update_parent_map:
                partner_id = exit_partner[ID][0]
                partner_data = exit_data[partner_id]  # If partner isn't in exit_data, this shouldn't be a door connection.
                self.partner_destination = partner_data[:3] + [partner_data[6]]  # [dest_map, dest_x, dest_y, facing]

        else:
            # Handle the small number of one-way entrances from doors.
            if ID < 6000:
                # get vanilla connecting door to this ID
                partner_ID = exit_partner[ID][0]
                if ID in exit_data.keys():
                    exit_location = exit_data[ID]  # Get location info for this door
                elif ID - 4000 in exit_data.keys():
                    # This is a logical door, use its partner
                    exit_location = exit_data[ID - 4000]
                else:
                    raise Exception('Exit data not found for ID: ' + str(ID))
            else:
                # This is the destination of a door acting as a one-way.  Use the door itself.
                partner_ID = ID - 6000
                exit_location = exit_data[ID - 6000]  # Get location info for this door.

            if partner_ID is None:
                # This is a door acting as a one-way trap or pit.  If it's a pit, its destination is the destination.
                partner_data = exit_data[ID]
            elif partner_ID in exit_data.keys():
                # This is a door transition.  Get connection data for partner door
                partner_data = exit_data[partner_ID]
            elif partner_ID - 4000 in exit_data.keys():
                # This is a logical door transition.  Get connection data from partner door
                partner_data = exit_data[partner_ID - 4000]
            else:
                raise Exception('Exit data not found for ID: ' + str(partner_ID))

            # exit_original_data structure:
            # [dest_map, dest_x, dest_y,
            #  refreshparentmap, enterlowZlevel, displaylocationname, facing, unknown,
            #  x, y, size, direction, map_id].  note: map_id appended in maps.read().

            # Use exit_location for the "exit" info
            self.location = exit_location[-1:] + exit_location[8:12]  # [map_id, x, y, size, direction]
            #self.destination = exit_location[:3] + [exit_location[6]] # [dest_map, dest_x, dest_y, facing]
            #print(self.id, exit_location, self.location, self.destination)

            self.world = exit_world[ID]            # which world is it in?

            # Use partner_data for the "entrance" info
            self.dest_location = partner_data[0:3]  # [dest_map, dest_x, dest_y]

            # if ID in exit_door_patch:
            #     # Prepend any data required by the door
            #     self.exit_code = exit_door_patch[ID] + self.exit_code

            # Load the map with facing & destination music; x coord; y coord; fade screen in & run entrance event, return
            self.entr_code = [partner_data[0] % 0x100,
                              (partner_data[0] // 0x100) + (partner_data[6] << 4),
                              partner_data[1], partner_data[2], 0x80]
            if self.location[0] < 2:
                self.entr_code += [0xff]  # world.End()
            else:
                self.entr_code += [0xfe]  # field.Return()

            # if ID in entrance_door_patch.keys():
            #     # This door additionally requires code to be executed after the load command
            #     if entrance_door_patch[ID] is list:
            #         self.entr_code += entrance_door_patch[ID]
            #     else:
            #         self.entr_code += entrance_door_patch[ID](self.args)

