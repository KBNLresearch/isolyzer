#! /usr/bin/env python3
"""Verify if size of CD / DVD ISO image is consistent with the information in
its filesystem-level headers.
"""
#
# Copyright (C) 2015 -2022, Johan van der Knijff, Koninklijke Bibliotheek
#  National Library of the Netherlands
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from __future__ import division
import sys
import os
import mmap
import time
import glob
import platform
import re
import codecs
import argparse
import xml.etree.ElementTree as ET
from xml.dom import minidom
from . import iso9660 as iso
from . import hsf as hsf
from . import udf as udf
from . import apple as apple
from . import byteconv as bc
from . import shared as shared


scriptPath, scriptName = os.path.split(sys.argv[0])

# Fix empty scriptName if isolyzer is called from Java/Jython
if len(scriptName) == 0:
    scriptName = 'isolyzer'

__version__ = '1.4.0'


# Name space and XSD schema strings 
nsString = 'http://kb.nl/ns/isolyzer/v1/'
schemaString = 'http://kb.nl/ns/isolyzer/v1/ \
https://raw.githubusercontent.com/KBNLresearch/isolyzer/main/xsd/isolyzer-v-1-0.xsd'
xsiNsString = 'http://www.w3.org/2001/XMLSchema-instance'

# Create parser
parser = argparse.ArgumentParser(
    description="Verify file size of ISO image and extract technical information")


def printWarning(msg):
    """Print warning to stderr"""
    msgString = ("User warning: " + msg + "\n")
    sys.stderr.write(msgString)


def errorExit(msg):
    """Print warning to stderr and exit"""
    msgString = ("Error: " + msg + "\n")
    sys.stderr.write(msgString)
    sys.exit()


def checkFileExists(fileIn):
    """Check if file exists and exit if not"""
    if not os.path.isfile(fileIn):
        msg = fileIn + " does not exist"
        errorExit(msg)


def fileToMemoryMap(filename):
    """Read contents of filename to memory map object"""

    # Open filename
    f = open(filename, "rb")

    # Call to mmap is different on Linux and Windows, so we need to know
    # the current platform
    platform = sys.platform

    try:
        if platform == "win32":
            # Parameters for Windows may need further fine-tuning ...
            fileData = mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ)
        else:
            # This works for Linux (and Cygwin on Windows). Not too sure
            # about other platforms like Mac OS though
            fileData = mmap.mmap(f.fileno(), 0, mmap.MAP_SHARED, mmap.PROT_READ)
    except ValueError:
        # mmap fails on empty files.
        fileData = ""

    f.close()

    return fileData


def makeHumanReadable(element, remapTable={}):
    """Takes element object, and returns a modified version in which all
    non-printable 'text' fields (which may contain numeric data or binary strings)
    are replaced by printable strings

    Property values in original tree may be mapped to alternative (more user-friendly)
    reportable values using a remapTable, which is a nested dictionary.
    TODO: add to separate module
    """

    for elt in element.iter():
        # Text field of this element
        textIn = elt.text

        # Tag name
        tag = elt.tag

        # Step 1: replace property values by values defined in enumerationsMap,
        # if applicable
        try:
            # If tag is in enumerationsMap, replace property values
            parameterMap = remapTable[tag]
            try:
                # Map original property values to values in dictionary
                remappedValue = parameterMap[textIn]
            except KeyError:
                # If value doesn't match any key: use original value
                # instead
                remappedValue = textIn
        except KeyError:
            # If tag doesn't match any key in enumerationsMap, use original
            # value
            remappedValue = textIn

        # Step 2: convert all values to text strings.

        # First set up list of all numeric data types,
        numericTypes = [int, float, bool]

        # Convert

        if remappedValue is not None:
            # Data type
            textType = type(remappedValue)

            # Convert text field, depending on type
            if textType == bytes:
                textOut = bc.bytesToText(remappedValue)
            elif textType in numericTypes:
                textOut = str(remappedValue)
            else:
                # Remove control chars and strip leading/ trailing whitespaces
                textOut = bc.removeControlCharacters(remappedValue).strip()

            # Update output tree
            elt.text = textOut


def writeElement(elt, codec):
    """Writes element as XML to stdout using defined codec"""

    # Element to string
    xmlOut = ET.tostring(elt, 'unicode', 'xml')

    # Make xml pretty
    xmlPretty = minidom.parseString(xmlOut).toprettyxml('    ')

    xmlOut = xmlPretty

    # Write output
    codec.write(xmlOut)


def stripSurrogatePairs(ustring):

    """Removes surrogate pairs from a Unicode string"""

    # This works for Python 3.x, but not for 2.x!
    # Source: http://stackoverflow.com/q/19649463/1209004

    try:
        ustring.encode('utf-8')
    except UnicodeEncodeError:
        # Strip away surrogate pairs
        tmp = ustring.encode('utf-8', 'replace')
        ustring = tmp.decode('utf-8', 'ignore')

    return ustring


def parseCommandLine():
    """Parse command line"""
    # Add arguments
    parser.add_argument('ISOImages',
                        action="store",
                        type=str,
                        nargs='+',
                        help="input ISO image(s) (wildcards allowed)")
    parser.add_argument('--version', '-v',
                        action='version',
                        version=__version__)
    parser.add_argument('--offset', '-o',
                        type=int,
                        help="offset (in sectors) of ISO image on CD (analogous to \
                        -N option in cdinfo)",
                        action='store',
                        dest='sectorOffset',
                        default=0)

    # Parse arguments
    args = parser.parse_args()

    return args


def processImage(image, offset):
    """Process one image"""

    # Does image exist?
    checkFileExists(image)

    # Create root element for image
    imageRoot = ET.Element('image')

    # Create elements for file and status meta info
    fileInfo = ET.Element('fileInfo')
    statusInfo = ET.Element('statusInfo')

    # File name and path
    fileName = os.path.basename(image)
    filePath = os.path.abspath(image)

    # If file name / path contain any surrogate pairs, remove them to
    # avoid problems when writing to XML
    fileNameCleaned = stripSurrogatePairs(fileName)
    filePathCleaned = stripSurrogatePairs(filePath)

    # Produce some general file meta info
    shared.addProperty(fileInfo, "fileName", fileNameCleaned)
    shared.addProperty(fileInfo, "filePath", filePathCleaned)
    shared.addProperty(fileInfo, "fileSizeInBytes", str(os.path.getsize(image)))
    try:
        lastModifiedDate = time.ctime(os.path.getmtime(image))
    except ValueError:
        # Dates earlier than 1 Jan 1970 can raise ValueError on Windows
        # Workaround: replace by lowest possible value (typically 1 Jan 1970)
        lastModifiedDate = time.ctime(0)
    shared.addProperty(fileInfo, "fileLastModified", lastModifiedDate)

    tests = ET.Element("tests")
    fileSystems = ET.Element("fileSystems")

    # Initialise success flag
    success = True

    try:
        # Get file size in bytes
        isoFileSize = os.path.getsize(image)

        # Set these flags to initial value
        containsAppleMasterDirectoryBlock = False
        containsHFSPlusVolumeHeader = False
        containsAppleFS = False
        containsApplePartitionMap = False
        parsedAppleZeroBlock = False
        containsUDF = False
        appleBlockSize = 512

        # Contents of file to memory map object
        isoBytes = fileToMemoryMap(image)

        # Does image match byte signature for an ISO 9660 file system?
        containsISO9660Signature = isoBytes[32769:32774] == b'CD001' \
            and isoBytes[34817:34822] == b'CD001'

        # Does image match byte signature for a High Sierra file system?
        containsHSFSignature = isoBytes[32777:32782] == b'CDROM'
      
        # Does image contain Apple Zero Block?
        containsAppleZeroBlock = isoBytes[0:2] == b'\x45\x52'

        if containsAppleZeroBlock:
            # Read block size
            appleBlockSize = bc.bytesToUShortInt(isoBytes[2:4])

        # Look for Apple Partition Map. Since we cannot rely on the block size
        # defined in the zero block, we do this by trial and error. First create
        # a list with all possible start offsets (not sure if 1024 and 1536 are even used in the wild)
        pmOffsets = [512, 1024, 1536, 2048, appleBlockSize]
        # Remove duplicates and sort
        pmOffsets = sorted(list(set(pmOffsets)))

        # Iterate over offsets, and stop at first match
        for pmOffset in pmOffsets:
            if isoBytes[pmOffset:pmOffset + 2] == b'\x50\x4D':
                containsApplePartitionMap = True
                partitionMapOffset = pmOffset
                appleBlockSize = pmOffset
                break

        # Does image contain HFS Plus Header or Master Directory Block? This also allows us to
        # identify the specific file system
        # (Note: the HFS Plus Header replaces the Master Directory Block of HFS)

        if isoBytes[1024:1026] == b'\x42\x44':
            # Hierarchical File System
            containsAppleMasterDirectoryBlock = True
            fileSystemApple = "HFS"
        if isoBytes[1024:1026] == b'\xd2\xd7':
            # Macintosh File System
            containsAppleMasterDirectoryBlock = True
            fileSystemApple = "MFS"
        if isoBytes[1024:1026] == b'\x48\x2B':
            # HFS Plus
            containsHFSPlusVolumeHeader = True
            fileSystemApple = "HFS+"
        if isoBytes[1024:1026] == b'\x48\x58':
            # HFS X (record as HFS+ for consistency with Partition Map fields)
            containsHFSPlusVolumeHeader = True
            fileSystemApple = "HFS+"

        # Create element to store properties of Apple filesystems
        if (containsApplePartitionMap or containsAppleMasterDirectoryBlock or
                containsHFSPlusVolumeHeader):
            containsAppleFS = True
            fsApple = ET.Element("fileSystem")

        if containsAppleZeroBlock:

            # Based on description at: https://en.wikipedia.org/wiki/Apple_Partition_Map#Layout and
            # https://opensource.apple.com/source/IOStorageFamily/IOStorageFamily-116/IOApplePartitionScheme.h

            # Get zero block data
            appleZeroBlockData = isoBytes[0:512]
            try:
                appleZeroBlockInfo = apple.parseZeroBlock(appleZeroBlockData)
                fsApple.append(appleZeroBlockInfo)
                parsedAppleZeroBlock = True
            except Exception:
                parsedAppleZeroBlock = False

            # shared.addProperty(tests, "parsedAppleZeroBlock", str(parsedAppleZeroBlock))
        if containsApplePartitionMap:

            # Set up list to store all values of 'partionType' in partition map
            partitionTypes = []

            # Get partition map data
            applePartitionMapData = isoBytes[partitionMapOffset:partitionMapOffset + appleBlockSize]
            try:
                applePartitionMapInfo = apple.parsePartitionMap(applePartitionMapData)
                # Add partition type value to list
                partitionType = applePartitionMapInfo.find('partitionType').text
                partitionTypes.append(partitionType)
                fsApple.append(applePartitionMapInfo)
                parsedApplePartitionMap = True
            except Exception:
                parsedApplePartitionMap = False
                partitionType = ''

            # If partitionType is Apple_HFS, parse corresponding Master Directory Block
            if partitionType == 'Apple_HFS':
                offsetHFS = appleBlockSize * applePartitionMapInfo.find('partitionBlockStart').text
                masterDirectoryBlockData = isoBytes[offsetHFS + 1024:offsetHFS + 1536]
                try:
                    masterDirectoryBlockInfo = apple.parseMasterDirectoryBlock(masterDirectoryBlockData)
                    fsApple.append(masterDirectoryBlockInfo)
                    parsedMasterDirectoryBlock = True
                except Exception:
                    parsedMasterDirectoryBlock = False

            # Iterate over remaining partition map entries
            pOffset = partitionMapOffset + appleBlockSize
            for pMap in range(0, applePartitionMapInfo.find('numberOfPartitionEntries').text - 1):
                applePartitionMapData = isoBytes[pOffset:pOffset + appleBlockSize]
                try:
                    applePartitionMapInfo = apple.parsePartitionMap(applePartitionMapData)
                    # Add partition type value to list
                    partitionType = applePartitionMapInfo.find('partitionType').text
                    partitionTypes.append(partitionType)
                    fsApple.append(applePartitionMapInfo)
                    parsedApplePartitionMap = True
                except Exception:
                    parsedApplePartitionMap = False
                    partitionType = ''

                # If partitionType is Apple_HFS, parse corresponding Master Directory Block
                if partitionType == 'Apple_HFS':
                    offsetHFS = appleBlockSize * applePartitionMapInfo.find('partitionBlockStart').text
                    masterDirectoryBlockData = isoBytes[offsetHFS + 1024:offsetHFS + 1536]

                    try:
                        masterDirectoryBlockInfo = apple.parseMasterDirectoryBlock(masterDirectoryBlockData)
                        fsApple.append(masterDirectoryBlockInfo)
                        parsedMasterDirectoryBlock = True
                    except Exception:
                        parsedMasterDirectoryBlock = False

                pOffset += appleBlockSize

            # Establish file system type from partitionType values in all partition maps
            # Source: https://en.wikipedia.org/wiki/Apple_Partition_Map#Partition_identifiers
            # Note that this doesn't cover all possible types (but no idea if any of the other types
            # are used for optical media)

            if 'Apple_MFS' in partitionTypes:
                # Macintosh File System
                fileSystemApple = "MFS"
            elif 'Apple_HFS' in partitionTypes:
                # Hierarchical File System
                fileSystemApple = "HFS"
            elif 'Apple_HFSX' in partitionTypes:
                # HFS Plus
                fileSystemApple = "HFS+"
            else:
                # Unknown file system
                fileSystemApple = "Unknown"

        if containsHFSPlusVolumeHeader:

            hfsPlusHeaderData = isoBytes[1024:1536]
            try:
                hfsPlusHeaderInfo = apple.parseHFSPlusVolumeHeader(hfsPlusHeaderData)
                fsApple.append(hfsPlusHeaderInfo)
                parsedHFSPlusVolumeHeader = True
            except Exception:
                parsedHFSPlusVolumeHeader = False

            # shared.addProperty(tests, "parsedHFSPlusVolumeHeader", str(parsedHFSPlusVolumeHeader))

        if containsAppleMasterDirectoryBlock:

            masterDirectoryBlockData = isoBytes[1024:1536]  # Size of MDB?
            try:
                masterDirectoryBlockInfo = apple.parseMasterDirectoryBlock(masterDirectoryBlockData)
                fsApple.append(masterDirectoryBlockInfo)
                parsedMasterDirectoryBlock = True
            except Exception:
                parsedMasterDirectoryBlock = False

            # shared.addProperty(tests, "parsedMasterDirectoryBlock",\
            # str(parsedMasterDirectoryBlock))

        # This is a dummy value
        volumeDescriptorType = -1

        # Count volume descriptors (ISO + High Sierra)
        noISOVolumeDescriptors = 0
        noHSFVolumeDescriptors = 0

        # Flag that indicates primary volume descriptor (ISO) / Standard File Structure Volume
        # Descriptor (High Sierra) was parsed
        parsedPrimaryVolumeDescriptor = False
        parsedSFSVolumeDescriptor = False

        # Skip to byte 32768, which is where actual ISO 9660/HSF fields start
        byteStart = 32768

        if containsISO9660Signature:

            # Create element to store properties of ISO9660 filesystem
            fsISO = ET.Element("fileSystem")

            # Read through all 2048-byte ISO volume descriptors, until Volume Descriptor
            # Set Terminator is found (or unexpected EOF, which will result in -9999
            # value for volumeDescriptorType)
            while volumeDescriptorType != 255 and volumeDescriptorType != -9999:

                volumeDescriptorType, volumeDescriptorData, byteEnd = \
                    iso.getVolumeDescriptor(isoBytes, byteStart)
                noISOVolumeDescriptors += 1

                if volumeDescriptorType == 1:
                    # Get info from Primary Volume Descriptor (as element object)
                    try:
                        pvdInfo = iso.parsePrimaryVolumeDescriptor(volumeDescriptorData)
                        fsISO.append(pvdInfo)
                        parsedPrimaryVolumeDescriptor = True
                    except Exception:
                        parsedPrimaryVolumeDescriptor = False
                        # raise

                    # shared.addProperty(tests, "parsedPrimaryVolumeDescriptor", \
                    # str(parsedPrimaryVolumeDescriptor))
                byteStart = byteEnd

        if containsHSFSignature:

            # Create element to store properties of High Sierra filesystem
            fsHSF = ET.Element("fileSystem")

            # Read through all 2048-byte volume descriptors, until Volume Descriptor
            # Set Terminator is found (or unexpected EOF, which will result in -9999
            # value for volumeDescriptorType)
            while volumeDescriptorType != 255 and volumeDescriptorType != -9999:

                volumeDescriptorType, volumeDescriptorData, byteEnd = \
                    hsf.getVolumeDescriptor(isoBytes, byteStart)
                
                noHSFVolumeDescriptors += 1

                if volumeDescriptorType == 1:
                    # Get info from Standard File Structure Volume Descriptor (as element object)
                    try:
                        sfsvdInfo = hsf.parseSFSVolumeDescriptor(volumeDescriptorData)
                        fsHSF.append(sfsvdInfo)
                        parsedSFSVolumeDescriptor = True
                    except Exception:
                        parsedSFSVolumeDescriptor = False
                        # raise

                    # shared.addProperty(tests, "parsedPrimaryVolumeDescriptor", \
                    # str(parsedPrimaryVolumeDescriptor))
                byteStart = byteEnd

        # Read through extended (UDF) volume descriptors (if present)
        noExtendedVolumeDescriptors = 0
        volumeDescriptorIdentifier = "CD001"

        while volumeDescriptorIdentifier in ["CD001", "BEA01", "NSR02", "NSR03", "BOOT2", "TEA01"]:
            volumeDescriptorIdentifier, volumeDescriptorData, byteEnd = \
                udf.getExtendedVolumeDescriptor(isoBytes, byteStart)
            if volumeDescriptorIdentifier in ["BEA01", "NSR02", "NSR03", "BOOT2", "TEA01"]:
                noExtendedVolumeDescriptors += 1

            byteStart = byteEnd

        containsUDF = noExtendedVolumeDescriptors > 0

        if containsUDF:

            # Initialise flags 
            parsedUDFLogicalVolumeDescriptor = False
            parsedUDFLogicalVolumeIntegrityDescriptor = False
            parsedUDFPartitionDescriptor = False

            # Create element to store properties of UDF filesystem
            fsUDF = ET.Element("fileSystem")

            # Read Anchor Volume Descriptor Pointer; located at sector 256
            byteStart = 256*2048
            anchorVolumeDescriptorPointer = isoBytes[byteStart:byteStart + 512]
            descriptorTag = anchorVolumeDescriptorPointer[0:16]
            mainVolumeDescriptorSequenceExtent = anchorVolumeDescriptorPointer[16:24]
            reserveVolumeDescriptorSequenceExtent = anchorVolumeDescriptorPointer[24:32]

            # Descriptor tag fields
            tagIdentifier = bc.bytesToUShortIntL(descriptorTag[0:2])
            descriptorVersion = bc.bytesToUShortIntL(descriptorTag[2:4])

            # Extent fields
            extentLength = bc.bytesToUIntL(mainVolumeDescriptorSequenceExtent[0:4])
            extentLocation = bc.bytesToUIntL(mainVolumeDescriptorSequenceExtent[4:8])

            byteStart = 2048*extentLocation
            noUDFVolumeDescriptors = 0

            # Read through main Volume Descriptor Sequence
            while tagIdentifier != 8 and tagIdentifier != -9999:
                tagIdentifier, volumeDescriptorData, byteEnd = \
                    udf.getVolumeDescriptor(isoBytes, byteStart)
                # sys.stderr.write(str(tagIdentifier) + "\n")

                if tagIdentifier == 6:

                    # Logical Volume descriptor

                    try:
                        lvdInfo = udf.parseLogicalVolumeDescriptor(volumeDescriptorData)
                        fsUDF.append(lvdInfo)
                        parsedUDFLogicalVolumeDescriptor = True

                        # Start sector and length of integrity sequence
                        integritySequenceExtentLocation = \
                            lvdInfo.find("integritySequenceExtentLocation").text
                        integritySequenceExtentLength = \
                            lvdInfo.find("integritySequenceExtentLength").text

                        try:
                            # Read Logical Volume Integrity Descriptor
                            lvidTagIdentifier, lvidVolumeDescriptorData, lVIDbyteEnd = \
                                udf.getVolumeDescriptor(isoBytes,
                                                        2048 * integritySequenceExtentLocation)
                            lvidInfo = udf.parseLogicalVolumeIntegrityDescriptor(lvidVolumeDescriptorData)
                            fsUDF.append(lvidInfo)
                            parsedUDFLogicalVolumeIntegrityDescriptor = True
                        except Exception:
                            parsedUDFLogicalVolumeIntegrityDescriptor = False
                            # raise

                    except Exception:
                        parsedUDFLogicalVolumeDescriptor = False
                        # raise

                    # shared.addProperty(tests, "parsedUDFLogicalVolumeDescriptor", \
                    # str(parsedUDFLogicalVolumeDescriptor))
                    # shared.addProperty(tests, "parsedUDFLogicalVolumeIntegrityDescriptor", \
                    # str(parsedUDFLogicalVolumeIntegrityDescriptor))

                if tagIdentifier == 5:

                    # Partition Descriptor

                    try:
                        pdInfo = udf.parsePartitionDescriptor(volumeDescriptorData)
                        fsUDF.append(pdInfo)
                        parsedUDFPartitionDescriptor = True

                    except Exception:
                        parsedUDFPartitionDescriptor = False
                        # raise

                    # shared.addProperty(tests, "parsedUDFPartitionDescriptor",
                    # str(parsedUDFPartitionDescriptor))

                noUDFVolumeDescriptors += 1
                byteStart = byteEnd

        # Append all fs-specific output to fileSystems element
        if containsISO9660Signature:
            fsISO.attrib["TYPE"] = "ISO 9660"
            fileSystems.append(fsISO)
        if containsHSFSignature:
            fsHSF.attrib["TYPE"] = "High Sierra"
            fileSystems.append(fsHSF)
        if containsAppleFS:
            fsApple.attrib["TYPE"] = fileSystemApple
            fileSystems.append(fsApple)
        if containsUDF:
            fsUDF.attrib["TYPE"] = "UDF"
            fileSystems.append(fsUDF)

        # If no known file systems were found, report this in the tests element
        if len(fileSystems) == 0:
            containsKnownFileSystem = False
        else:
            containsKnownFileSystem = True

        shared.addProperty(tests, "containsKnownFileSystem", str(containsKnownFileSystem))

        # Expected ISO size (bytes) can now be calculated from 6 different places:
        # PVD, High Sierra SFSVolumeDescriptor, Zero Block, Master Directory Block,
        # HFS Plus header or UDF descriptors

        # Intialise all estimates at 0
        sizeExpectedPVD = 0
        sizeExpectedSFSVD = 0
        sizeExpectedZeroBlock = 0
        sizeExpectedMDB = 0
        sizeExpectedHFSPlus = 0
        sizeExpectedUDF = 0

        # Initialise flag
        calculatedSizeExpected = False

        if parsedPrimaryVolumeDescriptor:
            # Calculate from Primary Volume Descriptor
            # Subtracting offset from volumeSpaceSize gives the correct size in case of image
            # from 2nd session of multisession disc
            sizeExpectedPVD = (pvdInfo.find('volumeSpaceSize').text - offset) * \
                pvdInfo.find('logicalBlockSize').text
            # NOTE: this might be off if logicalBlockSize != 2048 (since Sys area and
            # Volume Descriptors are ALWAYS multiples of 2048 bytes!). Also, even for
            # non-hybrid FS actual size is sometimes slightly larger than expected size.
            # Not entirely sure why (padding bytes?)
        
        if parsedSFSVolumeDescriptor:
            # Calculate from Standard File Structure Volume Descriptor
            # in case of HSF file system; calculation is identical to ISO 9660 case
            sizeExpectedSFSVD = (sfsvdInfo.find('volumeSpaceSize').text - offset) * \
                sfsvdInfo.find('logicalBlockSize').text

        if containsApplePartitionMap and parsedAppleZeroBlock:
            # Calculate from zero block in Apple partition
            sizeExpectedZeroBlock = appleZeroBlockInfo.find('blockCount').text * \
                appleZeroBlockInfo.find('blockSize').text

        if containsAppleMasterDirectoryBlock and parsedMasterDirectoryBlock:
            # Calculate from Apple Master Directory Block
            sizeExpectedMDB = masterDirectoryBlockInfo.find('blockCount').text * \
                masterDirectoryBlockInfo.find('blockSize').text

        if containsHFSPlusVolumeHeader and parsedHFSPlusVolumeHeader:
            # Calculate from HFS Plus volume Header
            sizeExpectedHFSPlus = hfsPlusHeaderInfo.find('blockCount').text * \
                hfsPlusHeaderInfo.find('blockSize').text

        if containsUDF and parsedUDFLogicalVolumeDescriptor and \
                parsedUDFLogicalVolumeIntegrityDescriptor:
            # For UDF estimating the expected file size is not straightforward, because the fields
            # in the Partition Descriptor and the Integrity Descriptor exclude the size occupied
            # by descriptors before and after the partition. The number of sectors *before*
            # the partition equals (partitionStartingLocation - 1). The number of sectors *after*
            # the partition is more difficult to establish, but it must be at least 1 (Anchor
            # Volume Descriptor Pointer). So a conservative estimate is:
            #
            # number of sectors =  partitionLength + partitionStartingLocation
            #
            # In reality this estimate may be too low because of additional descriptors after
            # the partition.
            sizeExpectedUDF = (pdInfo.find('partitionLength').text +
                               pdInfo.find('partitionStartingLocation').text) * \
                               lvdInfo.find('logicalBlockSize').text

        # Assuming here that best estimate is largest out of the above values
        sizeExpected = max([sizeExpectedPVD,
                            sizeExpectedSFSVD,
                            sizeExpectedZeroBlock,
                            sizeExpectedMDB,
                            sizeExpectedHFSPlus,
                            sizeExpectedUDF])

        # Size difference
        diffSize = isoFileSize - sizeExpected

        # Size difference, expressed in 2048-byte sectors
        diffSizeSectors = diffSize / 2048

        imageSmallerThanExpected = False

        # If sizeExpected is 0 something is seriously wrong, shouldn't be flagged as expected
        if diffSize == 0 and sizeExpected != 0:
            imageHasExpectedSize = True
        elif diffSize > 0:
            # Image larger than expected, probably OK
            imageHasExpectedSize = False
        else:
            # Image smaller than expected size, probably indicates a problem
            imageHasExpectedSize = False
            imageSmallerThanExpected = True

        shared.addProperty(tests, "sizeExpected", sizeExpected)
        shared.addProperty(tests, "sizeActual", isoFileSize)
        shared.addProperty(tests, "sizeDifference", diffSize)
        shared.addProperty(tests, "sizeDifferenceSectors", diffSizeSectors)
        shared.addProperty(tests, "sizeAsExpected", imageHasExpectedSize)
        shared.addProperty(tests, "smallerThanExpected", imageSmallerThanExpected)

    except Exception as ex:
        success = False
        exceptionType = type(ex)

        if exceptionType == MemoryError:
            failureMessage = "memory error (file size too large)"
        elif exceptionType == IOError:
            failureMessage = "I/O error (cannot open file)"
        elif exceptionType == RuntimeError:
            failureMessage = "runtime error (please report to developers)"
        else:
            failureMessage = "unknown error (please report to developers)"
            raise
        printWarning(failureMessage)

    # Add success outcome to status info
    shared.addProperty(statusInfo, "success", str(success))
    if not success:
        shared.addProperty(statusInfo, "failureMessage", failureMessage)

    imageRoot.append(fileInfo)
    imageRoot.append(statusInfo)
    # Add offset value
    shared.addProperty(imageRoot, "sectorOffset", str(offset))
    imageRoot.append(tests)
    imageRoot.append(fileSystems)

    return imageRoot


def processImages(images, offset):
    """
    Process list of images
    """

    global out
    global err

    out = codecs.getwriter("UTF-8")(sys.stdout.buffer)
    err = codecs.getwriter("UTF-8")(sys.stderr.buffer)

    # Create output element
    root = ET.Element("isolyzer", {'xmlns': nsString,
                                   'xmlns:xsi': xsiNsString,
                                   'xsi:schemaLocation': schemaString})

    # Add some info on isolyzer and the version used
    toolInfo = ET.Element('toolInfo')
    shared.addProperty(toolInfo, "toolName", scriptName)
    shared.addProperty(toolInfo, "toolVersion", __version__)
    root.append(toolInfo)

    for image in images:
        result = processImage(image, offset)
        root.append(result)

    # Write output
    makeHumanReadable(root)
    writeElement(root, out)


def main():
    """Main command line application"""

    # Get input from command line
    args = parseCommandLine()

    # In Linux this works for wildcard expressions (but in Windows this is only a string!)
    if platform.system() == "Windows":
        # Windows doesn't natively handle wildcard expansion, so we need to do it ourselves
        try:
            # This can result in a regex error if filename contains
            # special character
            ISOImages = glob.glob(args.ISOImages[0])
        except re.error:
            # In case of regex error use this fallback 
            escaped = glob.escape(args.ISOImages[0])
            ISOImages = glob.glob(escaped)
    else:
        # In Linux the OS takes care of the wildcard expansion
        ISOImages = args.ISOImages

    # Sector offset
    sectorOffset = args.sectorOffset

    processImages(ISOImages, sectorOffset)


if __name__ == "__main__":
    main()
