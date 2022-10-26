import binascii
import lzma

# will decode valid lzma2 stream to bytes
# print(lzma.decompress(arcStream, format=lzma.FORMAT_RAW, filters=[{'id': lzma.FILTER_LZMA2}]))

# lzma.decompress(test, format=lzma.FORMAT_RAW, filters=[{'id': lzma.FILTER_LZMA1}])

# LZMA2 packet for 0xFF*10
# \xE0\x00\x0A\x00\x06\x5D\x00\x7F\xEB\xFC\x00\x00\x00\x00
# lzma.decompress(b'\xE0\x00\x0A\x00\x06\x5D\x00\x7F\xEB\xFC\x00\x00\x00\x00', format=lzma.FORMAT_RAW, filters=[{'id': lzma.FILTER_LZMA2}])

# LZMA1 data for 0xFF*10
# \x00\x7F\xEB\xFC\x00\x00\x00

def main():
    # infile = 'FF10.7z'
    # infile = 'broken.7z'
    infile = 'good.7z'
    
    with open(infile, 'rb') as f:
        arcBin = f.read()
    
    # verify magic header
    magicheader = arcBin[:6].hex().upper()
    if magicheader != '377ABCAF271C': raise Exception('Input file is not a valid .7z file')
    
    footerOffset = int.from_bytes(arcBin[12:20], 'little')+0x20
    arcStream = arcBin[0x20:footerOffset]
    
    i=1
    totalBytes=0
    packetOffset=0
    while True:
        print(f'\n{hex(packetOffset+0x20)}\t\t\tpacket {i}:')
        
        LZMA_STATE=None
        ORIG_CHUNK_SIZE=None
        COMPRESSED_CHUNK_SIZE=None
        PROPERTY_BYTE=None
        IS_LAST_BYTE=None
        IS_COMPRESSED=None
        
        # handle control byte
        if arcStream[packetOffset]==0:
            raise Exception('packet type LZMA1 or no data present')
        elif arcStream[packetOffset]>=3 and arcStream[0]<=0x7F:
            raise Exception('invalid lzma2 control-byte')       
        elif arcStream[packetOffset] in [1, 2]: # uncompressed chunk
            # 1==dict reset, 2!=dict reset
            IS_COMPRESSED=False
            
            ORIG_CHUNK_SIZE=arcStream[packetOffset+1]
            ORIG_CHUNK_SIZE<<=8
            ORIG_CHUNK_SIZE+=arcStream[packetOffset+2]
            ORIG_CHUNK_SIZE+=1 # size is stored -1
            
            totalBytes+=ORIG_CHUNK_SIZE
            
            packetEnd=packetOffset+2 # control byte + uint16 size
            packetEnd+=ORIG_CHUNK_SIZE
            
        elif arcStream[packetOffset]>=0x80: # compressed lzma2 chunk
            IS_COMPRESSED=True
            
            LZMA_STATE = (arcStream[packetOffset]&0b01100000)>>5 # 0-3
            # 0: nothing reset
            # 1: state reset
            # 2: state reset, properties reset using properties byte
            # 3: state reset, properties reset using properties byte, dictionary reset
            
            ORIG_CHUNK_SIZE = arcStream[packetOffset]&0b00011111
            ORIG_CHUNK_SIZE<<=8
            ORIG_CHUNK_SIZE+=arcStream[packetOffset+1]
            ORIG_CHUNK_SIZE<<=8
            ORIG_CHUNK_SIZE+=arcStream[packetOffset+2]
            ORIG_CHUNK_SIZE+=1 # size is stored -1
            
            totalBytes+=ORIG_CHUNK_SIZE
            
            COMPRESSED_CHUNK_SIZE=arcStream[packetOffset+3]
            COMPRESSED_CHUNK_SIZE<<=8
            COMPRESSED_CHUNK_SIZE+=arcStream[packetOffset+4]
            COMPRESSED_CHUNK_SIZE+=1 # the size is stored -1
            
            packetEnd = packetOffset+4 # control byte and compressed/uncompressed sizes
            packetEnd+=COMPRESSED_CHUNK_SIZE # plus the size of the actual chunk
            
            if LZMA_STATE>1:
                PROPERTY_BYTE = arcStream[packetOffset+5]
                packetEnd+=1
            
            
        IS_LAST_BYTE = len(arcStream)==packetEnd+1 # +1 for being 1 vs 0 indexed, +1 for block terminator byte
        
        ### check if the start of the lzma data is ever not 0
        
        print(f'uncompressed packet bytecount:\t{ORIG_CHUNK_SIZE} bytes')
        if COMPRESSED_CHUNK_SIZE!=None:
            print(f'compressed packet bytecount:\t{COMPRESSED_CHUNK_SIZE} bytes')
        else:
            print(f'compressed packet bytecount:\tN/A')
        if IS_COMPRESSED==False:
            print(f'packet state control flags:\tN/A')
        else:
            print(f'packet state control flags:\t{LZMA_STATE}    ({hex(arcStream[packetOffset])})')
        if PROPERTY_BYTE!=None: print(f'property state;\t\t\t{hex(PROPERTY_BYTE)}')
        else:  print(f'property state;\t\t\tN/A')
        
        # packetEnd is the end of the current packet
        # packetOffset is the start of the current packet
        
        # if arcStream[packetEnd] == 0: # should be terminator
            # print(f"Terminator seen! at {hex(packetOffset)}")
            # print(f'terminator for packet {i} was expected but not present ({hex(packetEnd+0x20)})')
            
            # print(f'original bytecount: {totalBytes} bytes')
            # raise Exception(f'Address {hex(packetEnd+0x20)} was not an expected null terminator byte')
        
        # print(hex(arcStream[packetOffset-3]))
        # print(hex(arcStream[packetOffset-2]))
        # print(hex(arcStream[packetOffset-1]))
        # print(hex(arcStream[packetOffset]))
        # print(hex(arcStream[packetOffset+1]))
        # print(hex(arcStream[packetOffset+2]))
        # print(hex(arcStream[packetOffset+3]))
        
        print(hex(packetEnd+0x20))
        packetEnd+=1 # add 1 to skip terminator ?
        packetOffset = packetEnd+=1
        if i>=31: break
        if IS_LAST_BYTE: break
        i+=1
        
    
    exit()
        
if __name__ == '__main__':
    main()
