# 7z deglover
 Attempt to decode a single-block LZMA2-compressed .7z file

# Usage; no warranty provided, no support guaranteed.
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

I wrote this to try to recover 14 corrupted and compressed MKV files, 9 had bit flips and the other 5 had small swathes of data zeroed-out, I was able to recover all 14 with this utility, with 60KiB-1MiB of data missing per recovered file, a lot better than only being able to extract 1/3 before 7zip would crash...

# Limitations
* doesn't attempt any LZMA1 repair
* doesn't currently support non-lzma2 compressed data (might be possible?)
* doesn't currently support archives with more than a single file inside

# Improvements
* Potentially repairing LZMA1 data where only a bit flip occured? may be possible to track down a problem to a single byte manually and attempt to correct it manually or by bruteforcing that byte until the packet passes the checksum (since one bad bit seems to affect the entire output of all of the data after it that approach should be viable...)  

* Should be possible to automatically find LZMA2 packets admidst zeroed-out data, by searching for packets that start with a compressed LZMA2 control-byte (0b111XXXXX), checking for a 00 to indicate the start of the LZMA1 stream, and verifying that the compressed-length uint16 value (plus 1) points to another valid LZMA2 header.

* Only reads one block/file; It's entirely possible to support extracting multiple blocks/files but when there's more than one file in the archive there's a metadata header/block/thing that has references to where all the data is, I just didn't implement reading it, the function to build the index of LZMA2 packets supports a custom offset. PRs welcome.

# LZMA2 crash course
2 blocks compressed with LZMA2 and LZMA1 using 7zip 19.00
LZMA2 = `E0 00 0A 00 06 5D 00 7F EB FC 00 00 00 00` == 0xFF*11
LZMA1 = `                  00 7F EB FC 00 00 00   ` == 0xFF*11 
That is the entirety of what makes up an LZMA2 packet AFAIK...
The wikipedia page has more info, but here goes: the first bit indicates that the packet is compressed (control bytes over >0x80 are), the 2 bits after that are flags for property resets and dict resets, the following 5 bits and 2 bytes are the size of the data uncompressed minus one, the 2 bytes after that are the size of the compressed stream minus one, and finally a properties byte if the upper of the 2 properties bits was set, of course following the data stream there is a termination byte.

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

# Example log
```
>py ../7z-lzma2-recover/7z_deglover.py -i "2019-07-22 19-22-27_recovered.mkv.7z" -o "_test.mkv" --skips 0xC261FC3E,0x10FE58DF0

Verifying file type...
Building LZMA2 index...
using skip 0 to skip from 0xc258f0d4 to 0xc261fc3e
using skip 1 to skip from 0x10fe23f10 to 0x10fe58df0
Decompressing input file to output file...
damaged data found!
affected packets:
{'index': 28333, 'start': 1596325187, 'end': 1596382540, 'header_size': 6, 'lzma_state': 3, 'is_compressed': True, 'property_byte': 93, 'compressed_size': 57348, 'uncompressed_size': 59344, 'uncompressed_position': 1769996288, 'packet_type': 'COMPRESSED_LZMA2', 'last_byte': 0, 'dict_reset': True, 'is_last_packet': False, 'next_packet_start': 128}
{'index': 28334, 'start': 1596382541, 'end': 1596439893, 'header_size': 5, 'lzma_state': 0, 'is_compressed': True, 'property_byte': None, 'compressed_size': 57348, 'uncompressed_size': 58458, 'uncompressed_position': 1770055632, 'packet_type': 'COMPRESSED_LZMA2', 'last_byte': 0, 'dict_reset': False, 'is_last_packet': False, 'next_packet_start': 128}
{'index': 28335, 'start': 1596439894, 'end': 1596497246, 'header_size': 5, 'lzma_state': 0, 'is_compressed': True, 'property_byte': None, 'compressed_size': 57348, 'uncompressed_size': 58463, 'uncompressed_position': 1770114090, 'packet_type': 'COMPRESSED_LZMA2', 'last_byte': 56, 'dict_reset': False, 'is_last_packet': False, 'next_packet_start': 128}
{'index': 28336, 'start': 1596497247, 'end': 1596554600, 'header_size': 5, 'lzma_state': 0, 'is_compressed': True, 'property_byte': None, 'compressed_size': 57349, 'uncompressed_size': 58456, 'uncompressed_position': 1770172553, 'packet_type': 'COMPRESSED_LZMA2', 'last_byte': 220, 'dict_reset': False, 'is_last_packet': False, 'next_packet_start': 128}
{'index': 28337, 'start': 1596554601, 'end': 1596611953, 'header_size': 5, 'lzma_state': 0, 'is_compressed': True, 'property_byte': None, 'compressed_size': 57348, 'uncompressed_size': 58469, 'uncompressed_position': 1770231009, 'packet_type': 'COMPRESSED_LZMA2', 'last_byte': 82, 'dict_reset': False, 'is_last_packet': False, 'next_packet_start': 128}
{'index': 28338, 'start': 1596611954, 'end': 1596669306, 'header_size': 5, 'lzma_state': 0, 'is_compressed': True, 'property_byte': None, 'compressed_size': 57348, 'uncompressed_size': 58475, 'uncompressed_position': 1770289478, 'packet_type': 'COMPRESSED_LZMA2', 'last_byte': 150, 'dict_reset': False, 'is_last_packet': False, 'next_packet_start': 128}
{'index': 28339, 'start': 1596669307, 'end': 1596726660, 'header_size': 5, 'lzma_state': 0, 'is_compressed': True, 'property_byte': None, 'compressed_size': 57349, 'uncompressed_size': 59392, 'uncompressed_position': 1770347953, 'packet_type': 'COMPRESSED_LZMA2', 'last_byte': 0, 'dict_reset': False, 'is_last_packet': False, 'next_packet_start': 128}
{'index': 28340, 'start': 1596726661, 'end': 1596784013, 'header_size': 5, 'lzma_state': 0, 'is_compressed': True, 'property_byte': None, 'compressed_size': 57348, 'uncompressed_size': 58466, 'uncompressed_position': 1770407345, 'packet_type': 'COMPRESSED_LZMA2', 'last_byte': 28, 'dict_reset': False, 'is_last_packet': False, 'next_packet_start': 128}
{'index': 28341, 'start': 1596784014, 'end': 1596841366, 'header_size': 5, 'lzma_state': 0, 'is_compressed': True, 'property_byte': None, 'compressed_size': 57348, 'uncompressed_size': 58454, 'uncompressed_position': 1770465811, 'packet_type': 'COMPRESSED_LZMA2', 'last_byte': 115, 'dict_reset': False, 'is_last_packet': False, 'next_packet_start': 128}
{'index': 28342, 'start': 1596841367, 'end': 1596898720, 'header_size': 5, 'lzma_state': 0, 'is_compressed': True, 'property_byte': None, 'compressed_size': 57349, 'uncompressed_size': 58472, 'uncompressed_position': 1770524265, 'packet_type': 'COMPRESSED_LZMA2', 'last_byte': 121, 'dict_reset': False, 'is_last_packet': False, 'next_packet_start': 128}
{'index': 28343, 'start': 1596898721, 'end': 1596956073, 'header_size': 5, 'lzma_state': 0, 'is_compressed': True, 'property_byte': None, 'compressed_size': 57348, 'uncompressed_size': 58443, 'uncompressed_position': 1770582737, 'packet_type': 'COMPRESSED_LZMA2', 'last_byte': 140, 'dict_reset': False, 'is_last_packet': False, 'next_packet_start': 128}
{'index': 28344, 'start': 1596956074, 'end': 1597013426, 'header_size': 5, 'lzma_state': 0, 'is_compressed': True, 'property_byte': None, 'compressed_size': 57348, 'uncompressed_size': 58473, 'uncompressed_position': 1770641180, 'packet_type': 'COMPRESSED_LZMA2', 'last_byte': 103, 'dict_reset': False, 'is_last_packet': False, 'next_packet_start': 128}
{'index': 28345, 'start': 1597013427, 'end': 1597070779, 'header_size': 5, 'lzma_state': 0, 'is_compressed': True, 'property_byte': None, 'compressed_size': 57348, 'uncompressed_size': 58483, 'uncompressed_position': 1770699653, 'packet_type': 'COMPRESSED_LZMA2', 'last_byte': 117, 'dict_reset': False, 'is_last_packet': False, 'next_packet_start': 128}
{'index': 28346, 'start': 1597070780, 'end': 1597128132, 'header_size': 5, 'lzma_state': 0, 'is_compressed': True, 'property_byte': None, 'compressed_size': 57348, 'uncompressed_size': 58455, 'uncompressed_position': 1770758136, 'packet_type': 'COMPRESSED_LZMA2', 'last_byte': 52, 'dict_reset': False, 'is_last_packet': False, 'next_packet_start': 128}
{'index': 28347, 'start': 1597128133, 'end': 1597185485, 'header_size': 5, 'lzma_state': 0, 'is_compressed': True, 'property_byte': None, 'compressed_size': 57348, 'uncompressed_size': 57530, 'uncompressed_position': 1770816591, 'packet_type': 'COMPRESSED_LZMA2', 'last_byte': 114, 'dict_reset': False, 'is_last_packet': False, 'next_packet_start': 128}
{'index': 28348, 'start': 1597185486, 'end': 1597242838, 'header_size': 5, 'lzma_state': 0, 'is_compressed': True, 'property_byte': None, 'compressed_size': 57348, 'uncompressed_size': 59419, 'uncompressed_position': 1770874121, 'packet_type': 'COMPRESSED_LZMA2', 'last_byte': 22, 'dict_reset': False, 'is_last_packet': False, 'next_packet_start': 128}
{'index': 28349, 'start': 1597242839, 'end': 1597300191, 'header_size': 5, 'lzma_state': 0, 'is_compressed': True, 'property_byte': None, 'compressed_size': 57348, 'uncompressed_size': 58470, 'uncompressed_position': 1770933540, 'packet_type': 'COMPRESSED_LZMA2', 'last_byte': 131, 'dict_reset': False, 'is_last_packet': False, 'next_packet_start': 128}
{'index': 28350, 'start': 1597300192, 'end': 1597352797, 'header_size': 5, 'lzma_state': 0, 'is_compressed': True, 'property_byte': None, 'compressed_size': 52601, 'uncompressed_size': 52854, 'uncompressed_position': 1770992010, 'packet_type': 'COMPRESSED_LZMA2', 'last_byte': 149, 'dict_reset': False, 'is_last_packet': False, 'next_packet_start': 224}
{'index': 57932, 'start': 3260207251, 'end': 3260264604, 'header_size': 6, 'lzma_state': 3, 'is_compressed': True, 'property_byte': 93, 'compressed_size': 57348, 'uncompressed_size': 60327, 'uncompressed_position': 3687841792, 'packet_type': 'COMPRESSED_LZMA2', 'last_byte': 0, 'dict_reset': True, 'is_last_packet': False, 'next_packet_start': 128}
{'index': 57933, 'start': 3260264605, 'end': 3260321958, 'header_size': 5, 'lzma_state': 0, 'is_compressed': True, 'property_byte': None, 'compressed_size': 57349, 'uncompressed_size': 59397, 'uncompressed_position': 3687902119, 'packet_type': 'COMPRESSED_LZMA2', 'last_byte': 0, 'dict_reset': False, 'is_last_packet': False, 'next_packet_start': 128}
{'index': 57934, 'start': 3260321959, 'end': 3260379311, 'header_size': 5, 'lzma_state': 0, 'is_compressed': True, 'property_byte': None, 'compressed_size': 57348, 'uncompressed_size': 58470, 'uncompressed_position': 3687961516, 'packet_type': 'COMPRESSED_LZMA2', 'last_byte': 97, 'dict_reset': False, 'is_last_packet': False, 'next_packet_start': 128}
{'index': 57935, 'start': 3260379312, 'end': 3260436664, 'header_size': 5, 'lzma_state': 0, 'is_compressed': True, 'property_byte': None, 'compressed_size': 57348, 'uncompressed_size': 60340, 'uncompressed_position': 3688019986, 'packet_type': 'COMPRESSED_LZMA2', 'last_byte': 35, 'dict_reset': False, 'is_last_packet': False, 'next_packet_start': 128}
{'index': 57936, 'start': 3260436665, 'end': 3260494017, 'header_size': 5, 'lzma_state': 0, 'is_compressed': True, 'property_byte': None, 'compressed_size': 57348, 'uncompressed_size': 60388, 'uncompressed_position': 3688080326, 'packet_type': 'COMPRESSED_LZMA2', 'last_byte': 124, 'dict_reset': False, 'is_last_packet': False, 'next_packet_start': 128}
{'index': 57937, 'start': 3260494018, 'end': 3260551370, 'header_size': 5, 'lzma_state': 0, 'is_compressed': True, 'property_byte': None, 'compressed_size': 57348, 'uncompressed_size': 59411, 'uncompressed_position': 3688140714, 'packet_type': 'COMPRESSED_LZMA2', 'last_byte': 187, 'dict_reset': False, 'is_last_packet': False, 'next_packet_start': 128}
{'index': 57938, 'start': 3260551371, 'end': 3260608723, 'header_size': 5, 'lzma_state': 0, 'is_compressed': True, 'property_byte': None, 'compressed_size': 57348, 'uncompressed_size': 57515, 'uncompressed_position': 3688200125, 'packet_type': 'COMPRESSED_LZMA2', 'last_byte': 0, 'dict_reset': False, 'is_last_packet': False, 'next_packet_start': 0}
{'index': 80972, 'start': 4560649873, 'end': 4560707226, 'header_size': 6, 'lzma_state': 3, 'is_compressed': True, 'property_byte': 93, 'compressed_size': 57348, 'uncompressed_size': 59362, 'uncompressed_position': 5059795048, 'packet_type': 'COMPRESSED_LZMA2', 'last_byte': 32, 'dict_reset': True, 'is_last_packet': False, 'next_packet_start': 128}
{'index': 80973, 'start': 4560707227, 'end': 4560764579, 'header_size': 5, 'lzma_state': 0, 'is_compressed': True, 'property_byte': None, 'compressed_size': 57348, 'uncompressed_size': 59403, 'uncompressed_position': 5059854410, 'packet_type': 'COMPRESSED_LZMA2', 'last_byte': 0, 'dict_reset': False, 'is_last_packet': False, 'next_packet_start': 128}
{'index': 80974, 'start': 4560764580, 'end': 4560821932, 'header_size': 5, 'lzma_state': 0, 'is_compressed': True, 'property_byte': None, 'compressed_size': 57348, 'uncompressed_size': 58466, 'uncompressed_position': 5059913813, 'packet_type': 'COMPRESSED_LZMA2', 'last_byte': 54, 'dict_reset': False, 'is_last_packet': False, 'next_packet_start': 128}
{'index': 80975, 'start': 4560821933, 'end': 4560879285, 'header_size': 5, 'lzma_state': 0, 'is_compressed': True, 'property_byte': None, 'compressed_size': 57348, 'uncompressed_size': 59441, 'uncompressed_position': 5059972279, 'packet_type': 'COMPRESSED_LZMA2', 'last_byte': 218, 'dict_reset': False, 'is_last_packet': False, 'next_packet_start': 128}
{'index': 80976, 'start': 4560879286, 'end': 4560936638, 'header_size': 5, 'lzma_state': 0, 'is_compressed': True, 'property_byte': None, 'compressed_size': 57348, 'uncompressed_size': 59411, 'uncompressed_position': 5060031720, 'packet_type': 'COMPRESSED_LZMA2', 'last_byte': 18, 'dict_reset': False, 'is_last_packet': False, 'next_packet_start': 128}
{'index': 80977, 'start': 4560936639, 'end': 4560993991, 'header_size': 5, 'lzma_state': 0, 'is_compressed': True, 'property_byte': None, 'compressed_size': 57348, 'uncompressed_size': 58462, 'uncompressed_position': 5060091131, 'packet_type': 'COMPRESSED_LZMA2', 'last_byte': 73, 'dict_reset': False, 'is_last_packet': False, 'next_packet_start': 128}
{'index': 80978, 'start': 4560993992, 'end': 4561051344, 'header_size': 5, 'lzma_state': 0, 'is_compressed': True, 'property_byte': None, 'compressed_size': 57348, 'uncompressed_size': 58483, 'uncompressed_position': 5060149593, 'packet_type': 'COMPRESSED_LZMA2', 'last_byte': 40, 'dict_reset': False, 'is_last_packet': False, 'next_packet_start': 128}
{'index': 80979, 'start': 4561051345, 'end': 4561108697, 'header_size': 5, 'lzma_state': 0, 'is_compressed': True, 'property_byte': None, 'compressed_size': 57348, 'uncompressed_size': 59417, 'uncompressed_position': 5060208076, 'packet_type': 'COMPRESSED_LZMA2', 'last_byte': 0, 'dict_reset': False, 'is_last_packet': False, 'next_packet_start': 128}
{'index': 80980, 'start': 4561108698, 'end': 4561166050, 'header_size': 5, 'lzma_state': 0, 'is_compressed': True, 'property_byte': None, 'compressed_size': 57348, 'uncompressed_size': 58468, 'uncompressed_position': 5060267493, 'packet_type': 'COMPRESSED_LZMA2', 'last_byte': 112, 'dict_reset': False, 'is_last_packet': False, 'next_packet_start': 128}
{'index': 80981, 'start': 4561166051, 'end': 4561223403, 'header_size': 5, 'lzma_state': 0, 'is_compressed': True, 'property_byte': None, 'compressed_size': 57348, 'uncompressed_size': 59433, 'uncompressed_position': 5060325961, 'packet_type': 'COMPRESSED_LZMA2', 'last_byte': 194, 'dict_reset': False, 'is_last_packet': False, 'next_packet_start': 128}
{'index': 80982, 'start': 4561223404, 'end': 4561280756, 'header_size': 5, 'lzma_state': 0, 'is_compressed': True, 'property_byte': None, 'compressed_size': 57348, 'uncompressed_size': 59440, 'uncompressed_position': 5060385394, 'packet_type': 'COMPRESSED_LZMA2', 'last_byte': 142, 'dict_reset': False, 'is_last_packet': False, 'next_packet_start': 128}
{'index': 80983, 'start': 4561280757, 'end': 4561338109, 'header_size': 5, 'lzma_state': 0, 'is_compressed': True, 'property_byte': None, 'compressed_size': 57348, 'uncompressed_size': 58485, 'uncompressed_position': 5060444834, 'packet_type': 'COMPRESSED_LZMA2', 'last_byte': 0, 'dict_reset': False, 'is_last_packet': False, 'next_packet_start': 128}
{'index': 80984, 'start': 4561338110, 'end': 4561395462, 'header_size': 5, 'lzma_state': 0, 'is_compressed': True, 'property_byte': None, 'compressed_size': 57348, 'uncompressed_size': 59421, 'uncompressed_position': 5060503319, 'packet_type': 'COMPRESSED_LZMA2', 'last_byte': 240, 'dict_reset': False, 'is_last_packet': False, 'next_packet_start': 128}
{'index': 80985, 'start': 4561395463, 'end': 4561452815, 'header_size': 5, 'lzma_state': 0, 'is_compressed': True, 'property_byte': None, 'compressed_size': 57348, 'uncompressed_size': 58484, 'uncompressed_position': 5060562740, 'packet_type': 'COMPRESSED_LZMA2', 'last_byte': 0, 'dict_reset': False, 'is_last_packet': False, 'next_packet_start': 0}
{'index': 96747, 'start': 5451953183, 'end': 5452010536, 'header_size': 6, 'lzma_state': 3, 'is_compressed': True, 'property_byte': 93, 'compressed_size': 57348, 'uncompressed_size': 58396, 'uncompressed_position': 5999096744, 'packet_type': 'COMPRESSED_LZMA2', 'last_byte': 0, 'dict_reset': True, 'is_last_packet': False, 'next_packet_start': 128}
{'index': 96748, 'start': 5452010537, 'end': 5452067889, 'header_size': 5, 'lzma_state': 0, 'is_compressed': True, 'property_byte': None, 'compressed_size': 57348, 'uncompressed_size': 58454, 'uncompressed_position': 5999155140, 'packet_type': 'COMPRESSED_LZMA2', 'last_byte': 222, 'dict_reset': False, 'is_last_packet': False, 'next_packet_start': 128}
{'index': 96749, 'start': 5452067890, 'end': 5452125242, 'header_size': 5, 'lzma_state': 0, 'is_compressed': True, 'property_byte': None, 'compressed_size': 57348, 'uncompressed_size': 59433, 'uncompressed_position': 5999213594, 'packet_type': 'COMPRESSED_LZMA2', 'last_byte': 52, 'dict_reset': False, 'is_last_packet': False, 'next_packet_start': 128}
{'index': 96750, 'start': 5452125243, 'end': 5452182595, 'header_size': 5, 'lzma_state': 0, 'is_compressed': True, 'property_byte': None, 'compressed_size': 57348, 'uncompressed_size': 58469, 'uncompressed_position': 5999273027, 'packet_type': 'COMPRESSED_LZMA2', 'last_byte': 0, 'dict_reset': False, 'is_last_packet': False, 'next_packet_start': 128}
{'index': 96751, 'start': 5452182596, 'end': 5452239948, 'header_size': 5, 'lzma_state': 0, 'is_compressed': True, 'property_byte': None, 'compressed_size': 57348, 'uncompressed_size': 58487, 'uncompressed_position': 5999331496, 'packet_type': 'COMPRESSED_LZMA2', 'last_byte': 218, 'dict_reset': False, 'is_last_packet': False, 'next_packet_start': 128}
{'index': 96752, 'start': 5452239949, 'end': 5452297301, 'header_size': 5, 'lzma_state': 0, 'is_compressed': True, 'property_byte': None, 'compressed_size': 57348, 'uncompressed_size': 60387, 'uncompressed_position': 5999389983, 'packet_type': 'COMPRESSED_LZMA2', 'last_byte': 106, 'dict_reset': False, 'is_last_packet': False, 'next_packet_start': 128}
{'index': 96753, 'start': 5452297302, 'end': 5452354654, 'header_size': 5, 'lzma_state': 0, 'is_compressed': True, 'property_byte': None, 'compressed_size': 57348, 'uncompressed_size': 58473, 'uncompressed_position': 5999450370, 'packet_type': 'COMPRESSED_LZMA2', 'last_byte': 0, 'dict_reset': False, 'is_last_packet': False, 'next_packet_start': 128}
{'index': 96754, 'start': 5452354655, 'end': 5452412007, 'header_size': 5, 'lzma_state': 0, 'is_compressed': True, 'property_byte': None, 'compressed_size': 57348, 'uncompressed_size': 58467, 'uncompressed_position': 5999508843, 'packet_type': 'COMPRESSED_LZMA2', 'last_byte': 0, 'dict_reset': False, 'is_last_packet': False, 'next_packet_start': 128}
{'index': 96755, 'start': 5452412008, 'end': 5452469360, 'header_size': 5, 'lzma_state': 0, 'is_compressed': True, 'property_byte': None, 'compressed_size': 57348, 'uncompressed_size': 58465, 'uncompressed_position': 5999567310, 'packet_type': 'COMPRESSED_LZMA2', 'last_byte': 0, 'dict_reset': False, 'is_last_packet': False, 'next_packet_start': 128}
{'index': 96756, 'start': 5452469361, 'end': 5452526713, 'header_size': 5, 'lzma_state': 0, 'is_compressed': True, 'property_byte': None, 'compressed_size': 57348, 'uncompressed_size': 58422, 'uncompressed_position': 5999625775, 'packet_type': 'COMPRESSED_LZMA2', 'last_byte': 16, 'dict_reset': False, 'is_last_packet': False, 'next_packet_start': 128}
{'index': 96757, 'start': 5452526714, 'end': 5452584066, 'header_size': 5, 'lzma_state': 0, 'is_compressed': True, 'property_byte': None, 'compressed_size': 57348, 'uncompressed_size': 57529, 'uncompressed_position': 5999684197, 'packet_type': 'COMPRESSED_LZMA2', 'last_byte': 0, 'dict_reset': False, 'is_last_packet': False, 'next_packet_start': 128}
{'index': 96758, 'start': 5452584067, 'end': 5452641419, 'header_size': 5, 'lzma_state': 0, 'is_compressed': True, 'property_byte': None, 'compressed_size': 57348, 'uncompressed_size': 60379, 'uncompressed_position': 5999741726, 'packet_type': 'COMPRESSED_LZMA2', 'last_byte': 246, 'dict_reset': False, 'is_last_packet': False, 'next_packet_start': 128}
{'index': 96759, 'start': 5452641420, 'end': 5452698772, 'header_size': 5, 'lzma_state': 0, 'is_compressed': True, 'property_byte': None, 'compressed_size': 57348, 'uncompressed_size': 60382, 'uncompressed_position': 5999802105, 'packet_type': 'COMPRESSED_LZMA2', 'last_byte': 249, 'dict_reset': False, 'is_last_packet': False, 'next_packet_start': 128}
{'index': 96760, 'start': 5452698773, 'end': 5452756125, 'header_size': 5, 'lzma_state': 0, 'is_compressed': True, 'property_byte': None, 'compressed_size': 57348, 'uncompressed_size': 58460, 'uncompressed_position': 5999862487, 'packet_type': 'COMPRESSED_LZMA2', 'last_byte': 198, 'dict_reset': False, 'is_last_packet': False, 'next_packet_start': 128}
{'index': 96761, 'start': 5452756126, 'end': 5452813478, 'header_size': 5, 'lzma_state': 0, 'is_compressed': True, 'property_byte': None, 'compressed_size': 57348, 'uncompressed_size': 58469, 'uncompressed_position': 5999920947, 'packet_type': 'COMPRESSED_LZMA2', 'last_byte': 5, 'dict_reset': False, 'is_last_packet': False, 'next_packet_start': 2}
{'index': 96762, 'start': 5452813479, 'end': 5452870045, 'header_size': 3, 'lzma_state': None, 'is_compressed': False, 'property_byte': None, 'compressed_size': None, 'uncompressed_size': 56564, 'uncompressed_position': 5999979416, 'packet_type': 'UNCOMPRESSED_LZMA2', 'last_byte': 50, 'dict_reset': False, 'is_last_packet': False, 'next_packet_start': 2}
{'index': 96763, 'start': 5452870046, 'end': 5452926602, 'header_size': 3, 'lzma_state': None, 'is_compressed': False, 'property_byte': None, 'compressed_size': None, 'uncompressed_size': 56554, 'uncompressed_position': 6000035980, 'packet_type': 'UNCOMPRESSED_LZMA2', 'last_byte': 220, 'dict_reset': False, 'is_last_packet': False, 'next_packet_start': 128}
{'index': 96764, 'start': 5452926603, 'end': 5452979184, 'header_size': 5, 'lzma_state': 0, 'is_compressed': True, 'property_byte': None, 'compressed_size': 52577, 'uncompressed_size': 52786, 'uncompressed_position': 6000092534, 'packet_type': 'COMPRESSED_LZMA2', 'last_byte': 151, 'dict_reset': False, 'is_last_packet': False, 'next_packet_start': 224}

Report:
compressed packet 28350 was not readable - bytes 0x698f318a-0x69900000 of the output file were written as 0xCD.
compressed packet 57938 was not readable - bytes 0xdbd577bd-0xdbd65868 of the output file were written as 0xCD.
compressed packet 80985 was not readable - bytes 0x12da20f34-0x12da2f3a8 of the output file were written as 0xCD.
compressed packet 96752 was not readable - bytes 0x165976d1f-0x165985902 of the output file were written as 0xCD.
compressed packet 96753 was not readable - bytes 0x165985902-0x165993d6b of the output file were written as 0xCD.
compressed packet 96754 was not readable - bytes 0x165993d6b-0x1659a21ce of the output file were written as 0xCD.
compressed packet 96755 was not readable - bytes 0x1659a21ce-0x1659b062f of the output file were written as 0xCD.
compressed packet 96756 was not readable - bytes 0x1659b062f-0x1659bea65 of the output file were written as 0xCD.
compressed packet 96757 was not readable - bytes 0x1659bea65-0x1659ccb1e of the output file were written as 0xCD.
compressed packet 96758 was not readable - bytes 0x1659ccb1e-0x1659db6f9 of the output file were written as 0xCD.
compressed packet 96759 was not readable - bytes 0x1659db6f9-0x1659ea2d7 of the output file were written as 0xCD.
compressed packet 96760 was not readable - bytes 0x1659ea2d7-0x1659f8733 of the output file were written as 0xCD.
compressed packet 96761 was not readable - bytes 0x1659f8733-0x165a06b98 of the output file were written as 0xCD.
uncompressed packet 96762 was written as-is - bytes 0x165a06b98-0x165a1488c of the original file, this data has not been verified.
uncompressed packet 96763 was written as-is - bytes 0x165a1488c-0x165a22576 of the original file, this data has not been verified.
compressed packet 96764 was not readable - bytes 0x165a22576-0x165a2f3a8 of the output file were written as 0xCD.
Some bytes were skipped using --skips
In total 811072 or more bytes are inaccurate to the original file (792.00KiB)

Finished, exiting...
```
