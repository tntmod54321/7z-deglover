import sys
from os import listdir, makedirs, system, remove, rmdir
from os.path import isfile, isdir, splitext, split, join, exists

def printHelp():
    print("Usage:", "py 7zdeglover.py -i [INPUT FILE] -o [OUTPUT FILE]\n\n"+
    "Arguments:\n", "  -h, --help\tdisplay this usage info\n",
    "  -i, -I\tinput .7z file\n",
    "  -o, -O\toutput file\n",
    "  -X\t\toverwrite output file if exists\n")
    exit()

def main():
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
    
    # check outfile doesn't exist
    if exists(outfile) and not overwrite: raise Exception('Output file already exsists')
    
    # load file into mem, could stream but KEK
    with open(infile, 'rb') as f:
        inBin = f.read()
    
    magicheader = inBin[:6].hex().upper()
    if magicheader != '377ABCAF271C': raise Exception('Input file is not a .7z file')
    
    footerOffset = int.from_bytes(inBin[12:20], 'little')+0x20
    arcStream = inBin[0x20:footerOffset]
    
    with open(outfile, 'wb') as f:
        f.write(arcStream)
    print(f'wrote {infile} stream to {outfile}')
    
    return

if __name__=='__main__':
    main()
