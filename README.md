# Isolyzer

## About

*Isolyzer* verifies if the file size of a CD / DVD image ("ISO image") is consistent with the information in its filesystem-level headers. The following file systems are supported:

* [ISO 9660](https://en.wikipedia.org/wiki/ISO_9660)
* [High Sierra](https://web.archive.org/web/20220111023846/https://www.os2museum.com/files/docs/cdrom/CDROM_Working_Paper-1986.pdf) (supported in isolyzer 1.4.0 and onward)
* [Universal Disk Format](https://en.wikipedia.org/wiki/Universal_Disk_Format) (UDF)
* Apple [Hierarchical File System](https://en.wikipedia.org/wiki/Hierarchical_File_System) (HFS)
* Apple [HFS+](https://en.wikipedia.org/wiki/HFS_Plus)
* [Hybrids](https://en.wikipedia.org/wiki/Hybrid_disc) of the above file systems, e.g. ISO 9660 + HFS; UDF Bridge (UDF + ISO 9660)

Isolyzer uses the information in the filesystem-level headers to calculate the expected file size (typically based on a block size field and a number of blocks field). This is then compared against the actual file size, which can be useful for detecting incomplete (e.g. truncated) ISO images. Isolyzer also extracts and reports some technical metadata from the filesystem-level headers.

## Installation

The easiest method to install Isolyzer is to use the [*pip* package manager](https://en.wikipedia.org/wiki/Pip_(package_manager)). You will need a recent version of *pip* (version 9.0 or more recent). Alternatively, Windows users can also use stand-alone binaries that don't require Python (see below).

## Installation with pip 

Before installing, you need to decide whether you want to install Isolyzer for a single user only, or do a global installation (that is: for all users). The main advantage of a single-user installation is that it doesn't require administrator (sudo) rights. The downside is that this will install the tool to a directory that is not included in the `PATH` environment variable by default, which means you'll have to do some (minor) configuration to make it work. A global installation will make Isolyzer usable without any configuration, but the downside is that you need administrator (sudo) rights. Both methods are explained below.

### Single user installation (Linux)

Enter the following command:

```
pip install isolyzer --user
```

This will install the software to the `.local` folder (hidden by default!) in your home directory (`~/.local`). Next try to run Isolyzer by entering:

```
isolyzer
```

Most likely this will result in:

```
isolyzer: command not found
```

If this happens, you will need to add the directory `~/.local/bin` (which is where the Isolyzer command-line tool is installed) to the `PATH` environment variable (you only need to do this once). To do this, locate the (hidden) file `.profile` in you home directory (`~/`), and open it in a text editor. Then add the following lines at the end of the file:

```
# set PATH so it includes the user's .local bin if it exists
if [ -d "$HOME/.local/bin" ] ; then
    PATH="$HOME/.local/bin:$PATH"
fi
```

Save the file, log out of your session and then log in again. Open a command terminal and type:

```
isolyzer
```

If all went well you now see this:

```
usage: isolyzer [-h] [--version] ISOImage
isolyzer: error: too few arguments
```

Which means that the installation was successful!

### Global installation (Linux)

Simply enter:

```
sudo -H pip install isolyzer
```

No further configuration is needed in this case. 

### Note on pre-releases

The above command lines will only install stable versions of isolyzer. In order to install the latest pre-release, add the `--pre` switch. For example:

```
sudo -H pip install isolyzer --pre
```

## Installation from stand-alone binaries (Windows)

Go to the *release* page of Isolyzer's Github repo:

<https://github.com/KBNLresearch/isolyzer/releases>

Then download the file 'isolyzer_x.y.z_win64.zip' from the most recent release. Unzip the file to whatever location on your machine you like. You'll now be able to run Isolyzer from a command window by entering 'isolyzer', including its full path. For example, if you extracted the zip file 'isolyzer_1.4.0_win64.zip' to directory 'c:\isolyzer', you have to enter:

```
c:\\isolyzer\isolyzer
```

## Upgrade Isolyzer to the latest version

If you installed with pip, enter this for a single user installation:

```
pip install isolyzer -U --user
```

For a global installation:

```
sudo -H pip install isolyzer -U
```

If you installed from the Windows binaries, repeat the instructions from the 'Installation from stand-alone binaries' section above (you may want to remove the old installation manually).

## Command line use

### Usage

```
isolyzer [-h] [--version] [--offset SECTOROFFSET] ISOImage
```

### Positional arguments

`ISOImage` : input ISO image

### Optional arguments

`-h, --help` : show this help message and exit;

`-v, --version` : show program's version number and exit;

`--offset SECTOROFFSET`, `-o SECTOROFFSET` : offset (in sectors) of ISO image on CD (analogous to *-N* option in cdinfo; only affects size calculation for ISO 9660 file systems)

## Using isolyzer as a Python module

Instead of using isolyzer from the command-line, you can also import
it as a module in your own Python programs. To do so, install isolyzer
with *pip*. Then import it into your code by adding:

```python
from isolyzer import isolyzer
```

Use the *processImage* function to analyze a file. This function takes
two arguments:

1. The file that you want to analyze
2. A sector offset value

The following minimal script shows how this works:

```python
#! /usr/bin/env python3

from isolyzer import isolyzer

# Define image file
myFile = "/home/johan/isolyzer/testFiles/iso9660.iso"

# Analyse with isolyzer, result to Element object
isolyzerResult = isolyzer.processImage(myFile, 0)

# Isolyzer status
isolyzerSuccess = isolyzerResult.find('statusInfo/success').text

# True/false flag that indicates if image smaller than expected
smallerThanExpected = isolyzerResult.find('tests/smallerThanExpected').text
```

## Calculation of the expected file size

### ISO 9660

For an ISO 9660 file system, Isolyzer locates and parses its [Primary Volume Descriptor](http://wiki.osdev.org/ISO_9660#The_Primary_Volume_Descriptor) (PVD). From the PVD it then reads the *Volume Space Size* field (which denotes the number of sectors/blocks in the image) and the *Logical Block Size* field (the number of bytes for each block). The expected file size is then calculated as:

*SizeExpectedISO* =  (*Volume Space Size* - *Offset*) x *Logical Block Size*

Here, *Offset* is a user-defined sector offset (its value is 0 by default, but see example 4 below for an explanation).  

### High Sierra

For the High Sierra file system, Isolyzer locates and parses the Standard File Structure Volume Descriptor (SFSVD). From the SFSVD it then reads the *Volume Space Size* and *Logical Block Size* fields (which both have the same meaning as in ISO 9660). The expected file size is then calculated as:

*SizeExpectedHS* =  (*Volume Space Size* - *Offset*) x *Logical Block Size*

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
* *statusInfo*: contains information about the status of Isolyzer's attempt at processing the file
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

```
memory error (file size too large)

runtime error (please report to developers)

unknown error (please report to developers)
```

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
* *High Sierra*
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

```
isolyzer iso9660.iso
```

Output:

```xml
<?xml version="1.0" ?>
<isolyzer xmlns="http://kb.nl/ns/isolyzer/v1/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://kb.nl/ns/isolyzer/v1/ https://raw.githubusercontent.com/KBNLresearch/isolyzer/xsd/xsd/isolyzer-v-1-0.xsd">
    <toolInfo>
        <toolName>isolyzer</toolName>
        <toolVersion>1.4.0a3</toolVersion>
    </toolInfo>
    <image>
        <fileInfo>
            <fileName>iso9660.iso</fileName>
            <filePath>/home/johan/isolyzer/testFiles/iso9660.iso</filePath>
            <fileSizeInBytes>442368</fileSizeInBytes>
            <fileLastModified>Thu Apr 14 18:49:18 2022</fileLastModified>
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
            <sizeDifferenceSectors>0.0</sizeDifferenceSectors>
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
                    <volumeIdentifier>ISO9660 only</volumeIdentifier>
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
                    <applicationIdentifier>GENISOIMAGE ISO 9660/HFS FILESYSTEM CREATOR (C) 1993 E.YOUNGDALE (C) 1997-2006 J.PEARSON/J.SCHILLING (C) 2006-2007 CDRKIT TEAM</applicationIdentifier>
                    <copyrightFileIdentifier/>
                    <abstractFileIdentifier/>
                    <bibliographicFileIdentifier/>
                    <volumeCreationDateAndTime>2022/04/07, 20:31:13</volumeCreationDateAndTime>
                    <volumeModificationDateAndTime>2022/04/07, 20:31:13</volumeModificationDateAndTime>
                    <volumeExpirationDateAndTime>0/00/00, 00:00:00</volumeExpirationDateAndTime>
                    <volumeEffectiveDateAndTime>2022/04/07, 20:31:13</volumeEffectiveDateAndTime>
                    <fileStructureVersion>1</fileStructureVersion>
                </primaryVolumeDescriptor>
            </fileSystem>
        </fileSystems>
    </image>
</isolyzer>
```

### Example 2: ISO 9660 image smaller than expected size

```
isolyzer iso9660_trunc.iso
```

Output:

```xml
<?xml version="1.0" ?>
<isolyzer xmlns="http://kb.nl/ns/isolyzer/v1/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://kb.nl/ns/isolyzer/v1/ https://raw.githubusercontent.com/KBNLresearch/isolyzer/xsd/xsd/isolyzer-v-1-0.xsd">
    <toolInfo>
        <toolName>isolyzer</toolName>
        <toolVersion>1.4.0a3</toolVersion>
    </toolInfo>
    <image>
        <fileInfo>
            <fileName>iso9660_trunc.iso</fileName>
            <filePath>/home/johan/isolyzer/testFiles/iso9660_trunc.iso</filePath>
            <fileSizeInBytes>49157</fileSizeInBytes>
            <fileLastModified>Thu Apr 14 18:49:18 2022</fileLastModified>
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
            <sizeDifferenceSectors>-191.99755859375</sizeDifferenceSectors>
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
```

### Example 3: ISO 9660 image from 'enhanced' audio CD (multisession)

First use *cd-info* on the physical carrier to find out the start sector of the data session:

```
cd-info
```

Then look for this bit:

```
CD-Plus/Extra
session #2 starts at track  8, LSN: 21917, ISO 9660 blocks:  25309
ISO 9660: 25309 blocks, label `DISC
```

So start sector of the data session is 21917. Then:

```
isolyzer --offset 21917 multisession.iso
```

Output:

```xml
<?xml version="1.0" ?>
<isolyzer xmlns="http://kb.nl/ns/isolyzer/v1/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://kb.nl/ns/isolyzer/v1/ https://raw.githubusercontent.com/KBNLresearch/isolyzer/xsd/xsd/isolyzer-v-1-0.xsd">
    <toolInfo>
        <toolName>isolyzer</toolName>
        <toolVersion>1.4.0a3</toolVersion>
    </toolInfo>
    <image>
        <fileInfo>
            <fileName>multisession.iso</fileName>
            <filePath>/home/johan/isolyzer/testFiles/multisession.iso</filePath>
            <fileSizeInBytes>6950912</fileSizeInBytes>
            <fileLastModified>Wed Nov  1 18:19:19 2017</fileLastModified>
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
            <sizeDifferenceSectors>2.0</sizeDifferenceSectors>
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
```

### Example 4: Hybrid ISO 9660 /UDF /  image

```
isolyzer iso9660_udf_hfs.iso
```

Output:

```xml
<?xml version="1.0" ?>
<isolyzer xmlns="http://kb.nl/ns/isolyzer/v1/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://kb.nl/ns/isolyzer/v1/ https://raw.githubusercontent.com/KBNLresearch/isolyzer/xsd/xsd/isolyzer-v-1-0.xsd">
    <toolInfo>
        <toolName>isolyzer</toolName>
        <toolVersion>1.4.0a3</toolVersion>
    </toolInfo>
    <image>
        <fileInfo>
            <fileName>iso9660_udf_hfs.iso</fileName>
            <filePath>/home/johan/isolyzer/testFiles/iso9660_udf_hfs.iso</filePath>
            <fileSizeInBytes>1212416</fileSizeInBytes>
            <fileLastModified>Thu Apr  7 20:31:13 2022</fileLastModified>
        </fileInfo>
        <statusInfo>
            <success>True</success>
        </statusInfo>
        <sectorOffset>0</sectorOffset>
        <tests>
            <containsKnownFileSystem>True</containsKnownFileSystem>
            <sizeExpected>1212416</sizeExpected>
            <sizeActual>1212416</sizeActual>
            <sizeDifference>0</sizeDifference>
            <sizeDifferenceSectors>0.0</sizeDifferenceSectors>
            <sizeAsExpected>True</sizeAsExpected>
            <smallerThanExpected>False</smallerThanExpected>
        </tests>
        <fileSystems>
            <fileSystem TYPE="ISO 9660">
                <primaryVolumeDescriptor>
                    <typeCode>1</typeCode>
                    <standardIdentifier>CD001</standardIdentifier>
                    <version>1</version>
                        :: 
                        ::
                </primaryVolumeDescriptor>
            </fileSystem>
            <fileSystem TYPE="HFS">
                <appleZeroBlock>
                    <signature>ER</signature>
                    <blockSize>512</blockSize>
                    <blockCount>1764</blockCount>
                    <deviceType>1</deviceType>
                    <deviceID>1</deviceID>
                    <driverData>1149173760</driverData>
                    <driverDescriptorCount>0</driverDescriptorCount>
                    <driverDescriptorBlockStart>0</driverDescriptorBlockStart>
                    <driverDescriptorBlockCount>0</driverDescriptorBlockCount>
                    <driverDescriptorSystemType>0</driverDescriptorSystemType>
                </appleZeroBlock>
                <applePartitionMap>
                    <signature>PM</signature>
                    <numberOfPartitionEntries>2</numberOfPartitionEntries>
                    <partitionBlockStart>1</partitionBlockStart>
                    <partitionBlockCount>2</partitionBlockCount>
                    <partitionName>Apple</partitionName>
                    <partitionType>Apple_partition_map</partitionType>
                        :: 
                        ::
                </applePartitionMap>
                <applePartitionMap>
                    <signature>PM</signature>
                    <numberOfPartitionEntries>2</numberOfPartitionEntries>
                    <partitionBlockStart>16</partitionBlockStart>
                    <partitionBlockCount>1748</partitionBlockCount>
                    <partitionName>UDF Bridge</partitionName>
                    <partitionType>Apple_HFS</partitionType>
                        :: 
                        ::
                </applePartitionMap>
                <masterDirectoryBlock>
                    <signature>BD</signature>
                    <blockCount>436</blockCount>
                    <blockSize>2048</blockSize>
                    <volumeName>UDF Bridge</volumeName>
                </masterDirectoryBlock>
            </fileSystem>
            <fileSystem TYPE="UDF">
                <partitionDescriptor>
                    <tagIdentifier>5</tagIdentifier>
                    <descriptorVersion>2</descriptorVersion>
                        :: 
                        ::
                </partitionDescriptor>
                <logicalVolumeDescriptor>
                    <tagIdentifier>6</tagIdentifier>
                    <descriptorVersion>2</descriptorVersion>
                    <tagSerialNumber>0</tagSerialNumber>
                        :: 
                        ::
                </logicalVolumeDescriptor>
                <logicalVolumeIntegrityDescriptor>
                    <tagIdentifier>9</tagIdentifier>
                    <descriptorVersion>2</descriptorVersion>
                    <tagSerialNumber>0</tagSerialNumber>
                        :: 
                        ::
                </logicalVolumeIntegrityDescriptor>
            </fileSystem>
        </fileSystems>
    </image>
</isolyzer>
```

## Further resources

The Isolyzer code is largely based on the following documentation and resources:

* <http://wiki.osdev.org/ISO_9660> - explanation of the ISO 9660 filesystem
* <https://web.archive.org/web/20220111023846/https://www.os2museum.com/files/docs/cdrom/CDROM_Working_Paper-1986.pdf> - Working Paper for a Standard CDROM Volume and File Structure (High Sierra specification)
* <http://preserve.mactech.com/articles/develop/issue_03/high_sierra.html> - Overview of main differences between the ISO 9660 and High Sierra formats
* <https://github.com/libyal/libfshfs/blob/master/documentation/Hierarchical%20File%20System%20(HFS).asciidoc> - good explanation of HFS and HFS+ file systems
* <https://opensource.apple.com/source/IOStorageFamily/IOStorageFamily-116/IOApplePartitionScheme.h> - Apple's code with Apple partitions and zero block definitions
* <https://en.wikipedia.org/wiki/Apple_Partition_Map#Layout> - overview of Apple partition map
* <https://developer.apple.com/legacy/library/documentation/mac/Files/Files-102.html> - Apple documentation on Master Directory Block structure
* <http://wiki.osdev.org/UDF> - overview of UDF
* <https://www.ecma-international.org/publications/standards/Ecma-167.htm> - Volume and File Structure for Write-Once and Rewritable Media using Non-Sequential Recording for Information Interchange (general framework that forms basis of UDF)
* <http://www.osta.org/specs/index.htm> - UDF specifications
* <https://www.ecma-international.org/publications/files/ECMA-TR/ECMA%20TR-071.PDF> - UDF Bridge Format
* <https://sites.google.com/site/udfintro/> - Wenguang's Introduction to Universal Disk Format (UDF)
* <https://en.wikipedia.org/wiki/Hybrid_disc> - Wikipedia entry on hybrid discs
* <https://archive.org/details/MS_BOOKSHELF_87> -Hight Sierra example file (in BIN/CUE format; use bchunk to extract ISO image first!)

## License

Published under the [Apache 2.0](http://www.apache.org/licenses/LICENSE-2.0) license.