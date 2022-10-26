import binascii
import lzma


def main():
    # infile = 'FF10.7z'
    # infile = 'broken.7z'
    infile = 'good.7z'
    
    with open(infile, 'rb') as f:
        arcBin = f.read()
    
    magicheader = arcBin[:6].hex().upper()
    if magicheader != '377ABCAF271C': raise Exception('Input file is not a valid .7z file')
    
    footerOffset = int.from_bytes(arcBin[12:20], 'little')+0x20
    arcStream = arcBin[0x20:footerOffset]
    
    # will decode valid lzma2 stream to bytes
    # print(lzma.decompress(arcStream, format=lzma.FORMAT_RAW, filters=[{'id': lzma.FILTER_LZMA2}]))
    
    # lzma.decompress(test, format=lzma.FORMAT_RAW, filters=[{'id': lzma.FILTER_LZMA1}])
    packetOffset=0
    i=1
    totalBytes=0
    while True:
        if arcStream[packetOffset]==0: raise Exception('packet type LZMA1 or no data present')
        elif arcStream[packetOffset]==1: # dict reset followed by uncompressed chunk
            print('uncompressed data!')
        elif arcStream[packetOffset]==2: # uncompressed chunk w/o dict reset
            print('uncompressed data!')
        elif arcStream[packetOffset]>=3 and arcStream[0]<=0x7F:
            raise Exception('invalid lzma2 header control-byte ID')
        elif arcStream[packetOffset]>=0x80: # lzma2 chunk
            print(f'\npacket {i}:')
            
            LZMA_STATE = arcStream[packetOffset]<<1>>7 # 0-3
            
            ORIG_CHUNK_SIZE = arcStream[packetOffset]&0b00011111
            ORIG_CHUNK_SIZE<<=8
            ORIG_CHUNK_SIZE+=arcStream[packetOffset+1]
            ORIG_CHUNK_SIZE<<=8
            ORIG_CHUNK_SIZE+=arcStream[packetOffset+2]
            ORIG_CHUNK_SIZE+=1 # size is stored -1
            # 0: nothing reset
            # 1: state reset
            # 2: state reset, properties reset using properties byte
            # 3: state reset, properties reset using properties byte, dictionary reset
            totalBytes+=ORIG_CHUNK_SIZE
            print(f'uncompressed packet bytecount:\t{ORIG_CHUNK_SIZE} bytes')
            print(f'packet state control flags:\t{LZMA_STATE}')
            
            # LZMA2 packet for 0xFF*10
            # \xE0\x00\x0A\x00\x06\x5D\x00\x7F\xEB\xFC\x00\x00\x00\x00
            # lzma.decompress(b'\xE0\x00\x0A\x00\x06\x5D\x00\x7F\xEB\xFC\x00\x00\x00\x00', format=lzma.FORMAT_RAW, filters=[{'id': lzma.FILTER_LZMA2}])
            
            # LZMA1 data for 0xFF*10
            # \x00\x7F\xEB\xFC\x00\x00\x00
            
            COMPRESSED_CHUNK_SIZE=arcStream[packetOffset+3]
            COMPRESSED_CHUNK_SIZE<<=8
            COMPRESSED_CHUNK_SIZE+=arcStream[packetOffset+4]
            COMPRESSED_CHUNK_SIZE+=1 # the size is stored -1
            print(f'compressed packet bytecount:\t{COMPRESSED_CHUNK_SIZE} bytes')
            
            PROPERTY_BYTE = None
            if LZMA_STATE>1:
                PROPERTY_BYTE = arcStream[packetOffset+5]
                print(f'property state byte present;\t{hex(PROPERTY_BYTE)}')
            
            # check if byte after property byte is always 0 (part of LZMA stream)
            # or if in it's used to designate an LZMA only packet to 7z but is used
            # when inside of an LZMA2 packet
            
            packetEnd = packetOffset+4 # control byte and compressed/uncompressed sizes
            if PROPERTY_BYTE!=None: packetEnd+=1 # property byte if set
            packetEnd+=COMPRESSED_CHUNK_SIZE # plus the size of the actual chunk
            
            ### check if the start of the lzma data is ever not 0
            
            if arcStream[packetEnd] != 0: # should be terminator
                packetEnd-=1
                print(f'terminator for packet {i} was expected but not present')
                if PROPERTY_BYTE:
                    print(f'original bytecount: {totalBytes} bytes')
                    raise Exception(f'Address {hex(packetEnd+0x20)} was not an expected null terminator byte')
            
            IS_LAST_BYTE = len(arcStream)==packetEnd+1 # +1 for being 1 vs 0 indexed, +1 for block terminator byte
            
            if IS_LAST_BYTE: break
            if i>=10: break
            
            i+=1
            packetOffset = packetEnd+1 # skip terminator
            
            # if not IS_LAST_BYTE:
                
                # print(f"second packet starting addr\t{hex(packet1end+1+0x20)}")
                
                # print(hex(arcStream[packet1end+1]))
                # print(hex(arcStream[packet1end+2]))
                # print(hex(arcStream[packet1end+3]))
                # print(hex(arcStream[packet1end+4]))
                # print(hex(arcStream[packet1end+5]))
                # print(hex(arcStream[packet1end+6]))
                # print(hex(arcStream[packet1end+7]))
    
    exit()
        
if __name__ == '__main__':
    main()
