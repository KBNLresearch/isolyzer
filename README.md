# Isolyzer

## About

*Isolyzer* verifies if the file size of a CD / DVD ISO 9660 image is consistent with the information in its [Primary Volume Descriptor](http://wiki.osdev.org/ISO_9660#The_Primary_Volume_Descriptor). For [hybrid discs](https://en.wikipedia.org/wiki/Hybrid_disc) that contain both an ISO 9660 file system and an Apple partition, the file size is verified against the information in its partition table (zero block). This can be useful for detecting incomplete (e.g. truncated) ISO images. What the tool does is this:

1. Locate the image's Primary Volume Descriptor (PVD).
2. From the PVD, read the Volume Space Size (number of sectors/blocks) and Logical Block Size (number of bytes for each block) fields.
3. If the image contains an Apple Partition Map, read the Block Size and Block Count fields from ['Block Zero'](https://en.wikipedia.org/wiki/Apple_Partition_Map#Layout)
4. If the image contains an Apple Partition Map, calculate the expected file size as ( Block Size x Block Count ); otherwise calculate expected file size as ( Volume Space Size x Logical Block Size ).
5. Compare this against the actual size of the image files.

In practice the following 3 situations can occur:

1. Actual size equals expected size - perfect!
2. Actual size smaller than expected size: in this case the image is damaged or otherwise incomplete.
3. Actual size larger than expected size: this seems to be the case for many ISO images. Not sure about the exact cause (padding bytes?), but this does not typically indicate a damaged image.

I wrote this tool after encountering [incomplete ISO images after running ddrescue](http://qanda.digipres.org/1076/incomplete-image-after-imaging-rom-prevent-and-detect-this) (most likely caused by some hardware issue), and subsequently discovering that [isovfy](http://manpages.ubuntu.com/manpages/hardy/man1/devdump.1.html) doesn't detect this at all (tried with version 1.1.11 on Linux Mint 17.1).

## Limitations

* Behaviour with ISO files that use the [Universal Disk Format (UDF)](https://en.wikipedia.org/wiki/Universal_Disk_Format) file system has not been thoroughly tested yet (although preliminary tests on a limited number of video DVDs resulted in expected file size that were equal to the actual size in all cases). 
* No support (yet?) for HFS partitions that don't have a partition map (although they are detected)
* Also a correct file *size* alone does not guarantee the integrity of the image (for this there's not getting around running a checksum on both the image and the physical source medium).
* Other types of hybrid filesystems may exist (but I'm no aware of them, and the available documentation I could find about this is pretty limited)

## Installation

    pip install isolyzer

(May need super user privilige, in which case use `sudo pip install jpylyzer`)

To upgrade from a previous version:

    pip install isolyzer -U

## Command line use

### Usage

    isolyzer.py [-h] [--version] ISOImage
    
### Positional arguments

`ISOImage` : input ISO image

### Optional arguments

`-h, --help` : show this help message and exit;

`-v, --version` : show program's version number and exit;

## Examples

(All files available in *testFiles* folder of this repo.) 

### Example 1: ISO image has expected size 

    isolyzer.py minimal.iso
    
Output:

    <isolyzer>
        <image>
            <fileInfo>
                <fileName>minimal.iso</fileName>
                <filePath>/home/johan/verifyISOSize/testFiles/minimal.iso</filePath>
                <fileSizeInBytes>358400</fileSizeInBytes>
                <fileLastModified>Mon Sep  7 18:29:48 2015</fileLastModified>
            </fileInfo>
            <statusInfo>
                <success>True</success>
            </statusInfo>
            <tests>
                <containsISO9660Signature>True</containsISO9660Signature>
                <containsApplePartitionMap>False</containsApplePartitionMap>
                <containsAppleHFSHeader>False</containsAppleHFSHeader>
                <parsedPrimaryVolumeDescriptor>True</parsedPrimaryVolumeDescriptor>
                <sizeExpected>358400</sizeExpected>
                <sizeActual>358400</sizeActual>
                <sizeDifference>0</sizeDifference>
                <sizeAsExpected>True</sizeAsExpected>
                <smallerThanExpected>False</smallerThanExpected>
            </tests>
            <properties>
                <primaryVolumeDescriptor>
                    <typeCode>1</typeCode>
                    <standardIdentifier>CD001</standardIdentifier>
                    <version>1</version>
                    <systemIdentifier>LINUX</systemIdentifier>
                    <volumeIdentifier>CDROM</volumeIdentifier>
                    <volumeSpaceSize>175</volumeSpaceSize>
                    <volumeSetSize>1</volumeSetSize>
                    <volumeSequenceNumber>1</volumeSequenceNumber>
                    <logicalBlockSize>2048</logicalBlockSize>
                    <pathTableSize>10</pathTableSize>
                    <typeLPathTableLocation>19</typeLPathTableLocation>
                    <optionalTypeLPathTableLocation>0</optionalTypeLPathTableLocation>
                    <typeMPathTableLocation>21</typeMPathTableLocation>
                    <optionalTypeMPathTableLocation>0</optionalTypeMPathTableLocation>
                    <volumeSetIdentifier/>
                    <publisherIdentifier/>
                    <dataPreparerIdentifier/>
                    <applicationIdentifier>GENISOIMAGE ISO 9660/HFS FILESYSTEM CREATOR (C) 1993 E.YOUNGDALE (C) 1997-2006 J.PEARSON/J.SCHILLING (C) 2006-2007 CDRKIT TEAM</applicationIdentifier>
                    <copyrightFileIdentifier/>
                    <abstractFileIdentifier/>
                    <bibliographicFileIdentifier/>
                    <volumeCreationDateAndTime>2015/09/05, 17:45:07</volumeCreationDateAndTime>
                    <volumeModificationDateAndTime>2015/09/05, 17:45:07</volumeModificationDateAndTime>
                    <volumeExpirationDateAndTime>0/00/00, 00:00:00</volumeExpirationDateAndTime>
                    <volumeEffectiveDateAndTime>2015/09/05, 17:45:07</volumeEffectiveDateAndTime>
                    <fileStructureVersion>1</fileStructureVersion>
                </primaryVolumeDescriptor>
            </properties>
        </image>
    </isolyzer>

### Example 2: ISO image smaller than expected size

    isolyzer.py minimal_trunc.iso

Output:

    <isolyzer>
        <image>
            <fileInfo>
                <fileName>minimal_trunc.iso</fileName>
                <filePath>/home/johan/verifyISOSize/testFiles/minimal_trunc.iso</filePath>
                <fileSizeInBytes>91582</fileSizeInBytes>
                <fileLastModified>Mon Sep  7 18:29:48 2015</fileLastModified>
            </fileInfo>
            <statusInfo>
                <success>True</success>
            </statusInfo>
            <tests>
                <containsISO9660Signature>True</containsISO9660Signature>
                <containsApplePartitionMap>False</containsApplePartitionMap>
                <containsAppleHFSHeader>False</containsAppleHFSHeader>
                <parsedPrimaryVolumeDescriptor>True</parsedPrimaryVolumeDescriptor>
                <sizeExpected>358400</sizeExpected>
                <sizeActual>91582</sizeActual>
                <sizeDifference>-266818</sizeDifference>
                <sizeAsExpected>False</sizeAsExpected>
                <smallerThanExpected>True</smallerThanExpected>
            </tests>
            <properties>
                <primaryVolumeDescriptor>
                    <typeCode>1</typeCode>
                    <standardIdentifier>CD001</standardIdentifier>
                    <version>1</version>
                    <systemIdentifier>LINUX</systemIdentifier>
                    <volumeIdentifier>CDROM</volumeIdentifier>
                    <volumeSpaceSize>175</volumeSpaceSize>
                    <volumeSetSize>1</volumeSetSize>
                    <volumeSequenceNumber>1</volumeSequenceNumber>
                    <logicalBlockSize>2048</logicalBlockSize>
                    <pathTableSize>10</pathTableSize>
                    <typeLPathTableLocation>19</typeLPathTableLocation>
                    <optionalTypeLPathTableLocation>0</optionalTypeLPathTableLocation>
                    <typeMPathTableLocation>21</typeMPathTableLocation>
                    <optionalTypeMPathTableLocation>0</optionalTypeMPathTableLocation>
                    <volumeSetIdentifier/>
                    <publisherIdentifier/>
                    <dataPreparerIdentifier/>
                    <applicationIdentifier>GENISOIMAGE ISO 9660/HFS FILESYSTEM CREATOR (C) 1993 E.YOUNGDALE (C) 1997-2006 J.PEARSON/J.SCHILLING (C) 2006-2007 CDRKIT TEAM</applicationIdentifier>
                    <copyrightFileIdentifier/>
                    <abstractFileIdentifier/>
                    <bibliographicFileIdentifier/>
                    <volumeCreationDateAndTime>2015/09/05, 17:45:07</volumeCreationDateAndTime>
                    <volumeModificationDateAndTime>2015/09/05, 17:45:07</volumeModificationDateAndTime>
                    <volumeExpirationDateAndTime>0/00/00, 00:00:00</volumeExpirationDateAndTime>
                    <volumeEffectiveDateAndTime>2015/09/05, 17:45:07</volumeEffectiveDateAndTime>
                    <fileStructureVersion>1</fileStructureVersion>
                </primaryVolumeDescriptor>
            </properties>
        </image>
    </isolyzer>



### Example 3: ISO truncated before Primary Volume Descriptor

    isolyzer.py minimal_trunc_nopvd.iso
    
Output:

    <isolyzer>
        <image>
            <fileInfo>
                <fileName>minimal_trunc_nopvd.iso</fileName>
                <filePath>/home/johan/verifyISOSize/testFiles/minimal_trunc_nopvd.iso</filePath>
                <fileSizeInBytes>32860</fileSizeInBytes>
                <fileLastModified>Tue Jan 10 18:21:05 2017</fileLastModified>
            </fileInfo>
            <statusInfo>
                <success>True</success>
            </statusInfo>
            <tests>
                <containsISO9660Signature>False</containsISO9660Signature>
                <containsApplePartitionMap>False</containsApplePartitionMap>
                <containsAppleHFSHeader>False</containsAppleHFSHeader>
                <parsedPrimaryVolumeDescriptor>False</parsedPrimaryVolumeDescriptor>
            </tests>
            <properties/>
        </image>
    </isolyzer>


## License

Published under the [Apache 2.0](http://www.apache.org/licenses/LICENSE-2.0) license.