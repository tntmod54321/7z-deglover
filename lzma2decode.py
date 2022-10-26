import binascii
import lzma


def main():
    # infile = 'FF10.7z'
    infile = 'broken.7z'
    
    with open(infile, 'rb') as f:
        arcBin = f.read()
    
    magicheader = arcBin[:6].hex().upper()
    if magicheader != '377ABCAF271C': raise Exception('Input file is not a valid .7z file')
    
    footerOffset = int.from_bytes(arcBin[12:20], 'little')+0x20
    arcStream = arcBin[0x20:footerOffset]
    
    # will decode valid lzma2 stream to bytes
    # print(lzma.decompress(arcStream, format=lzma.FORMAT_RAW, filters=[{'id': lzma.FILTER_LZMA2}]))
    
    # lzma.decompress(test, format=lzma.FORMAT_RAW, filters=[{'id': lzma.FILTER_LZMA1}])
    
    if arcStream[0]==0: raise Exception('packet type LZMA1 or no data present')
    elif arcStream[0]==1: # dict reset followed by uncompressed chunk
        print('uncompressed data!')
    elif arcStream[0]==2: # uncompressed chunk w/o dict reset
        print('uncompressed data!')
    elif arcStream[0]>=3 and arcStream[0]<=0x7F:
        raise Exception('invalid lzma2 header control-byte ID')
    elif arcStream[0]>=0x80: # lzma2 chunk
        LZMA_STATE = arcStream[0]<<1>>7 # 0-3
        
        ORIG_CHUNK_SIZE = arcStream[0]&0b00011111
        ORIG_CHUNK_SIZE<<=8
        ORIG_CHUNK_SIZE+=arcStream[1]
        ORIG_CHUNK_SIZE<<=8
        ORIG_CHUNK_SIZE+=arcStream[2]
        ORIG_CHUNK_SIZE+=1 # size is stored -1
        # 0: nothing reset
        # 1: state reset
        # 2: state reset, properties reset using properties byte
        # 3: state reset, properties reset using properties byte, dictionary reset
        
        print(f'uncompressed packet bytecount:\t{ORIG_CHUNK_SIZE} bytes')
        print(f'packet state control flags:\t{LZMA_STATE}')
        
        # LZMA2 packet for 0xFF*10
        # \xE0\x00\x0A\x00\x06\x5D\x00\x7F\xEB\xFC\x00\x00\x00\x00
        # lzma.decompress(b'\xE0\x00\x0A\x00\x06\x5D\x00\x7F\xEB\xFC\x00\x00\x00\x00', format=lzma.FORMAT_RAW, filters=[{'id': lzma.FILTER_LZMA2}])
        
        # LZMA1 data for 0xFF*10
        # \x00\x7F\xEB\xFC\x00\x00\x00
        
        
        
        COMPRESSED_CHUNK_SIZE=arcStream[3]
        COMPRESSED_CHUNK_SIZE<<=8
        COMPRESSED_CHUNK_SIZE+=arcStream[4]
        COMPRESSED_CHUNK_SIZE+=1 # the size is stored -1
        print(f'compressed packet bytecount:\t{COMPRESSED_CHUNK_SIZE} bytes')
        
        PROPERTY_BYTE = None
        if LZMA_STATE>1:
            PROPERTY_BYTE = arcStream[5]
            print(f'property state byte present;\t{hex(PROPERTY_BYTE)}')
        
        # check if byte after property byte is always 0 (part of LZMA stream)
        # or if in it's used to designate an LZMA only packet to 7z but is used
        # when inside of an LZMA2 packet
        
        packet1end = 4 # control byte and compressed/uncompressed sizes
        if PROPERTY_BYTE!=None: packet1end+=1 # property byte if set
        packet1end+=COMPRESSED_CHUNK_SIZE # plus the size of the actual chunk
        
        if arcStream[packet1end] != 0: # should be terminator
            raise Exception(f'Address {hex(packet1end+0x20)} was not an expected null terminator byte')
        
        IS_LAST_BYTE = len(arcStream)==packet1end+2 # +1 for being 1 vs 0 indexed, +1 for block terminator byte
        
        if not IS_LAST_BYTE:
            
            print(f"second packet starting addr\t{hex(packet1end+1)}")
            
            print(hex(arcStream[packet1end-3]))
            print(hex(arcStream[packet1end-2]))
            print(hex(arcStream[packet1end-1]))
            print(hex(arcStream[packet1end]))
            print(hex(arcStream[packet1end+1]))
            print(hex(arcStream[packet1end+2]))
            print(hex(arcStream[packet1end+3]))
            
            # print(arcStream[0:1].hex())
            # print(arcStream[1:2].hex())
            # print(arcStream[2:3].hex())
            # print(arcStream[3:4].hex())
            # print(arcStream[4:5].hex())
            # print(arcStream[5:6].hex())
            # print(arcStream[6:7].hex())
            # print(arcStream[7:8].hex())
        
        exit()
        
        # uncompressed size is stored somehow, aswell as the dict size

if __name__ == '__main__':
    main()
