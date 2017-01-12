# Isolyzer

## About

*Isolyzer* verifies if the file size of a CD / DVD ISO 9660 image is consistent with the information in its [Primary Volume Descriptor](http://wiki.osdev.org/ISO_9660#The_Primary_Volume_Descriptor). For [hybrid discs](https://en.wikipedia.org/wiki/Hybrid_disc) that contain both an ISO 9660 file system and an Apple partition, the expected file size is calculated using the information in the partition table (zero block) or the master directory block. This can be useful for detecting incomplete (e.g. truncated) ISO images. What the tool does is this:

1. Locate the image's Primary Volume Descriptor (PVD).
2. From the PVD, read the Volume Space Size (number of sectors/blocks) and Logical Block Size (number of bytes for each block) fields.
3. Calculate expected file size as ( Volume Space Size x Logical Block Size ).
4. If the image contains an Apple Partition Map, read the Block Size and Block Count fields from ['Block Zero'](https://en.wikipedia.org/wiki/Apple_Partition_Map#Layout)
5. Calculate expected file size as ( Block Size x Block Count )
6. If the image contains an Apple Master Directory Block, read its Block Size and Block Count fields
7. Calculate expected file size as ( Block Size x Block Count )
8. Calculate final expected file size as the largest value out of any of the above 3 values
9. Compare this against the actual size of the image files.

In addition to this, Isolyzer also extracts and reports technical metadata from the Primary Volume Descriptor and the Zero Block. 

In practice the following 3 situations can occur:

1. Actual size equals expected size (value of *tests/sizeAsExpected* in the output equals *True*) - perfect!
2. Actual size is smaller than expected size (value of *tests/sizeAsExpected* in the output equals *False*, and value of *test/smallerThanExpected* equals *True*): in this case the image is damaged or otherwise incomplete.
3. Actual size is (somewhat) larger than expected size (value of *tests/sizeAsExpected* in the output equals *False*, and value of *test/smallerThanExpected* equals *False*): this seems to be the case for the majority of ISO images on which I tested the tool. Not sure about the exact cause (padding bytes?), but this does not typically indicate a damaged image.

I wrote this tool after encountering [incomplete ISO images after running ddrescue](http://qanda.digipres.org/1076/incomplete-image-after-imaging-rom-prevent-and-detect-this) (most likely caused by some hardware issue), and subsequently discovering that [isovfy](http://manpages.ubuntu.com/manpages/hardy/man1/devdump.1.html) doesn't detect this at all (tried with version 1.1.11 on Linux Mint 17.1).

The code is largely based on the following documentation:

* <http://wiki.osdev.org/ISO_9660> - explanation of the ISO 9660 filesystem
* <https://en.wikipedia.org/wiki/Hybrid_disc> - Wikipedia entry on hybrid discs
* <https://opensource.apple.com/source/IOStorageFamily/IOStorageFamily-116/IOApplePartitionScheme.h> - Apple's code with Apple partitions and zero block definitions  
* <https://en.wikipedia.org/wiki/Apple_Partition_Map#Layout> - overview of Apple partition map
* <https://developer.apple.com/legacy/library/documentation/mac/Files/Files-102.html> - Apple documentation on Master Directory Block structure

## Limitations

* Behaviour with ISO files that use the [Universal Disk Format (UDF)](https://en.wikipedia.org/wiki/Universal_Disk_Format) file system has not been thoroughly tested yet (although preliminary tests on a limited number of video DVDs resulted in expected file size that were equal to the actual size in all cases). 
* No support (yet?) for HFS partitions that don't have a partition map (although they are detected)
* Also a correct file *size* alone does not guarantee the integrity of the image (for this there's not getting around running a checksum on both the image and the physical source medium).
* Other types of hybrid filesystems may exist (but I'm no aware of them, and the available documentation I could find about this is pretty limited)
* At this stage the tool is still somewhat experimental; use at your own peril!

## Installation

The easiest method to install Isolyzer is to use the [*pip* package manager](https://en.wikipedia.org/wiki/Pip_(package_manager)). You will need a recent version of *pip* (version 9.0 or more recent).

Before installing, you need to decide whether you want to install Isolyzer for a single user only, or do a global installation (that is: for all users). The main advantage of a single-user installation is thatn it doesn't require administrator (sudo) rights. The downside is that this will install the tool to a directory that is not included in the `PATH` environment variable by default, which means you'll have to do some (minor) configuration to make it work. A global installation will make Isolyzer usable without any configuration, but the downside is that you need administrator (sudo) rights. Both methods are explained below.

### Single user installation

Enter the following command:

   pip install isolyzer --user
   
This will install the software to the `.local` folder (hidden by default!) in your home directory (`~/.local`). Next try to run Isolyzer by entering:

     isolyzer

Most likely this will result in:

     isolyzer: command not found

If this happens, you will need to directory `~./local/bin` (which is where the Isolyzer command-line tool is installed) to the `PATH` environment variable (you only need to do this once). To do this, locate the (hidden) file `.profile` in you home directory (`~/`), and open it in a text editor. Then add the following lines at the end of the file:

    # set PATH so it includes the user's .local bin if it exists
    if [ -d "$HOME/.local/bin" ] ; then
        PATH="$HOME/.local/bin:$PATH"
    fi

Save the file, log out of your session and then log in again. Open a command terminal and type:

     isolyzer
     
If all went well you now see this:

    usage: isolyzer [-h] [--version] ISOImage
    isolyzer: error: too few arguments

Which means that the installation was successful!


### Global installation

Simply enter:

    sudo -H pip install isolyzer


No further configuration is needed in this case. 

## Upgrade Isolyzer to he latest version 

For a single user installation:

    pip install isolyzer -U --user

For a global installation:
    
    sudo -H pip install isolyzer -U

## Command line use

### Usage

    isolyzer [-h] [--version] ISOImage
    
### Positional arguments

`ISOImage` : input ISO image

### Optional arguments

`-h, --help` : show this help message and exit;

`-v, --version` : show program's version number and exit;

## Examples

(All files available in *testFiles* folder of this repo.) 

### Example 1: ISO image has expected size 

    isolyzer minimal.iso
    
Output:

    <isolyzer>
        <image>
            <fileInfo>
                <fileName>minimal.iso</fileName>
                <filePath>/home/johan/verifyISOSize/testFiles/minimal.iso</filePath>
                <fileSizeInBytes>358400</fileSizeInBytes>
                <fileLastModified>Thu Jan 12 12:48:49 2017</fileLastModified>
            </fileInfo>
            <statusInfo>
                <success>True</success>
            </statusInfo>
            <tests>
                <containsISO9660Signature>True</containsISO9660Signature>
                <containsApplePartitionMap>False</containsApplePartitionMap>
                <containsAppleHFSHeader>False</containsAppleHFSHeader>
                <containsAppleMasterDirectoryBlock>False</containsAppleMasterDirectoryBlock>
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

    isolyzer minimal_trunc.iso

Output:

    <isolyzer>
        <image>
            <fileInfo>
                <fileName>minimal_trunc.iso</fileName>
                <filePath>/home/johan/verifyISOSize/testFiles/minimal_trunc.iso</filePath>
                <fileSizeInBytes>49157</fileSizeInBytes>
                <fileLastModified>Thu Jan 12 13:01:00 2017</fileLastModified>
            </fileInfo>
            <statusInfo>
                <success>True</success>
            </statusInfo>
            <tests>
                <containsISO9660Signature>True</containsISO9660Signature>
                <containsApplePartitionMap>False</containsApplePartitionMap>
                <containsAppleHFSHeader>False</containsAppleHFSHeader>
                <containsAppleMasterDirectoryBlock>False</containsAppleMasterDirectoryBlock>
                <parsedPrimaryVolumeDescriptor>True</parsedPrimaryVolumeDescriptor>
                <sizeExpected>358400</sizeExpected>
                <sizeActual>49157</sizeActual>
                <sizeDifference>-309243</sizeDifference>
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

    isolyzer minimal_trunc_nopvd.iso
    
Output:

    <isolyzer>
        <image>
            <fileInfo>
                <fileName>minimal_trunc_nopvd.iso</fileName>
                <filePath>/home/johan/verifyISOSize/testFiles/minimal_trunc_nopvd.iso</filePath>
                <fileSizeInBytes>32860</fileSizeInBytes>
                <fileLastModified>Thu Jan 12 14:51:26 2017</fileLastModified>
            </fileInfo>
            <statusInfo>
                <success>True</success>
            </statusInfo>
            <tests>
                <containsISO9660Signature>False</containsISO9660Signature>
                <containsApplePartitionMap>False</containsApplePartitionMap>
                <containsAppleHFSHeader>False</containsAppleHFSHeader>
                <containsAppleMasterDirectoryBlock>False</containsAppleMasterDirectoryBlock>
                <parsedPrimaryVolumeDescriptor>False</parsedPrimaryVolumeDescriptor>
                <sizeExpected>0</sizeExpected>
                <sizeActual>32860</sizeActual>
                <sizeDifference>32860</sizeDifference>
                <sizeAsExpected>False</sizeAsExpected>
                <smallerThanExpected>False</smallerThanExpected>
            </tests>
            <properties/>
        </image>
    </isolyzer>


## License

Published under the [Apache 2.0](http://www.apache.org/licenses/LICENSE-2.0) license.