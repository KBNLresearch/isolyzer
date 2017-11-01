# Isolyzer

## About

*Isolyzer* verifies if the file size of a CD / DVD image ("ISO image") is consistent with the information in its filesystem-level headers. The following file systems are supported:

* [ISO 9660](https://en.wikipedia.org/wiki/ISO_9660)
* [Universal Disk Format](https://en.wikipedia.org/wiki/Universal_Disk_Format) (UDF)
* Apple [Hierarchical File System](https://en.wikipedia.org/wiki/Hierarchical_File_System) (HFS)
* Apple [HFS+](https://en.wikipedia.org/wiki/HFS_Plus)
* [Hybrids](https://en.wikipedia.org/wiki/Hybrid_disc) of the above file systems, e.g. ISO 9660 + HFS; UDF Bridge (UDF + ISO 9660)

Isolyzer uses the information in the filesystem-level headers to calculate the expected file size (typically based on a block size field and a number of blocks field). This is then compared against the actual file size, which can be useful for detecting incomplete (e.g. truncated) ISO images. Isolyzer also extracts and reports some technical metadata from the filesystem-level headers.

## Installation

The easiest method to install Isolyzer is to use the [*pip* package manager](https://en.wikipedia.org/wiki/Pip_(package_manager)). You will need a recent version of *pip* (version 9.0 or more recent). Alternatively, Windows users can also use stand-alone binaries that don't require Python (see below).

## Installation with pip 

Before installing, you need to decide whether you want to install Isolyzer for a single user only, or do a global installation (that is: for all users). The main advantage of a single-user installation is thatn it doesn't require administrator (sudo) rights. The downside is that this will install the tool to a directory that is not included in the `PATH` environment variable by default, which means you'll have to do some (minor) configuration to make it work. A global installation will make Isolyzer usable without any configuration, but the downside is that you need administrator (sudo) rights. Both methods are explained below.

### Single user installation (Linux)

Enter the following command:

    pip install isolyzer --user
   
This will install the software to the `.local` folder (hidden by default!) in your home directory (`~/.local`). Next try to run Isolyzer by entering:

    isolyzer

Most likely this will result in:

    isolyzer: command not found

If this happens, you will need to add the directory `~/.local/bin` (which is where the Isolyzer command-line tool is installed) to the `PATH` environment variable (you only need to do this once). To do this, locate the (hidden) file `.profile` in you home directory (`~/`), and open it in a text editor. Then add the following lines at the end of the file:

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


### Global installation (Linux)

Simply enter:

    sudo -H pip install isolyzer


No further configuration is needed in this case. 

### Note on pre-releases

The above command lines will only install stable versions of isolyzer. In order to install the latest pre-release, add the `--pre` switch. For example:

    sudo -H pip install isolyzer --pre


## Installation from stand-alone binaries (Windows)

Go to the *release* page of Isolyzer's Github repo: 

<https://github.com/KBNLresearch/isolyzer/releases>

Then download the file 'isolyzer_x_y_z_win32.zip' from the most recent release. Unzip the file to whatever location on your machine you like. You'll now be able to run Isolyzer from a command window by entering 'isolyzer', including its full path. For example, if you extracted the zip file isolyzer_0_2_0_win32.zip' to directory 'c:\test', you have to enter:

    c:\test\isolyzer_0_2_0_win32\isolyzer
    
## Upgrade Isolyzer to the latest version 

If you installed with pip, enter this for a single user installation:

    pip install isolyzer -U --user

For a global installation:
    
    sudo -H pip install isolyzer -U

If you installed from the Windows binaries, repeat the instructions from the 'Installation from stand-alone binaries' section above (you may want to remove the old installation manually).
    
## Command line use

### Usage

    isolyzer [-h] [--version] [--offset SECTOROFFSET] ISOImage
    
### Positional arguments

`ISOImage` : input ISO image

### Optional arguments

`-h, --help` : show this help message and exit;

`-v, --version` : show program's version number and exit;

`--offset SECTOROFFSET`, `-o SECTOROFFSET` : offset (in sectors) of ISO image on CD (analogous to *-N* option in cdinfo; only affects size calculation for ISO 9660 file systems)

## Calculation of the expected file size

### ISO 9660

For an ISO 9660 file system, Isolyzer locates and parses its [Primary Volume Descriptor](http://wiki.osdev.org/ISO_9660#The_Primary_Volume_Descriptor) (PVD). From the PVD it 2. From the PVD it then reads the *Volume Space Size* field (which denotes the number of sectors/blocks in the image) and the *Logical Block Size* field (the number of bytes for each block). The expected file size is then calculated as:

*SizeExpectedISO* =  (*Volume Space Size* - *Offset*) x *Logical Block Size*

Here, *Offset* is a user-defined sector offset (its value is 0 by default, but see example 4 below for an explanation).  

### Apple partition without Apple Partition Map

An Apple partition contains either a HFS or HFS+ file system. In the simplest case these file systems can be identified by the presence of a *Master Directory Block* (for a HFS file system) or a *HFS Plus Header* (HFS+ file system) at 1024 bytes into the image. If either of these structures are found, they are parsed by Isolyzer. Both contain a *Block Count* and a *Block Size* field, which are used to calculate the expected size as:

*SizeExpectedApple* =  *Block Count* x *Block Size*

### Apple partition with Apple Partition Map

In some cases Apple partitions are identified by the presence of a sequence of (one or more) [*Apple Partition Maps*](https://en.wikipedia.org/wiki/Apple_Partition_Map) starting at 512 bytes into the image. Images with an Apple Partition Map have a *Zero Block* at the beginning of the file, which contains *Block Count* and a *Block Size* fields that are used to calculate the expected size as:

*SizeExpectedPM* =  *Block Count* x *Block Size*

As an aside, the file system type in this case is identified from the Partition Map's *Partition Type* field. 

### UDF

For UDF file systems estimating the expected file size is less straightforward than the previous file systems, mainly because the equivalent field that denotes the number of blocks in the partition excludes the descriptor blocks that occur before and after the actual data. The following fields are relevant:

* *Logical Block Size*, read from the Logical Volume Descriptor.
* *Partition Length*, read from the Partition Descriptor.
* *Partition Starting Location*, read from the Partition Descriptor.

Using these fields, Isolyzer estimates the expected file size as:

*SizExpectedUDF* = (*Partition Length* + *Partition Starting Location*) * *Logical Block Size*

This corresponds to the combined size of the partition, the descriptor blocks that precede it and one additional descriptor block after the partition. However, often the partition is followed by *multiple* descriptor blocks (sometimes more than 100!). As there doesn't appear to be a way to determine the exact number of trailing descriptor blocks, the value of *SizExpectedUDF* is often smaller than the actual file size. This is something that might be improved in future versions of Isolyzer (e.g. by doing a deeper parsing of the UDF structure).

## Hybrid file systems

Many CD-ROMs and DVDs actually are [hybrids](https://en.wikipedia.org/wiki/Hybrid_disc) that combine multiple file systems. For instance, CD-ROMS with a hybrid ISO 9660/ Apple file system are common, as are DVDs with a UDF file system that is complemented by an additional ISO 9660 file system ([UDF Bridge](http://www.afterdawn.com/glossary/term.cfm/udf_bridge) format).

For these hybrid file systems, Isolyzer assumes that the expected size is the largest value out of the individual values of all file systems:

*SizeExpected* = max(*SizeExpectedISO*, *SizeExpectedApple*, *SizeExpectedPM*, *SizExpectedUDF*) 

## Isolyzer output

Isolyzer report its output in XML format; the top-level element is called *isolyzer*. The *isolyzer* element in turn contains the following child elements:

* *toolInfo*: contains information about Isolyzer

* *image*: contains information about the analysed image

## toolInfo element

This *toolInfo* element holds information about Isolyzer. Currently it contains
the following  child elements:

* *toolName*: name of the analysis tool (i.e. *isolyzer.py* or *isolyzer*, depending on whether the Python script or the Windows
binaries were used)
* *toolVersion*: version of Isolyzer

## image element

The *image* element holds information about an analysed image. It contains the following child elements:

* *fileInfo*: contains general information about the analysed file
* *statusInfo*: contains information about about the status of Isolyzer's attempt at processing the file
* *sectorOffset*: contains the value of `--offset` as specified by the user (offset in sectors)
* *tests*: contains outcomes of the tests that are performed by Isolyzer
* *fileSystems*: contains technical metadata that are extracted from the filesystem-level headers.

## fileInfo element

This element holds general information about the analysed file.
Currently it contains the following sub-elements:

* *filename*: name of the analysed file without its path (e.g.
“rubbish.iso”)
* *filePath*: name of the analysed file, including its full absolute
path (e.g. “d:\\data\\images\\rubbish.iso”)
* *fileSizeInBytes*: file size in bytes
* *fileLastModified*: last modified date and time

## statusInfo element

This element describes the status of 
Isolyzer's attempt at processing a file. It tells you whether 
the analysis could be completed without any internal
errors. It contains the following sub-elements:

* *success*: a Boolean flag that indicates whether the validation attempt 
completed normally (“True”) or not (“False”). A value of “False” indicates
an internal error that prevented Isolyzer from processing the file. 
* *failureMessage*: if the validation attempt failed (value of *success* 
equals “False”), this field gives further details about the reason of the failure.
Examples are:

        memory error (file size too large)

        runtime error (please report to developers)

        unknown error (please report to developers)

## tests element

This element contains the outcomes of the tests that are performed by Isolyzer. Currently it includes the following tests:

* *containsKnownFileSystem*: Boolean (True/False) flag that indicates whether any of the supported file systems were found by Isolyzer
* *sizeExpected*: expected file size of the image in bytes, based on the filesystem-level headers
* *sizeActual*: actual size of the image in bytes
* *sizeDifference*: difference between actual and expected size in bytes (*sizeActual* - *sizeExpected*)
* *sizeDifferenceSectors*: difference between actual and expected size, expressed as a number of 2048-bytes sectors (= *sizeDifference*/2048)
* *sizeAsExpected*: Boolean (True/False) flag that indicates whether the actual image size is identical to the expected value 
* *smallerThanExpected*: Boolean (True/False) flag that indicates whether the actual image size is smaller than the expected value

### Interpretation of the size verification outcome

Often the value of *sizeActual* exceeds *sizeExpected* by several sectors. A possible cause might be that some CD-writers apparently add padding bytes (see for example [here](http://superuser.com/questions/220082/how-to-validate-a-dvd-against-an-iso) and [here](http://twiki.org/cgi-bin/view/Wikilearn/CdromMd5sumsAfterBurning)). For *UDF* file systems *sizeExpected* is typically several sectors smaller than *sizeActual* because of the presence of trailing descriptor blocks that are currently unaccounted for in the calculation of *sizeExpected* (see also the preceding section *Calculation of the expected file size*).

All of the above things are usually nothing to worry about. In cases where *sizeActual* is smaller than *sizeExpected*, it is likely that the image is incomplete or otherwise corrupted. For a typical imaging QA workflows you will probably want to make sure that the value of *containsKnownFileSystem* equals *True*, and *smallerThanExpected* is *False*.

## fileSystems element

The *fileSystems* element contains one or more *fileSystem* elements.

## fileSystem element

The *fileSystem* element contains technical metadata that are extracted from the filesystem-level headers. This element is repeated for each identified file system. Each *fileSystem* element has a *TYPE* attribute whose value indicates the file system. Currently supported values are:

* *ISO 9660*
* *UDF*
* *HFS*
* *HFS+*
* *MFS*

The sub-elements inside each *fileSystem* element depend on its respective file system. Note that for each file system Isolyzer only extracts a subset of all headers (primarily those that are needed for the file size verification).  

## Limitations

* Isolyzer does not 'validate' any of the supported file systems! It merely makes an educated guess about the expected file size and then compares this figure against the actual file size. 
* A correct file *size* alone does not guarantee the integrity of the image (for this there's not getting around running a checksum on both the image and the physical source medium).
* At this stage Isolyzer has only had limited testing with UDF, HFS and HFS+ file systems, so there's a real possibility of some hidden issues lurking. Use at your own peril! 

## Examples

Below are some examples of Isolyzer's output for different kinds of images. Note that the images that were used here are all available in the [*testFiles*](./testFiles) folder of this repo. 

### Example 1: ISO 9660 image has expected size 

    isolyzer iso9660.iso

Output:

    <?xml version="1.0" ?>
    <isolyzer>
        <toolInfo>
            <toolName>isolyzer</toolName>
            <toolVersion>1.0.0b3</toolVersion>
        </toolInfo>
        <image>
            <fileInfo>
                <fileName>iso9660.iso</fileName>
                <filePath>/home/johan/isolyzer/testFiles/iso9660.iso</filePath>
                <fileSizeInBytes>442368</fileSizeInBytes>
                <fileLastModified>Fri Jun 30 18:31:33 2017</fileLastModified>
            </fileInfo>
            <statusInfo>
                <success>True</success>
            </statusInfo>
            <sectorOffset>0</sectorOffset>
            <tests>
                <containsKnownFileSystem>True</containsKnownFileSystem>
                <sizeExpected>442368</sizeExpected>
                <sizeActual>442368</sizeActual>
                <sizeDifference>0</sizeDifference>
                <sizeDifferenceSectors>0</sizeDifferenceSectors>
                <sizeAsExpected>True</sizeAsExpected>
                <smallerThanExpected>False</smallerThanExpected>
            </tests>
            <fileSystems>
                <fileSystem TYPE="ISO 9660">
                    <primaryVolumeDescriptor>
                        <typeCode>1</typeCode>
                        <standardIdentifier>CD001</standardIdentifier>
                        <version>1</version>
                        <systemIdentifier>LINUX</systemIdentifier>
                        <volumeIdentifier>ISO 9660 only demo</volumeIdentifier>
                        <volumeSpaceSize>216</volumeSpaceSize>
                        <volumeSetSize>1</volumeSetSize>
                        <volumeSequenceNumber>1</volumeSequenceNumber>
                        <logicalBlockSize>2048</logicalBlockSize>
                        <pathTableSize>10</pathTableSize>
                        <typeLPathTableLocation>20</typeLPathTableLocation>
                        <optionalTypeLPathTableLocation>0</optionalTypeLPathTableLocation>
                        <typeMPathTableLocation>22</typeMPathTableLocation>
                        <optionalTypeMPathTableLocation>0</optionalTypeMPathTableLocation>
                        <volumeSetIdentifier/>
                        <publisherIdentifier/>
                        <dataPreparerIdentifier/>
                        <applicationIdentifier>MKISOFS ISO9660/HFS/UDF FILESYSTEM BUILDER &amp; CDRECORD CD/DVD/BluRay CREATOR (C) 1993 E.YOUNGDALE (C) 1997 J.PEARSON/J.SCHILLING</applicationIdentifier>
                        <copyrightFileIdentifier/>
                        <abstractFileIdentifier/>
                        <bibliographicFileIdentifier/>
                        <volumeCreationDateAndTime>2017/06/30, 18:31:33</volumeCreationDateAndTime>
                        <volumeModificationDateAndTime>2017/06/30, 18:31:33</volumeModificationDateAndTime>
                        <volumeExpirationDateAndTime>0/00/00, 00:00:00</volumeExpirationDateAndTime>
                        <volumeEffectiveDateAndTime>2017/06/30, 18:31:33</volumeEffectiveDateAndTime>
                        <fileStructureVersion>1</fileStructureVersion>
                    </primaryVolumeDescriptor>
                </fileSystem>
            </fileSystems>
        </image>
    </isolyzer>

### Example 2: ISO 9660 image smaller than expected size

    isolyzer iso9660_trunc.iso

Output:

    <?xml version="1.0" ?>
    <isolyzer>
        <toolInfo>
            <toolName>isolyzer</toolName>
            <toolVersion>1.0.0b3</toolVersion>
        </toolInfo>
        <image>
            <fileInfo>
                <fileName>iso9660_trunc.iso</fileName>
                <filePath>/home/johan/isolyzer/testFiles/iso9660_trunc.iso</filePath>
                <fileSizeInBytes>49157</fileSizeInBytes>
                <fileLastModified>Fri Jun 30 18:31:33 2017</fileLastModified>
            </fileInfo>
            <statusInfo>
                <success>True</success>
            </statusInfo>
            <sectorOffset>0</sectorOffset>
            <tests>
                <containsKnownFileSystem>True</containsKnownFileSystem>
                <sizeExpected>442368</sizeExpected>
                <sizeActual>49157</sizeActual>
                <sizeDifference>-393211</sizeDifference>
                <sizeDifferenceSectors>-192</sizeDifferenceSectors>
                <sizeAsExpected>False</sizeAsExpected>
                <smallerThanExpected>True</smallerThanExpected>
            </tests>
            <fileSystems>
                <fileSystem TYPE="ISO 9660">
                    <primaryVolumeDescriptor>
                        <typeCode>1</typeCode>
                        <standardIdentifier>CD001</standardIdentifier>
                          ::
                          ::
                        <fileStructureVersion>1</fileStructureVersion>
                    </primaryVolumeDescriptor>
                </fileSystem>
            </fileSystems>
        </image>
    </isolyzer>

    
### Example 3: ISO truncated before Primary Volume Descriptor

    isolyzer iso9660_nopvd.iso
    
Output:

    <?xml version="1.0" ?>
    <isolyzer>
        <toolInfo>
            <toolName>isolyzer</toolName>
            <toolVersion>1.0.0b3</toolVersion>
        </toolInfo>
        <image>
            <fileInfo>
                <fileName>iso9660_nopvd.iso</fileName>
                <filePath>/home/johan/isolyzer/testFiles/iso9660_nopvd.iso</filePath>
                <fileSizeInBytes>32860</fileSizeInBytes>
                <fileLastModified>Fri Jun 30 18:31:33 2017</fileLastModified>
            </fileInfo>
            <statusInfo>
                <success>True</success>
            </statusInfo>
            <sectorOffset>0</sectorOffset>
            <tests>
                <containsKnownFileSystem>False</containsKnownFileSystem>
                <sizeExpected>0</sizeExpected>
                <sizeActual>32860</sizeActual>
                <sizeDifference>32860</sizeDifference>
                <sizeDifferenceSectors>16</sizeDifferenceSectors>
                <sizeAsExpected>False</sizeAsExpected>
                <smallerThanExpected>False</smallerThanExpected>
            </tests>
            <fileSystems/>
        </image>
    </isolyzer>

### Example 4: ISO 9660 image from 'enhanced' audio CD (multisession)

First use *cd-info* on the physical carrier to find out the start sector of the data session:

    cd-info
    
Then look for this bit:

    CD-Plus/Extra   
    session #2 starts at track  8, LSN: 21917, ISO 9660 blocks:  25309
    ISO 9660: 25309 blocks, label `DISC 

So start sector of the data session is 21917. Then:

    isolyzer --offset 21917 multisession.iso

Output:

    <?xml version="1.0" ?>
    <isolyzer>
        <toolInfo>
            <toolName>isolyzer</toolName>
            <toolVersion>1.0.0b3</toolVersion>
        </toolInfo>
        <image>
            <fileInfo>
                <fileName>multisession.iso</fileName>
                <filePath>/home/johan/isolyzer/testFiles/multisession.iso</filePath>
                <fileSizeInBytes>6950912</fileSizeInBytes>
                <fileLastModified>Wed Apr 19 14:39:27 2017</fileLastModified>
            </fileInfo>
            <statusInfo>
                <success>True</success>
            </statusInfo>
            <sectorOffset>21917</sectorOffset>
            <tests>
                <containsKnownFileSystem>True</containsKnownFileSystem>
                <sizeExpected>6946816</sizeExpected>
                <sizeActual>6950912</sizeActual>
                <sizeDifference>4096</sizeDifference>
                <sizeDifferenceSectors>2</sizeDifferenceSectors>
                <sizeAsExpected>False</sizeAsExpected>
                <smallerThanExpected>False</smallerThanExpected>
            </tests>
            <fileSystems>
                <fileSystem TYPE="ISO 9660">
                    <primaryVolumeDescriptor>
                        <typeCode>1</typeCode>
                        <standardIdentifier>CD001</standardIdentifier>
                          :: 
                          ::
                        <fileStructureVersion>1</fileStructureVersion>
                    </primaryVolumeDescriptor>
                </fileSystem>
            </fileSystems>
        </image>
    </isolyzer>

### Example 5: UDF image

    isolyzer udf.iso

Output:

    <?xml version="1.0" ?>
    <isolyzer>
        <toolInfo>
            <toolName>isolyzer</toolName>
            <toolVersion>1.0.0b3</toolVersion>
        </toolInfo>
        <image>
            <fileInfo>
                <fileName>udf.iso</fileName>
                <filePath>/home/johan/isolyzer/testFiles/udf.iso</filePath>
                <fileSizeInBytes>614400</fileSizeInBytes>
                <fileLastModified>Fri Jun 30 18:31:33 2017</fileLastModified>
            </fileInfo>
            <statusInfo>
                <success>True</success>
            </statusInfo>
            <sectorOffset>0</sectorOffset>
            <tests>
                <containsKnownFileSystem>True</containsKnownFileSystem>
                <sizeExpected>579584</sizeExpected>
                <sizeActual>614400</sizeActual>
                <sizeDifference>34816</sizeDifference>
                <sizeDifferenceSectors>17</sizeDifferenceSectors>
                <sizeAsExpected>False</sizeAsExpected>
                <smallerThanExpected>False</smallerThanExpected>
            </tests>
            <fileSystems>
                <fileSystem TYPE="UDF">
                    <logicalVolumeDescriptor>
                        <tagIdentifier>6</tagIdentifier>
                        <descriptorVersion>3</descriptorVersion>
                        <tagSerialNumber>1</tagSerialNumber>
                        <volumeSequenceNumber>2</volumeSequenceNumber>
                        <logicalVolumeIdentifier>LinuxUDF</logicalVolumeIdentifier>
                        <logicalBlockSize>2048</logicalBlockSize>
                        <domainIdentifier>*OSTA UDF Compliant</domainIdentifier>
                        <mapTableLength>6</mapTableLength>
                        <numberOfPartitionMaps>1</numberOfPartitionMaps>
                        <implementationIdentifier>*Linux UDFFS</implementationIdentifier>
                        <integritySequenceExtentLength>2048</integritySequenceExtentLength>
                        <integritySequenceExtentLocation>273</integritySequenceExtentLocation>
                    </logicalVolumeDescriptor>
                    <logicalVolumeIntegrityDescriptor>
                        <tagIdentifier>9</tagIdentifier>
                        <descriptorVersion>3</descriptorVersion>
                        <tagSerialNumber>1</tagSerialNumber>
                        <timeStamp>2017/06/30, 18:31:33</timeStamp>
                        <integrityType>1</integrityType>
                        <numberOfPartitions>1</numberOfPartitions>
                        <lengthOfImplementationUse>46</lengthOfImplementationUse>
                        <freeSpaceTable>4</freeSpaceTable>
                        <sizeTable>9</sizeTable>
                    </logicalVolumeIntegrityDescriptor>
                    <partitionDescriptor>
                        <tagIdentifier>5</tagIdentifier>
                        <descriptorVersion>3</descriptorVersion>
                        <tagSerialNumber>1</tagSerialNumber>
                        <volumeDescriptorSequenceNumber>5</volumeDescriptorSequenceNumber>
                        <partitionNumber>0</partitionNumber>
                        <accessType>1</accessType>
                        <partitionStartingLocation>274</partitionStartingLocation>
                        <partitionLength>9</partitionLength>
                    </partitionDescriptor>
                </fileSystem>
            </fileSystems>
        </image>
    </isolyzer>

### Example 6: HFS+ image

    isolyzer hfsplus.iso

Output:

    <?xml version="1.0" ?>
    <isolyzer>
        <toolInfo>
            <toolName>isolyzer</toolName>
            <toolVersion>1.0.0b3</toolVersion>
        </toolInfo>
        <image>
            <fileInfo>
                <fileName>hfsplus.iso</fileName>
                <filePath>/home/johan/isolyzer/testFiles/hfsplus.iso</filePath>
                <fileSizeInBytes>614400</fileSizeInBytes>
                <fileLastModified>Fri Jun 30 18:31:33 2017</fileLastModified>
            </fileInfo>
            <statusInfo>
                <success>True</success>
            </statusInfo>
            <sectorOffset>0</sectorOffset>
            <tests>
                <containsKnownFileSystem>True</containsKnownFileSystem>
                <sizeExpected>614400</sizeExpected>
                <sizeActual>614400</sizeActual>
                <sizeDifference>0</sizeDifference>
                <sizeDifferenceSectors>0</sizeDifferenceSectors>
                <sizeAsExpected>True</sizeAsExpected>
                <smallerThanExpected>False</smallerThanExpected>
            </tests>
            <fileSystems>
                <fileSystem TYPE="HFS+">
                    <hfsPlusVolumeheader>
                        <signature>H+</signature>
                        <version>4</version>
                        <blockSize>2048</blockSize>
                        <blockCount>300</blockCount>
                    </hfsPlusVolumeheader>
                </fileSystem>
            </fileSystems>
        </image>
    </isolyzer>

### Example 7: Hybrid ISO 9660 /UDF image

    isolyzer hfsplus.iso

Output:

    <?xml version="1.0" ?>
    <isolyzer>
        <toolInfo>
            <toolName>isolyzer</toolName>
            <toolVersion>1.0.0b3</toolVersion>
        </toolInfo>
        <image>
            <fileInfo>
                <fileName>iso9660_udf.iso</fileName>
                <filePath>/home/johan/isolyzer/testFiles/iso9660_udf.iso</filePath>
                <fileSizeInBytes>942080</fileSizeInBytes>
                <fileLastModified>Fri Jun 30 18:31:33 2017</fileLastModified>
            </fileInfo>
            <statusInfo>
                <success>True</success>
            </statusInfo>
            <sectorOffset>0</sectorOffset>
            <tests>
                <containsKnownFileSystem>True</containsKnownFileSystem>
                <sizeExpected>942080</sizeExpected>
                <sizeActual>942080</sizeActual>
                <sizeDifference>0</sizeDifference>
                <sizeDifferenceSectors>0</sizeDifferenceSectors>
                <sizeAsExpected>True</sizeAsExpected>
                <smallerThanExpected>False</smallerThanExpected>
            </tests>
            <fileSystems>
                <fileSystem TYPE="ISO 9660">
                    <primaryVolumeDescriptor>
                        <typeCode>1</typeCode>
                        <standardIdentifier>CD001</standardIdentifier>
                        <version>1</version>
                        <systemIdentifier>LINUX</systemIdentifier>
                        <volumeIdentifier>UDF Bridge demo</volumeIdentifier>
                        <volumeSpaceSize>460</volumeSpaceSize>
                        <volumeSetSize>1</volumeSetSize>
                        <volumeSequenceNumber>1</volumeSequenceNumber>
                        <logicalBlockSize>2048</logicalBlockSize>
                        <pathTableSize>10</pathTableSize>
                        <typeLPathTableLocation>263</typeLPathTableLocation>
                        <optionalTypeLPathTableLocation>0</optionalTypeLPathTableLocation>
                        <typeMPathTableLocation>265</typeMPathTableLocation>
                        <optionalTypeMPathTableLocation>0</optionalTypeMPathTableLocation>
                        <volumeSetIdentifier/>
                        <publisherIdentifier/>
                        <dataPreparerIdentifier/>
                        <applicationIdentifier>MKISOFS ISO9660/HFS/UDF FILESYSTEM BUILDER &amp; CDRECORD CD/DVD/BluRay CREATOR (C) 1993 E.YOUNGDALE (C) 1997 J.PEARSON/J.SCHILLING</applicationIdentifier>
                        <copyrightFileIdentifier/>
                        <abstractFileIdentifier/>
                        <bibliographicFileIdentifier/>
                        <volumeCreationDateAndTime>2017/06/30, 18:31:33</volumeCreationDateAndTime>
                        <volumeModificationDateAndTime>2017/06/30, 18:31:33</volumeModificationDateAndTime>
                        <volumeExpirationDateAndTime>0/00/00, 00:00:00</volumeExpirationDateAndTime>
                        <volumeEffectiveDateAndTime>2017/06/30, 18:31:33</volumeEffectiveDateAndTime>
                        <fileStructureVersion>1</fileStructureVersion>
                    </primaryVolumeDescriptor>
                </fileSystem>
                <fileSystem TYPE="UDF">
                    <partitionDescriptor>
                        <tagIdentifier>5</tagIdentifier>
                        <descriptorVersion>2</descriptorVersion>
                        <tagSerialNumber>0</tagSerialNumber>
                        <volumeDescriptorSequenceNumber>2</volumeDescriptorSequenceNumber>
                        <partitionNumber>0</partitionNumber>
                        <accessType>1</accessType>
                        <partitionStartingLocation>257</partitionStartingLocation>
                        <partitionLength>53</partitionLength>
                    </partitionDescriptor>
                    <logicalVolumeDescriptor>
                        <tagIdentifier>6</tagIdentifier>
                        <descriptorVersion>2</descriptorVersion>
                        <tagSerialNumber>0</tagSerialNumber>
                        <volumeSequenceNumber>3</volumeSequenceNumber>
                        <logicalVolumeIdentifier>UDF Bridge demo</logicalVolumeIdentifier>
                        <logicalBlockSize>2048</logicalBlockSize>
                        <domainIdentifier>*OSTA UDF Compliant</domainIdentifier>
                        <mapTableLength>6</mapTableLength>
                        <numberOfPartitionMaps>1</numberOfPartitionMaps>
                        <implementationIdentifier>*mkisofs</implementationIdentifier>
                        <integritySequenceExtentLength>4096</integritySequenceExtentLength>
                        <integritySequenceExtentLocation>64</integritySequenceExtentLocation>
                    </logicalVolumeDescriptor>
                    <logicalVolumeIntegrityDescriptor>
                        <tagIdentifier>9</tagIdentifier>
                        <descriptorVersion>2</descriptorVersion>
                        <tagSerialNumber>0</tagSerialNumber>
                        <timeStamp>2017/06/30, 18:31:33</timeStamp>
                        <integrityType>1</integrityType>
                        <numberOfPartitions>1</numberOfPartitions>
                        <lengthOfImplementationUse>46</lengthOfImplementationUse>
                        <freeSpaceTable>0</freeSpaceTable>
                        <sizeTable>53</sizeTable>
                    </logicalVolumeIntegrityDescriptor>
                </fileSystem>
            </fileSystems>
        </image>
    </isolyzer>


## Further resources

The Isolyzer code is largely based on the following documentation and resources:

* <http://wiki.osdev.org/ISO_9660> - explanation of the ISO 9660 filesystem
 <https://github.com/libyal/libfshfs/blob/master/documentation/Hierarchical%20File%20System%20(HFS).asciidoc> - good explanation of HFS and HFS+ file systems
* <https://opensource.apple.com/source/IOStorageFamily/IOStorageFamily-116/IOApplePartitionScheme.h> - Apple's code with Apple partitions and zero block definitions  
* <https://en.wikipedia.org/wiki/Apple_Partition_Map#Layout> - overview of Apple partition map
* <https://developer.apple.com/legacy/library/documentation/mac/Files/Files-102.html> - Apple documentation on Master Directory Block structure
* <http://wiki.osdev.org/UDF> - overview of UDF
* <https://www.ecma-international.org/publications/standards/Ecma-167.htm> - Volume and File Structure for Write-Once and Rewritable Media using Non-Sequential Recording for Information Interchange (general framework that forms basis of UDF)
* <http://www.osta.org/specs/index.htm> - UDF specifications
* <https://www.ecma-international.org/publications/files/ECMA-TR/ECMA%20TR-071.PDF> - UDF Bridge Format
* <https://sites.google.com/site/udfintro/> - Wenguang's Introduction to Universal Disk Format (UDF)
* <https://en.wikipedia.org/wiki/Hybrid_disc> - Wikipedia entry on hybrid discs


## License

Published under the [Apache 2.0](http://www.apache.org/licenses/LICENSE-2.0) license.