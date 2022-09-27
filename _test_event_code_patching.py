from memory import rom
from data.event_exit_info import event_exit_info, exit_event_patch, entrance_event_patch, event_address_patch

hexify = lambda src: [hex(a)[2:] for a in src]

m = [2005, 3016]  # [Exit event, entrance event]

# Load exit_event_info[keys]
fn = 'FFIII.smc'  # vanilla rom
rom = rom.ROM(fn)

# Code from MapEvents.mod():
exit_info = event_exit_info[m[0]]
exit_address = exit_info[0]
exit_length = exit_info[1]
exit_split = exit_info[2]

# Right now the convention is that vanilla one-way entrance ID = (vanilla one-way exit ID + 1000)
entr_info = event_exit_info[m[1] - 1000]
entr_address = entr_info[0]
entr_length = entr_info[1]
entr_split = entr_info[2]

# Write a new Event1a = Event1[0:split1] + Event2[split2:]
src = rom.get_bytes(exit_address, exit_split)  # First half of event
src_end = rom.get_bytes(entr_address + entr_split, entr_length - entr_split)

print('ExitA (', hex(exit_address),'):', hexify(src))
print('ExitB (', hex(entr_address),'):', hexify(src_end))

# Perform common event patches
if exit_info[3] and not entr_info[3]:
    # Character is hidden during the transition and not unhidden later.
    # Add a "Show object 31" line after map transition ("0x41 0x31", two bytes) after the 6A or 6B
    src_end = src_end[:5] + [0x41, 0x31] + src_end[5:]

# Check for other event patches & implement if found
if m[0] in exit_event_patch.keys():
    [src, src_end] = exit_event_patch[m[0]](src, src_end)
if m[1] in entrance_event_patch.keys():
    [src, src_end] = entrance_event_patch[m[1]](src, src_end)

# Combine events
src.extend(src_end)

print('Final:', hexify(src))

# Update the MapEvent.event_address = Address(Event1a)
#self.events[self.event_address_index[exit_address - self.BASE_OFFSET]].event_address = new_event_address - self.BASE_OFFSET
