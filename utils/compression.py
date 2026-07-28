WINDOW_SIZE = 0x800
WINDOW_START = 0x7de # why start here?

MIN_MULTI_LENGTH = 3
MAX_MULTI_LENGTH = 34
MAX_COMPRESS_SIZE = 2 ** 16 - 1

def compress(data):
    result = []
    data_index = 0

    group = []
    control_byte = 0
    control_bit = 1

    byte_positions = {} # lists of sorted positions each byte occurs at
    window_indices = {} # start indices of byte_positions within current window
    for index, byte in enumerate(data):
        if byte in byte_positions:
            byte_positions[byte].append(index)
        else:
            byte_positions[byte] = [index]
            window_indices[byte] = 0

    while data_index < len(data):
        longest_length = 0
        longest_start = 0

        start_byte = data[data_index]
        for x in range(window_indices[start_byte], len(byte_positions[start_byte])):
            position = byte_positions[start_byte][x]

            if position >= data_index:
                # window has not reached position yet, skip the rest of the positions
                break
            if position < data_index - WINDOW_SIZE:
                # position is no longer within the window, increment window index for this byte and go to next position
                window_indices[start_byte] += 1
                continue

            try:
                length = 1
                while length < MAX_MULTI_LENGTH and data[data_index + length] == data[position + length]:
                    length += 1
            except IndexError:
                pass

            if length > longest_length:
                longest_length = length
                longest_start = position
                if length == MAX_MULTI_LENGTH:
                    break

        if longest_length >= MIN_MULTI_LENGTH:
            length_start = ((longest_start + WINDOW_START) % WINDOW_SIZE) | ((longest_length - MIN_MULTI_LENGTH) << 11)
            group.extend(list(length_start.to_bytes(2, "little")))
            data_index += longest_length
        else:
            control_byte = control_byte | control_bit
            group.append(data[data_index])
            data_index += 1

        control_bit <<= 1
        if control_bit > 0xff:
            result.append(control_byte)
            result.extend(group)
            control_byte = 0
            control_bit = 1
            group = []

    result.append(control_byte)
    result.extend(group)

    size = len(result) + 2
    if size > MAX_COMPRESS_SIZE:
        # a wrong size header would silently corrupt the decompressed data
        raise ValueError(f"compress: data too large (compressed size {size} > {MAX_COMPRESS_SIZE})")
    return list(size.to_bytes(2, "little")) + result

def decompress(data):
    window = [0] * WINDOW_SIZE
    window_index = WINDOW_START

    result = []
    data_index = 2 # first two bytes should be len(data)
    assert int.from_bytes(data[ : data_index], byteorder = "little") == len(data)
    while data_index < len(data):
        control_byte = data[data_index]
        data_index += 1

        control_bit = 1
        while control_bit <= 0xff and data_index < len(data):
            if control_bit & control_byte:
                # copy single value from data
                value = data[data_index]
                data_index += 1
                result.append(value)
                window[window_index] = value
                window_index = (window_index + 1) % WINDOW_SIZE
            else:
                # copy multiple values from window
                length_start = int.from_bytes(data[data_index : data_index + 2], byteorder = "little")
                data_index += 2

                length = (length_start >> 11) + MIN_MULTI_LENGTH
                start = length_start % WINDOW_SIZE
                for position in range(start, start + length):
                    value = window[position % WINDOW_SIZE]
                    result.append(value)
                    window[window_index] = value
                    window_index = (window_index + 1) % WINDOW_SIZE
            control_bit <<= 1
    return result

def splice_edit(stream, edits):
    """Edit specific decompressed-output bytes of a compressed stream WITHOUT
    recompressing it: every vanilla token is kept, except that matches whose
    output covers an edited offset are split so those bytes become literals
    (with the new value), and matches that would COPY an edited byte from the
    window are split so their bytes become literals pinned to the ORIGINAL
    values (the edit does not propagate).

    `edits` is {output_offset: new_byte_value}. Returns the new stream (with
    its 2-byte length header), verified to decompress to exactly the original
    output with only the requested bytes changed.

    Rationale: the game's decompressor accepts streams produced by the
    original compression tool, but streams recompressed from scratch by
    compress() above can crash it (cause undiagnosed -- discovered when a
    recompressed map tile set hard-crashed the map load, 2026-07). Splicing
    sidesteps that: all match tokens are vanilla-derived (or subranges of
    vanilla matches), which the game demonstrably decodes."""
    W, WS, MM = WINDOW_SIZE, WINDOW_START, MIN_MULTI_LENGTH
    original = decompress(stream)

    # parse tokens
    tokens = []
    i = 2
    while i < len(stream):
        control = stream[i]; i += 1
        bit = 1
        while bit <= 0xff and i < len(stream):
            if control & bit:
                tokens.append(('lit', stream[i])); i += 1
            else:
                ls = stream[i] | (stream[i + 1] << 8); i += 2
                tokens.append(('match', (ls % W, (ls >> 11) + MM)))
            bit <<= 1

    # window slots that will hold edited bytes (each output offset maps to a
    # unique slot for outputs < WINDOW_SIZE + anything -- one write per slot
    # within a single stream's first 2048 outputs)
    dirty_slots = set((WS + o) % W for o in edits)

    new_tokens = []
    out_off = 0
    for kind, val in tokens:
        if kind == 'lit':
            new_tokens.append(('lit', edits.get(out_off, val)))
            out_off += 1
            continue
        slot, length = val
        actions = []
        for j in range(length):
            o = out_off + j
            src = (slot + j) % W
            if o in edits:
                actions.append(('lit', edits[o]))
            elif src in dirty_slots:
                actions.append(('lit', original[o]))   # pin original value
            else:
                actions.append(('keep', src))
        j = 0
        while j < length:
            if actions[j][0] == 'keep':
                k = j
                while k < length and actions[k][0] == 'keep':
                    k += 1
                if k - j >= MM:
                    new_tokens.append(('match', ((slot + j) % W, k - j)))
                else:
                    for m in range(j, k):
                        new_tokens.append(('lit', original[out_off + m]))
                j = k
            else:
                new_tokens.append(('lit', actions[j][1]))
                j += 1
        out_off += length

    # serialize with control-byte packing
    result = []
    control = 0; bit = 1; group = []
    for kind, val in new_tokens:
        if kind == 'lit':
            control |= bit
            group.append(val)
        else:
            slot, length = val
            ls = slot | ((length - MM) << 11)
            group.extend(ls.to_bytes(2, "little"))
        bit <<= 1
        if bit > 0xff:
            result.append(control); result.extend(group)
            control = 0; bit = 1; group = []
    if bit > 1:
        result.append(control); result.extend(group)
    spliced = list((len(result) + 2).to_bytes(2, "little")) + result

    expected = list(original)
    for o, v in edits.items():
        expected[o] = v
    assert decompress(spliced) == expected, "splice_edit verification failed"
    return spliced
