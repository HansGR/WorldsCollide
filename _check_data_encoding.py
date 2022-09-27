# Short exits
decode = lambda data: [data[4], data[5], data[2] | (data[3] & 0x01) << 8, (data[3] & 0x02) >> 1, (data[3] & 0x04) >> 2, (data[3] & 0x08) >> 3, (data[3] & 0x30) >> 4, data[3] & 0xC0]
encode = lambda info: ['x', 'y', info[2] & 0xff, (((info[2] & 0x100) >> 8) | info[7]) | (info[3] << 1) | (info[4] << 2) | (info[5] << 3) | (info[6] << 4), info[0], info[1]]

# Long exits
decode_long = lambda data: [data[5], data[6], data[3] | (data[4] & 0x01) << 8, (data[4] & 0x02) >> 1, (data[4] & 0x04) >> 2, (data[4] & 0x08) >> 3, (data[4] & 0x30) >> 4, data[4] & 0xC0]
encode_long = lambda info: ['x', 'y', 'sd', info[2] & 0xff, (((info[2] & 0x100) >> 8) | info[7]) | (info[3] << 1) | (info[4] << 2) | (info[5] << 3) | (info[6] << 4), info[0], info[1]]

f = open('exit_original_info.txt','r')

nl = f.readline()
nl = f.readline()

while nl != '':
    #print(nl)

    # Parse the line:
    [exitID, nl] = nl.split(':')
    [originalData, nl] = nl.split('.')
    originalData = [int(i) for i in originalData[originalData.index('[')+1:-1].split(', ')]
    rawData = [int(i) for i in nl[nl.index('[')+1:-2].split(', ')]

    # Compare the encoded/decoded results
    if int(exitID) < 1129:
        # short exits
        reencode = encode(decode(rawData))
    else:
        # long exits
        reencode = encode_long(decode_long(rawData))

    if rawData[-4:] == reencode[-4:]:
        pass
        #print(exitID, ': pass')
    else:
        print(exitID, ': fail!', rawData, reencode, originalData)

    nl = f.readline()

f.close()