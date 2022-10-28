import binascii
import lzma
import sys
import io
from _lzma import LZMAError

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
               doPrintout=True, breakAfterX=0, skips=[]):
    indicies=[]
    
    i=1
    skip_i=0
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
        uncompressed_position=totalBytes
        
        arcOBJ.seek(packetOffset)
        control_byte = arcOBJ.read(1)[0]
        
        # handle control byte
        if control_byte==0:
            IS_NULL_CTRL=True
        elif control_byte>=3 and control_byte<=0x7F:
            raise Exception(f'invalid lzma2 control-byte {hex(control_byte)} at {hex(packetOffset)}')       
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
        
        try:
            IS_LAST_PACKET = blockEnd-packetEnd<=2
            if IS_NULL_CTRL and not IS_LAST_PACKET:
                raise Exception('packet type LZMA1 or no data present')
        except TypeError:
            if skip_i>=len(skips) or len(skips)==0:
                # skip to a specified address for the start of the next header
                raise Exception(f'Error reading lzma2 packet header at {hex(packetOffset)}, try specifying a skip? Use -P to printout packet debug info')
            print(f'using skip {skip_i} to skip from {hex(packetOffset)} to {hex(int(skips[skip_i], 16))}')
            packetOffset=int(skips[skip_i], 16)
            skip_i+=1
            continue
        
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
            'uncompressed_size': ORIG_CHUNK_SIZE,
            'uncompressed_position': uncompressed_position,
            
            'packet_type': PACKET_TYPE,
            'last_byte': LAST_BYTE,
            'dict_reset': DICT_RESET,
            'is_last_packet': IS_LAST_PACKET,
            'next_packet_start': nextPackStart,
        }
        
        indicies.append(packetMeta)
        
        if breakAfterX>0 and breakAfterX<=i: # make this return uh somethin else idk
            break
        
        packetOffset = packetEnd+1
        if IS_LAST_PACKET: break
        i+=1
    
    if doPrintout:
        print(f'\n{totalBytes} bytes (uncompressed) total size indexed')
    
    return indicies, totalBytes

def main():
    infile=''
    outfile=''
    skips=[]
    overwrite=False
    printPackets=False
    
    if len(sys.argv[1:]) == 0: printHelp()
    i=1 # for arguments like [--command value] get the value after the command
    # first arg in sys.argv is the python file
    for arg in sys.argv[1:]:
        if (arg in ["help", "/?", "-h", "--help"]): printHelp()
        if (arg in ["-i", "-I"]): infile = sys.argv[1:][i]
        if (arg in ["-o", "-O"]): outfile = sys.argv[1:][i]
        if (arg in ["-X"]): overwrite=True
        if (arg in ["-P"]): printPackets=True
        if (arg in ["--skips"]): skips = sys.argv[1:][i].split(',')
        i+=1
    if '' in [infile, outfile]: printHelp()
    
    if infile==outfile: raise Exception('Don\'t try to write to the same file you dolt.')
    
    with open(infile, 'rb') as f:
        arcbuf = io.BufferedReader(f)
        
        print('Verifying file type...')
        # verify magic header
        if arcbuf.read(6) != bytes([0x37,0x7A,0xBC,0xAF,0x27,0x1C]):
            raise Exception('Input file is not a valid .7z file')
        
        ### we would handle metadata block / selecting which file to read here
        
        arcbuf.seek(12)
        footerOffset = int.from_bytes(arcbuf.read(8), 'little')+0x20 # footer offset is from the end of the header
        
        print('Building LZMA2 index...')
        arcbuf.seek(0)
        packets, x = buildLZMA2Index(arcbuf, footerOffset, doPrintout=printPackets, breakAfterX=0, skips=skips)
        if printPackets: exit()
        
        # get list of runs of packets delimited by lzma dictionary resets
        i=0
        dictRuns=[]
        lastDictReset=0
        for packet in packets:
            workingRange=[lastDictReset, i]
            if packet['dict_reset'] or packet['is_last_packet']:
                lastDictReset=i
                if packet['is_last_packet']: workingRange[1]+=1
                dictRuns.append(workingRange)
            i+=1
        
        print('Decompressing input file to output file...')
        badPackets=[]
        with open(outfile, 'wb') as o:
            outOBJ = io.BufferedWriter(o)
            
            for run in dictRuns:
                runBuf=b''
                packetCache=[]
                
                # cache the packet binaries
                for packet in range(run[0], run[1]):
                    packet = packets[packet]
                    arcbuf.seek(packet['start'])
                    
                    packetCache.append(arcbuf.read(
                        packet['end'] - packet['start'] + 1))
                
                try:
                    runBuf = lzma.decompress(b''.join(packetCache)+b'\x00\x00', format=lzma.FORMAT_RAW, filters=[{'id': lzma.FILTER_LZMA2}])
                except LZMAError as e:
                    # format this runs packets into a format more suitable for attempting recovery
                    i=0
                    damagedPackets=[]
                    for packet in range(run[0], run[1]):
                        packet=packets[packet]
                        
                        packetBin = packetCache[i]
                        packetRunBin=packetCache[:i+1]
                        packetRunBin=b''.join(packetRunBin)
                        if not packet['is_compressed']:
                            packetBin = packetBin[3:] # cut out LZMA2 header (control byte + uint16 size)
                        
                        tempPacket={
                            'run_index': i,
                            'packetMeta': packet,
                            'packetBin': packetBin,
                            'packetRunBin': packetRunBin,
                            'damaged': None,
                        }
                        damagedPackets.append(tempPacket)
                        i+=1
                    
                    if len(badPackets)==0: # only print this once
                        print('damaged data found!\naffected packets:')
                    
                    # try to locate the damage
                    damaged_dict=False
                    for d in damagedPackets:
                        if damaged_dict: break
                        if d['packetMeta']['is_compressed']:
                            try:
                                lzma.decompress(d['packetRunBin']+b'\x00\x00', format=lzma.FORMAT_RAW, filters=[{'id': lzma.FILTER_LZMA2}])
                                d['damaged']=False
                            except LZMAError:
                                d['damaged']=True
                                # not sure how damaged blocks with property resests
                                # will affect shit
                                # if d['packetMeta']['dict_reset']: damaged_dict=True
                                if d['packetMeta']['lzma_state'] != 0: damaged_dict=True
                        else:
                            d['damaged']=False
                    
                    for d in damagedPackets:
                        # print(d['run_index'], d['damaged']) ###
                        print(d['packetMeta'])
                    
                    # get the index of the start of the damage,
                    # mark all packets as 'damaged' if a dict reset packet is damaged
                    damagedI=None
                    for d in damagedPackets:
                        if d['damaged']==True or damaged_dict:
                            damagedI=d['run_index']
                            break
                    
                    recoveryBuf=b''
                    # decode the data pre-damage
                    if not damaged_dict:
                        recoveryBuf+=lzma.decompress(
                            damagedPackets[:damagedI][-1:][0]['packetRunBin']+b'\x00\x00',
                            format=lzma.FORMAT_RAW, filters=[{'id': lzma.FILTER_LZMA2}]
                        )
                    
                    # fill in the blanks or copy uncompressed data
                    for dpak in damagedPackets[damagedI:]:
                        dpak['packetMeta']['damaged']=dpak['damaged']
                        badPackets.append(dpak['packetMeta'])
                        
                        if dpak['packetMeta']['is_compressed']:
                            recoveryBuf+=bytearray([0xCD]*dpak['packetMeta']['uncompressed_size'])
                        else:
                            recoveryBuf+=dpak['packetBin']
                    
                    runBuf = recoveryBuf
                    pass
                
                
                if len(runBuf)>0:
                    outOBJ.write(runBuf)
    
    print('\nReport:')
    badBytes=0
    for packet in badPackets:
        packeti=packet['index']
        outFstart=packet['uncompressed_position']
        outFend=packet['uncompressed_size']+outFstart
        if packet['is_compressed']:
            if packet['damaged']:
                print(f'compressed packet {packeti} was not readable - bytes {hex(outFstart)}-{hex(outFend)} of the output file were written as 0xCD.')
                badBytes+=packet['uncompressed_size']
            else:
                print(f'compressed packet {packeti} was in a run of damaged packets but was successfully decoded - bytes {hex(outFstart)}-{hex(outFend)} of the output file were written with this data.')
        else:
            print(f'uncompressed packet {packeti} was written as-is - bytes {hex(outFstart)}-{hex(outFend)} of the original file, this data has not been verified.')
    
    skippedBytes=0
    for skip in skips:
        skippedBytes+=int(skip, 16)
    
    print(f'{skippedBytes} bytes were skipped using --skips')
    print(f'In total {badBytes+skippedBytes} or more bytes are inaccurate to the original file ({round(badBytes/1024,2)}KiB)')
    
    print('\nFinished, exiting...')
    exit()

if __name__ == '__main__':
    main()


# packetBin=arcBin[0x20:packetEnd+1]
            
# decompData = lzma.decompress(packetBin+b'\x00\x00', format=lzma.FORMAT_RAW, filters=[{'id': lzma.FILTER_LZMA2}])
# with open(outfile, 'wb') as f:
    # f.write(decompData)


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

### add doc for print packets
### tested only w/ python 3.9.5 on windows 10
### the tool expects intact lzma2 packet headers, if they're damaged the
### tool will probably spaz out, those are fixable manually so might be a good thing

### tool will copy uncompressed blocks verbatim, without testing them in any way
### probably possible to recover dictionary from damaged dict reset packet

### can you read a block after a damaged one if there isn't a dict reset?
### answer: no, probably has some range thing, dk, I'm not using a custom lzma1 decoder

### pls write a tiny doc on lzma2 in the readme

### add an lzma2 packet size check

### if the lzma2 index fails building you should try to go in with a hex editor
### and manually change the address to point to the next packet

### -P to printout lzma2 packet headers for debug purposes

### --skips 0x500
### lpt: search 5D 00 (for properties byte+null)
### py ../7z-lzma2-recover/lzma2decode.py -i "2019-07-22 16-32-20_recovered.mkv.7z" -o "2019-07-22 16-32-20_recovered.mkv" --skips 0xBF3C2
