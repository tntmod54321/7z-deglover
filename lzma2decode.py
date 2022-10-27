import binascii
import lzma
import sys
import io

# update printhelp
def printHelp():
    print("Usage:", "py 7zdeglover.py -i [INPUT FILE] -o [OUTPUT FILE]\n\n"+
    "Arguments:\n", "  -h, --help\tdisplay this usage info\n",
    "  -i, -I\tinput .7z file\n",
    "  -o, -O\toutput file\n",
    "  -X\t\toverwrite output file if exists\n")
    exit()

# add footer offset for check?
def buildLZMA2Index(arcOBJ, blockEnd, blockOffset=0x20,
               doPrintout=True, breakAfterX=0):
    indicies=[]
    
    i=1
    totalBytes=0
    packetOffset=blockOffset
    while True:
        if doPrintout:
            print(f'\n{hex(packetOffset)}\t\t\tpacket {i}:')
        
        LZMA_STATE=None
        ORIG_CHUNK_SIZE=None
        COMPRESSED_CHUNK_SIZE=None
        PROPERTY_BYTE=None
        IS_LAST_PACKET=None
        IS_COMPRESSED=None
        IS_NULL_CTRL=False
        headerSize=1 # control byte
        PACKET_TYPE=None
        DICT_RESET=None
        LAST_BYTE=None
        packetEnd=None
        
        arcOBJ.seek(packetOffset)
        control_byte = arcOBJ.read(1)[0]
        
        # handle control byte
        if control_byte==0:
            IS_NULL_CTRL=True
        elif control_byte>=3 and control_byte<=0x7F:
            raise Exception('invalid lzma2 control-byte')       
        elif control_byte in [1, 2]: # uncompressed chunk
            if control_byte==1: DICT_RESET=True
            else: DICT_RESET=False
            IS_COMPRESSED=False
            headerSize+=2 # orig size uint16
            PACKET_TYPE="UNCOMPRESSED_LZMA2"
            
            ORIG_CHUNK_SIZE=arcOBJ.read(1)[0]
            ORIG_CHUNK_SIZE<<=8
            ORIG_CHUNK_SIZE+=arcOBJ.read(1)[0]
            ORIG_CHUNK_SIZE+=1 # size is stored -1
            
            totalBytes+=ORIG_CHUNK_SIZE
            
            packetEnd=packetOffset+2 # control byte + uint16 size
            packetEnd+=ORIG_CHUNK_SIZE
            
            arcOBJ.seek(packetEnd)
            LAST_BYTE=arcOBJ.read(1)[0]
            
        elif control_byte>=0x80: # compressed lzma2 chunk
            IS_COMPRESSED=True
            headerSize+=4 # compressed and orig uint16 sizes
            PACKET_TYPE="COMPRESSED_LZMA2"
            
            LZMA_STATE = (control_byte&0b01100000)>>5 # 0-3
            # 0: nothing reset
            # 1: state reset
            # 2: state reset, properties reset using properties byte
            # 3: state reset, properties reset using properties byte, dictionary reset
            
            ORIG_CHUNK_SIZE = control_byte&0b00011111
            ORIG_CHUNK_SIZE<<=8
            ORIG_CHUNK_SIZE+=arcOBJ.read(1)[0]
            ORIG_CHUNK_SIZE<<=8
            ORIG_CHUNK_SIZE+=arcOBJ.read(1)[0]
            ORIG_CHUNK_SIZE+=1 # the size is stored -1
            
            totalBytes+=ORIG_CHUNK_SIZE
            
            COMPRESSED_CHUNK_SIZE=arcOBJ.read(1)[0]
            COMPRESSED_CHUNK_SIZE<<=8
            COMPRESSED_CHUNK_SIZE+=arcOBJ.read(1)[0]
            COMPRESSED_CHUNK_SIZE+=1 # the size is stored -1
            
            packetEnd = packetOffset+4 # control byte and compressed/uncompressed sizes
            packetEnd+=COMPRESSED_CHUNK_SIZE # plus the size of the actual data
            
            if LZMA_STATE>1:
                PROPERTY_BYTE = arcOBJ.read(1)[0]
                packetEnd+=1
                headerSize+=1
            
            if LZMA_STATE==3: DICT_RESET=True
            else: DICT_RESET=False
            
            arcOBJ.seek(packetEnd)
            LAST_BYTE=arcOBJ.read(1)[0]
            
        IS_LAST_PACKET = blockEnd-packetEnd<=2
        if IS_NULL_CTRL and not IS_LAST_PACKET:
            raise Exception('packet type LZMA1 or no data present')
        
        nextPackStart=None
        if not IS_LAST_PACKET:
            arcOBJ.seek(packetEnd+1)
            nextPackStart=arcOBJ.read(1)[0]
        
        if doPrintout:
            packetTypeStr=f'packet type:\t\t\t{PACKET_TYPE}'
            if DICT_RESET: packetTypeStr+=', DICT_RESET'
            print(packetTypeStr)
            
            ctrlByteStr=""
            arcOBJ.seek(packetOffset)
            for byte in arcOBJ.read(headerSize):
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
                print(f'packet state control flags:\t{LZMA_STATE} ({bin(control_byte)})')
            if PROPERTY_BYTE!=None: print(f'property state;\t\t\t{hex(PROPERTY_BYTE)}')
            else:  print(f'property state;\t\t\tN/A')
            
            # if not arcBin[packetOffset+headerSize:packetOffset+headerSize+1]==b'\x00' and  IS_COMPRESSED:
                # raise Exception('Weird! lzma data starting with something other than 0x00')
            
            print('end of current packet is', hex(LAST_BYTE))
            if not IS_LAST_PACKET:
                print('start of next packet is', hex(nextPackStart))
            
            print(hex(packetEnd))
        
        packetMeta = {
            'index': i,
            'start': packetOffset,
            'end': packetEnd,
            
            'header_size': headerSize,
            'lzma_state': LZMA_STATE,
            'is_compressed': IS_COMPRESSED,
            'property_byte': PROPERTY_BYTE,
            
            'compressed_size': COMPRESSED_CHUNK_SIZE,
            'uncompressed_size': COMPRESSED_CHUNK_SIZE,
            
            'packet_type': PACKET_TYPE,
            'last_byte': LAST_BYTE,
            'dict_reset': DICT_RESET,
            'is_last_packet': IS_LAST_PACKET,
            'next_packet_start': nextPackStart,
        }
        
        indicies.append(packetMeta)
        
        if breakAfterX>0 and breakAfterX<=i: # make this return uh somethin else idk
            break
            # packetBin=arcBin[0x20:packetEnd+1]
            
            # decompData = lzma.decompress(packetBin+b'\x00\x00', format=lzma.FORMAT_RAW, filters=[{'id': lzma.FILTER_LZMA2}])
            # with open(outfile, 'wb') as f:
                # f.write(decompData)
        
        packetOffset = packetEnd+1
        if IS_LAST_PACKET: break
        i+=1
    
    if doPrintout:
        print(f'\n{totalBytes} bytes (uncompressed) total size indexed')
    
    return indicies, totalBytes

def main():
    infile=''
    outfile=''
    overwrite=False
    getPackets=False
    
    if len(sys.argv[1:]) == 0: printHelp()
    i=1 # for arguments like [--command value] get the value after the command
    # first arg in sys.argv is the python file
    for arg in sys.argv[1:]:
        if (arg in ["help", "/?", "-h", "--help"]): printHelp()
        if (arg in ["-i", "-I"]): infile = sys.argv[1:][i]
        if (arg in ["-o", "-O"]): outfile = sys.argv[1:][i]
        if (arg in ["-X"]): overwrite=True
        if (arg in ["-P"]): getPackets=True
        i+=1
    if '' in [infile, outfile]: printHelp()
    
    with open(infile, 'rb') as f:
        arcbuf = io.BufferedReader(f)
        
        # verify magic header
        if arcbuf.read(6) != bytes([0x37,0x7A,0xBC,0xAF,0x27,0x1C]):
            raise Exception('Input file is not a valid .7z file')
        
        ### we would handle metadata block / selecting which file to read here
        
        arcbuf.seek(12)
        footerOffset = int.from_bytes(arcbuf.read(8), 'little')+0x20 # footer offset is from the end of the header
        
        arcbuf.seek(0)
        index, x = buildLZMA2Index(arcbuf, footerOffset, doPrintout=getPackets, breakAfterX=0)
        if getPackets: exit()
        
        badBytes=0
        badPackets=0
        with open(outfile, 'wb') as o:
            outOBJ = io.BufferedWriter(o)
            
            # try except lzmaerror
            for packet in index:
                print(packet)
            
        # dasasdasdasd
    
    print('\nexiting...')
    exit()
        
if __name__ == '__main__':
    main()

### PRs welcome

### stream chunks to outfile, maybe stream in the infile?
### write undecodable data as 0xCD, printout ranges of bad data (mabey write to a doc alongside out file?)
### try except the whole while loop and if excepts we write 0s and continue (instantiating a try except thingy is expensive right?)

### read in bytes until next dict reset?

### maybe generate an index then attempt shit from that?
### try actually reading data from an arbitrary dict reset

### if block doesn't end with 00 we have to include the control byte for the next packet ?
### python lzma2 decoder est weird..

### this script is not at all the full extent of what is possible in terms of recovery
### should in theory be possible to find the problem byte by just observing the output and where it goes wrong
### (assuming it's a bit flip or something)
### should be easy with something like text or html, maybe not so much binary files but if it's something like
### a video or image file it might be possible to tell at which point invalid data appears
