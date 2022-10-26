import binascii
import lzma
import sys

# update printhelp
def printHelp():
    print("Usage:", "py 7zdeglover.py -i [INPUT FILE] -o [OUTPUT FILE]\n\n"+
    "Arguments:\n", "  -h, --help\tdisplay this usage info\n",
    "  -i, -I\tinput .7z file\n",
    "  -o, -O\toutput file\n",
    "  -X\t\toverwrite output file if exists\n")
    exit()

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
    # infile = 'good.7z'
    
    overwrite=False
    infile=''
    outfile=''
    
    if len(sys.argv[1:]) == 0: printHelp()
    i=1 # for arguments like [--command value] get the value after the command
    # first arg in sys.argv is the python file
    for arg in sys.argv[1:]:
        if (arg in ["help", "/?", "-h", "--help"]): printHelp()
        if (arg in ["-i", "-I"]): infile = sys.argv[1:][i]
        if (arg in ["-o", "-O"]): outfile = sys.argv[1:][i]
        if (arg in ["-X"]): overwrite=True
        i+=1
    if '' in [infile, outfile]: printHelp()
    
    with open(infile, 'rb') as f:
        arcBin = f.read()
    
    # verify magic header
    magicheader = arcBin[:6].hex().upper()
    if magicheader != '377ABCAF271C': raise Exception('Input file is not a valid .7z file')
    
    footerOffset = int.from_bytes(arcBin[12:20], 'little')+0x20
    
    i=1
    badBytes=0 ### use deez prease
    badChunks=0 ###
    totalBytes=0
    packetOffset=0x20
    while True:
        print(f'\n{hex(packetOffset)}\t\t\tpacket {i}:')
        
        LZMA_STATE=None
        ORIG_CHUNK_SIZE=None
        COMPRESSED_CHUNK_SIZE=None
        PROPERTY_BYTE=None
        IS_LAST_CHUNK=None
        IS_COMPRESSED=None
        IS_NULL_CTRL=False
        headerSize=1
        PACKET_TYPE=None
        DICT_RESET=None
        
        # handle control byte
        if arcBin[packetOffset]==0:
            IS_NULL_CTRL=True
        elif arcBin[packetOffset]>=3 and arcBin[packetOffset]<=0x7F:
            raise Exception('invalid lzma2 control-byte')       
        elif arcBin[packetOffset] in [1, 2]: # uncompressed chunk
            if arcBin[packetOffset]==1: DICT_RESET=True
            else: DICT_RESET=False
            IS_COMPRESSED=False
            headerSize+=2 # orig size uint16
            PACKET_TYPE="UNCOMPRESSED_LZMA2"
            
            ORIG_CHUNK_SIZE=arcBin[packetOffset+1]
            ORIG_CHUNK_SIZE<<=8
            ORIG_CHUNK_SIZE+=arcBin[packetOffset+2]
            ORIG_CHUNK_SIZE+=1 # size is stored -1
            
            totalBytes+=ORIG_CHUNK_SIZE
            
            packetEnd=packetOffset+2 # control byte + uint16 size
            packetEnd+=ORIG_CHUNK_SIZE
            
        elif arcBin[packetOffset]>=0x80: # compressed lzma2 chunk
            IS_COMPRESSED=True
            headerSize+=4 # compressed and orig uint16 sizes
            PACKET_TYPE="COMPRESSED_LZMA2"
            
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
            ORIG_CHUNK_SIZE+=1 # the size is stored -1
            
            totalBytes+=ORIG_CHUNK_SIZE
            
            COMPRESSED_CHUNK_SIZE=arcBin[packetOffset+3]
            COMPRESSED_CHUNK_SIZE<<=8
            COMPRESSED_CHUNK_SIZE+=arcBin[packetOffset+4]
            COMPRESSED_CHUNK_SIZE+=1 # the size is stored -1
            
            packetEnd = packetOffset+4 # control byte and compressed/uncompressed sizes
            packetEnd+=COMPRESSED_CHUNK_SIZE # plus the size of the actual data
            
            if LZMA_STATE>1:
                PROPERTY_BYTE = arcBin[packetOffset+5]
                packetEnd+=1
                headerSize+=1
            
            if LZMA_STATE==3: DICT_RESET=True
            else: DICT_RESET=False
            
        ### this is actually fucking awful, we should check if we're near the end of
        ### the size of this block/stream from the metadata header but ig idfc,
        ### I'm only planning to support 1 files recovery anyway
        IS_LAST_CHUNK = footerOffset-packetEnd<=2
        if IS_NULL_CTRL and not IS_LAST_CHUNK:
            raise Exception('packet type LZMA1 or no data present')
        
        packetTypeStr=f'packet type:\t\t\t{PACKET_TYPE}'
        if DICT_RESET: packetTypeStr+=', DICT_RESET'
        print(packetTypeStr)
        
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
        
        ### take contents :>
        
        if i>=12:
            packetBin=arcBin[0x20:packetEnd]
            print(len(packetBin))
            decompData = lzma.decompress(packetBin+b'\x00\x00', format=lzma.FORMAT_RAW, filters=[{'id': lzma.FILTER_LZMA2}])
            with open(outfile, 'wb') as f:
                f.write(decompData)
            exit()    
        
        packetOffset = packetEnd+1
        # if i>=10: break
        if IS_LAST_CHUNK: break
        i+=1
        
    print('\nexiting...') ###
    exit()
        
if __name__ == '__main__':
    main()

### PRs welcome

### add sys arg command parsing owo
### check if the start of the lzma data is ever not 0

### stream chunks to outfile, maybe stream in the infile?
### write undecodable data as 0xCD, printout ranges of bad data (mabey write to a doc alongside out file?)
### try except the whole while loop and if excepts we write 0s and continue (instantiating a try except thingy is expensive right?)

### read in bytes until next dict reset?
