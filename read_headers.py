import binascii

def spaceify(hexStr):
    spaced=''
    if not (len(hexStr)/2).is_integer(): raise Exception('invalid input to spaceify()')
    
    for i in range(int(len(hexStr)/2)):
        spaced += hexStr[i*2:(i+1)*2]+' '
    if len(spaced)>0: spaced=spaced[:-1]
    
    return spaced

def reverse(crcInt):
    crcHex=int(crcInt)
    crc = ''
    lastItr=''
    
    print(binascii.hexlify(crcInt))
    
    # for i in range(int(len(crcHex)/2)):
        # spaced += hexStr[i*2:(i+1)*2]+' '
    
    
    return crc

def main():
    infile = 'FF10.7z'
    
    with open(infile, 'rb') as f:
        arcBin = f.read()
    
    magicheader = arcBin[:6].hex().upper()
    if magicheader != '377ABCAF271C': raise Exception('Input file is not a valid .7z file')
    print(f'{spaceify(magicheader)}\tFile has valid magic header')
    
    formatver = arcBin[6:8].hex().upper()
    print(f'{spaceify(formatver)}\t\t\tFormat version ({int.from_bytes(arcBin[6:8], "big")})')
    
    headerCRC = arcBin[8:12]
    realHeaderCRC=binascii.crc32(arcBin[12:32]).to_bytes(4, 'little')
    if headerCRC != realHeaderCRC: raise Exception('Header checksum doesn\'t match')
    readableHeaderCRC = bytearray(headerCRC)
    readableHeaderCRC.reverse()
    print(f'{spaceify(realHeaderCRC.hex().upper())}\t\t(Valid) header checksum ({readableHeaderCRC.hex().upper()})')
    
    footerOff = int.from_bytes(arcBin[12:20], 'little')
    realFooterOff=footerOff+32
    print(f'{spaceify(arcBin[12:20].hex().upper())} Footer offset ({footerOff} + 32 bytes)')
    
    footerLen = int.from_bytes(arcBin[20:28], 'little')
    print(f'{spaceify(arcBin[20:28].hex().upper())} Footer length ({footerLen} bytes)')
    
    footerCRC = arcBin[28:32]
    footerBin = arcBin[realFooterOff:realFooterOff+footerLen]
    realFooterCRC=binascii.crc32(footerBin).to_bytes(4, 'little')
    if footerCRC != realFooterCRC: raise Exception('Footer checksum doesn\'t match')
    readableFooterCRC = bytearray(footerCRC)
    readableFooterCRC.reverse()
    print(f'{spaceify(realFooterCRC.hex().upper())}\t\t(Valid) header checksum ({readableFooterCRC.hex().upper()})')
    
    if footerBin[:1]==b'\x01': print(f'{footerBin[:1].hex()}\t\t\tMetadata block in footer')
    elif footerBin[:1]==b'\x17': raise Exception('This script doesn\'t support archives containing multiple files!')
    else: raise Exception('Invalid footer type!')
    
    # filename encoded as utf-16
    print(footerBin.decode('utf-16'))
    
    fileCRC=footerBin[0x19:0x1D]
    readableFileCRC=bytearray(fileCRC)
    readableFileCRC.reverse()
    print(readableFileCRC.hex().upper())
    return

if __name__ == '__main__':
    main()
