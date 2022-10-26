import binascii
import lzma

# will decode valid lzma2 stream to bytes
# print(lzma.decompress(arcStream[0x20:footerOffset], format=lzma.FORMAT_RAW, filters=[{'id': lzma.FILTER_LZMA2}]))

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
    
    i=1
    totalBytes=0
    packetOffset=0x20
    while True:
        print(f'\n{hex(packetOffset)}\t\t\tpacket {i}:')
        
        LZMA_STATE=None
        ORIG_CHUNK_SIZE=None
        COMPRESSED_CHUNK_SIZE=None
        PROPERTY_BYTE=None
        IS_LAST_BYTE=None
        IS_COMPRESSED=None
        IS_NULL_CTRL=False
        headerSize=1
        
        # handle control byte
        if arcBin[packetOffset]==0:
            IS_NULL_CTRL=True
        elif arcBin[packetOffset]>=3 and arcBin[packetOffset]<=0x7F:
            raise Exception('invalid lzma2 control-byte')       
        elif arcBin[packetOffset] in [1, 2]: # uncompressed chunk
            # 1==dict reset, 2!=dict reset
            IS_COMPRESSED=False
            headerSize+=2 # orig size uint16
            
            ORIG_CHUNK_SIZE=arcBin[packetOffset+1]
            ORIG_CHUNK_SIZE<<=8
            ORIG_CHUNK_SIZE+=arcBin[packetOffset+2]
            ORIG_CHUNK_SIZE+=1 # size is stored -1
            
            totalBytes+=ORIG_CHUNK_SIZE
            
            packetEnd=packetOffset+2 # control byte + uint16 size
            packetEnd+=ORIG_CHUNK_SIZE
            
        elif arcBin[packetOffset]>=0x80: # compressed lzma2 chunk
            IS_COMPRESSED=True
            headerSize+=4 # compressed and orig sizes
            
            LZMA_STATE = (arcBin[packetOffset]&0b01100000)>>5 # 0-3
            # 0: nothing reset
            # 1: state reset
            # 2: state reset, properties reset using properties byte
            # 3: state reset, properties reset using properties byte, dictionary reset
            
            ORIG_CHUNK_SIZE = arcBin[packetOffset]&0b00011111
            ORIG_CHUNK_SIZE<<=8
            ORIG_CHUNK_SIZE+=arcBin[packetOffset+1]
            ORIG_CHUNK_SIZE<<=8
            ORIG_CHUNK_SIZE+=arcBin[packetOffset+2]
            ORIG_CHUNK_SIZE+=1 # size is stored -1
            
            totalBytes+=ORIG_CHUNK_SIZE
            
            COMPRESSED_CHUNK_SIZE=arcBin[packetOffset+3]
            COMPRESSED_CHUNK_SIZE<<=8
            COMPRESSED_CHUNK_SIZE+=arcBin[packetOffset+4]
            COMPRESSED_CHUNK_SIZE+=1 # the size is stored -1
            
            packetEnd = packetOffset+4 # control byte and compressed/uncompressed sizes
            packetEnd+=COMPRESSED_CHUNK_SIZE # plus the size of the actual chunk
            
            if LZMA_STATE>1:
                PROPERTY_BYTE = arcBin[packetOffset+5]
                packetEnd+=1
                headerSize+=1
            
        ### this is actually fucking awful, we should check if we're near the end of
        ### the size of this block/stream from the metadata header but ig idfc,
        ### I'm only planning to support 1 files anyway
        IS_LAST_BYTE = len(arcBin[packetEnd+2:])<=len(arcBin[footerOffset:])
        if IS_NULL_CTRL and not IS_LAST_BYTE:
            raise Exception('packet type LZMA1 or no data present')
        
        ctrlByteStr=""
        for byte in arcBin[packetOffset:packetOffset+headerSize]:
            Byte = hex(byte)[2:].upper()+' ' # skip '0x'
            if len(Byte.strip())==1: Byte='0'+Byte
            ctrlByteStr+=Byte
        print(f'LZMA2 packet header:\t\t{ctrlByteStr}')
        
        print(f'uncompressed packet bytecount:\t{ORIG_CHUNK_SIZE} bytes')
        if COMPRESSED_CHUNK_SIZE!=None:
            print(f'compressed packet bytecount:\t{COMPRESSED_CHUNK_SIZE} bytes')
        else:
            print(f'compressed packet bytecount:\tN/A')
        if IS_COMPRESSED==False:
            print(f'packet state control flags:\tN/A')
        else:
            print(f'packet state control flags:\t{LZMA_STATE} ({bin(arcBin[packetOffset])})')
        if PROPERTY_BYTE!=None: print(f'property state;\t\t\t{hex(PROPERTY_BYTE)}')
        else:  print(f'property state;\t\t\tN/A')
        
        print(hex(packetEnd))
        
        # if arcBin[packetEnd] == 0: # should be terminator"
            # print(f"this packet is null terminated, {hex(packetEnd)}")
            # print(f'terminator for packet {i} was expected but not present ({hex(packetEnd+0x20)})')
            
            # print(f'original bytecount: {totalBytes} bytes')
            # raise Exception(f'Address {hex(packetEnd)} was not an expected null terminator byte')
        
        # print(hex(arcBin[packetOffset-3]))
        # print(hex(arcBin[packetOffset-2]))
        # print(hex(arcBin[packetOffset-1]))
        # print(hex(arcBin[packetOffset]))
        # print(hex(arcBin[packetOffset+1]))
        # print(hex(arcBin[packetOffset+2]))
        # print(hex(arcBin[packetOffset+3]))
        
        packetOffset = packetEnd+1
        # if i>=1: break
        if IS_LAST_BYTE: break
        i+=1
        
        ### check if the start of the lzma data is ever not 0
        ### make it properly detect the end of the file
    
    print('\nexiting...') ###
    exit()
        
if __name__ == '__main__':
    main()

### PRs welcome
