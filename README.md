# 7z deglover
 Attempt to decode a single-block LZMA2-compressed .7z file

# Usage
## No warranty provided, no support guaranteed.
```
Usage: py 7z_deglover.py -i [INPUT FILE] -o [OUTPUT FILE]

Arguments:
   -h, --help   display this usage info
   -i           input .7z file
   -o           output file
   -P           list packet debug information about the provided input file
   --skips      specify skips in hex-csv format for skipping corrupted data while decoding a packet, E.G. --skips 0xC261FC3E,0x10FE58DF0
```

# Infos
Works by indexing all of the LZMA2 packets and then skipping bad ones when decompressing, if the LZMA2 packet headers are damaged the user can specify locations to skip to.  

I wrote this to try to recover 14 corrupted and compressed MKV files, 9 had bit flips and the other 5 had small swathes of data zeroed-out.  
I was able to recover all 14 with this utility, less than 1MiB of data missing per recovered file, a lot better than only being able to extract 1/3 before 7zip would crash...

# Limitations
* doesn't attempt any LZMA1 repair
* doesn't currently support non-lzma2 compressed data (might be possible?)
* doesn't currently support archives with more than a single file inside

# Improvements
* Potentially repairing LZMA1 data where only a bit flip occured? may be possible to track down a problem to a single byte manually and attempt to correct it manually or by bruteforcing that byte until the packet passes the checksum (since one bad bit seems to affect the entire output of all of the data after it that approach should be viable...)  

* Should be possible to automatically find LZMA2 packets admidst zeroed-out data, by searching for packets that start with a compressed LZMA2 control-byte (0b111XXXXX), checking for a 00 to indicate the start of the LZMA1 stream, and verifying that the compressed-length uint16 value (plus 1) points to another valid LZMA2 header.

* Only reads one block/file; It's entirely possible to support extracting multiple blocks/files but when there's more than one file in the archive there's a metadata header/block/thing that has references to where all the data is, I just didn't implement reading it, the function to build the index of LZMA2 packets supports a custom offset. PRs welcome.

# Further references
7zip/LZMA2 info
https://www.7-zip.org/recover.html
https://www.nongnu.org/lzip/xz_inadequate.html#glossary
https://sourceforge.net/p/sevenzip/discussion/45798/thread/e34b4a1d/?page=3
https://en.wikipedia.org/wiki/Lempel%E2%80%93Ziv%E2%80%93Markov_chain_algorithm#LZMA2_format

LZMA decoders you could potentially use as a base for attempting more advanced recovery
https://ionescu007.github.io/minLZMA/
https://github.com/conor42/fast-LZMA2
https://github.com/gendx/LZMA-rs  
https://7-zip.org/sdk.html
