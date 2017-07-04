#! /usr/bin/env python
# 
# Verify if size of CD / DVD ISO image matches information in
# ISO 9660 Volume Descriptors (no support for UDF file systems yet)
# 
#
# Copyright (C) 2015, Johan van der Knijff, Koninklijke Bibliotheek -
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

import sys
import os
import time
import imp
import glob
import struct
import re
import time
import codecs
import argparse
import xml.etree.ElementTree as ET
from xml.dom import minidom
if __package__ is None:
    import byteconv as bc
    from six import u
else:
    # Use relative imports if run from package
    from . import byteconv as bc
    from .six import u

scriptPath, scriptName = os.path.split(sys.argv[0])

__version__ = '0.3.0'

# Create parser
parser = argparse.ArgumentParser(
    description="Extract technical information from ISO 9660 image (no support for UDF file systems yet!)")

def main_is_frozen():
    return (hasattr(sys, "frozen") or # new py2exe
        hasattr(sys, "importers") # old py2exe
        or imp.is_frozen("__main__")) # tools/freeze

def get_main_dir():
    if main_is_frozen():
        return os.path.dirname(sys.executable)
    return os.path.dirname(sys.argv[0])
    
def printWarning(msg):
    msgString=("User warning: " + msg +"\n")
    sys.stderr.write(msgString)

def errorExit(msg):
    msgString=("Error: " + msg + "\n")
    sys.stderr.write(msgString)
    sys.exit()

def checkFileExists(fileIn):
    # Check if file exists and exit if not
    if os.path.isfile(fileIn)==False:
        msg=fileIn + " does not exist"
        errorExit(msg)
    
def readFileBytes(file,byteStart,noBytes):
    # Read file, return contents as a byte object

    # Open file
    f = open(file,"rb")

    # Set position to byteStart
    f.seek(byteStart)

    # Put contents of file into a byte object.
    fileData=f.read(noBytes)
    f.close()

    return(fileData)

def makeHumanReadable(element, remapTable={}):
    # Takes element object, and returns a modified version in which all
    # non-printable 'text' fields (which may contain numeric data or binary strings)
    # are replaced by printable strings
    #
    # Property values in original tree may be mapped to alternative (more user-friendly)
    # reportable values using a remapTable, which is a nested dictionary.
    # TODO: add to separate module

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
        # which is dependent on the Python version used

        if sys.version.startswith("2"):
            # Python 2.x
            numericTypes = [int, long, float, bool]
            # Long type is deprecated in Python 3.x!
        else:
            numericTypes = [int, float, bool]

        # Convert

        if remappedValue != None:
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

def addProperty(element, tag, text):
        # Append childnode with text

        el = ET.SubElement(element, tag)
        el.text = text

def writeElement(elt, codec):
    # Writes element as XML to stdout using defined codec

    # Element to string
    if sys.version.startswith("2"):
        xmlOut = ET.tostring(elt, 'UTF-8', 'xml')
    if sys.version.startswith("3"):
        xmlOut = ET.tostring(elt, 'unicode', 'xml')

    # Make xml pretty
    xmlPretty = minidom.parseString(xmlOut).toprettyxml('    ')
 
    """
    # Steps to get rid of xml declaration:
    # String to list
    xmlAsList = xmlPretty.split("\n")
    # Remove first item (xml declaration)
    del xmlAsList[0]
    # Convert back to string
    xmlOut = "\n".join(xmlAsList)
    """
    xmlOut = xmlPretty
       
    # Write output
    codec.write(xmlOut)
    
def stripSurrogatePairs(ustring):

    # Removes surrogate pairs from a Unicode string

    # This works for Python 3.x, but not for 2.x!
    # Source: http://stackoverflow.com/q/19649463/1209004

    if sys.version.startswith("3"):
        try:
            ustring.encode('utf-8')
        except UnicodeEncodeError:
            # Strip away surrogate pairs
            tmp = ustring.encode('utf-8', 'surrogateescape')
            ustring = tmp.decode('utf-8', 'ignore')

    # In Python 2.x we need to use regex
    # Source: http://stackoverflow.com/a/18674109/1209004

    if sys.version.startswith("2"):
        # Generate regex for surrogate pair detection

        lone = re.compile(
            u(r"""(?x)            # verbose expression (allows comments)
            (                    # begin group
            [\ud800-\udbff]      #   match leading surrogate
            (?![\udc00-\udfff])  #   but only if not followed by trailing surrogate
            )                    # end group
            |                    #  OR
            (                    # begin group
            (?<![\ud800-\udbff]) #   if not preceded by leading surrogate
            [\udc00-\udfff]      #   match trailing surrogate
            )                   # end group
            """))
   
        # Remove surrogates (i.e. replace by empty string) 
        tmp = lone.sub(r'',ustring).encode('utf-8')
        ustring = tmp.decode('utf-8')

    return(ustring)

def signatureCheck(bytesData):
    # Check if file matches binary signature for ISO9660
    # (Check for occurrence at offsets 32769 and 34817; 
    # apparently 3rd ocurrece at offset 36865 is optional)
    """
    print("Signature matches:")
    print(str("offset 32669: " + bytesData[32769:32774]))
    print(str("offset 34817: " + bytesData[34817:34822]))
    print(str("offset 36865: " + bytesData[36865:36870]))
    """
    if bytesData[32769:32774] == b'CD001'\
        and bytesData[34817:34822] == b'CD001':
        iso9660Match = True
    else:
        iso9660Match = False
    
    return(iso9660Match)

def decDateTimeToDate(datetime):
    # Convert 17 bit dec-datetime field to formatted  date-time string
    # TODO: incorporate time zone offset into result
    try:
        year = int(bc.bytesToText(datetime[0:4]))
        month = int(bc.bytesToText(datetime[4:6]))
        day = int(bc.bytesToText(datetime[6:8]))
        hour = int(bc.bytesToText(datetime[8:10]))
        minute = int(bc.bytesToText(datetime[10:12]))
        second = int(bc.bytesToText(datetime[12:14]))
        hundrethSecond = int(bc.bytesToText(datetime[14:16]))
        timeZoneOffset = bc.bytesToUnsignedChar(datetime[16:17])
        dateString = "%d/%02d/%02d" % (year, month, day)
        timeString = "%02d:%02d:%02d" % (hour, minute, second)
        dateTimeString = "%s, %s" % (dateString, timeString)
    except ValueError:
        dateTimeString=""
    return(dateTimeString)
    
def getISOVolumeDescriptor(bytesData, byteStart):

    # Read one 2048-byte ISO volume descriptor and return its descriptor
    # code and contents
    byteEnd = byteStart + 2048
    volumeDescriptorType = bc.bytesToUnsignedChar(bytesData[byteStart:byteStart+1])
    volumeDescriptorData = bytesData[byteStart:byteEnd]
    
    return(volumeDescriptorType, volumeDescriptorData, byteEnd)
    
def getExtendedVolumeDescriptor(bytesData, byteStart):

    # Read one 2048-byte extended (UDF only) volume descriptor and return its descriptor
    # code and contents
    byteEnd = byteStart + 2048
    volumeDescriptorIdentifier = bc.bytesToText(bytesData[byteStart+1:byteStart+6])
    volumeDescriptorData = bytesData[byteStart:byteEnd]
    
    return(volumeDescriptorIdentifier, volumeDescriptorData, byteEnd)

def getUDFVolumeDescriptor(bytesData, byteStart):
    byteEnd = byteStart + 2048
    volumeDescriptorData = bytesData[byteStart:byteEnd]
    
    # Descriptor tag
    descriptorTag  = volumeDescriptorData[0:16]
    tagIdentifier = bc.bytesToUShortIntL(descriptorTag[0:2]) 
    descriptorVersion = bc.bytesToUShortIntL(descriptorTag[2:4])
       
    return(tagIdentifier, volumeDescriptorData, byteEnd)
    
def parsePrimaryVolumeDescriptor(bytesData):

    # Set up elemement object to store extracted properties
    properties = ET.Element("primaryVolumeDescriptor")
           
    addProperty(properties, "typeCode", bc.bytesToUnsignedChar(bytesData[0:1]))
    addProperty(properties, "standardIdentifier", bc.bytesToText(bytesData[1:6]))
    addProperty(properties, "version", bc.bytesToUnsignedChar(bytesData[6:7]))
    addProperty(properties, "systemIdentifier", bc.bytesToText(bytesData[8:40]))
    addProperty(properties, "volumeIdentifier", bc.bytesToText(bytesData[40:72]))

    # Fields below are stored as both little-endian and big-endian; only
    # big-endian values read here!
    
    # Number of Logical Blocks in which the volume is recorded
    addProperty(properties, "volumeSpaceSize", bc.bytesToUInt(bytesData[84:88]))
    # The size of the set in this logical volume (number of disks)
    addProperty(properties, "volumeSetSize", bc.bytesToUShortInt(bytesData[122:124]))
    # The number of this disk in the Volume Set
    addProperty(properties, "volumeSequenceNumber", bc.bytesToUShortInt(bytesData[126:128]))
    # The size in bytes of a logical block
    addProperty(properties, "logicalBlockSize", bc.bytesToUShortInt(bytesData[130:132]))
    # The size in bytes of the path table
    addProperty(properties, "pathTableSize", bc.bytesToUInt(bytesData[136:140]))
	# Location of Type-L Path Table (note this is stored as little-endian only, hence
	# byte swap!)
    addProperty(properties, "typeLPathTableLocation", bc.swap32(bc.bytesToUInt(bytesData[140:144])))
    # Location of Optional Type-L Path Table
    addProperty(properties, "optionalTypeLPathTableLocation", bc.swap32(bc.bytesToUInt(bytesData[144:148])))
    # Location of Type-M Path Table
    addProperty(properties, "typeMPathTableLocation", bc.bytesToUInt(bytesData[148:152]))
    # Location of Optional Type-M Path Table
    addProperty(properties, "optionalTypeMPathTableLocation", bc.bytesToUInt(bytesData[152:156]))

    # Following fields are all text strings
    addProperty(properties, "volumeSetIdentifier", bc.bytesToText(bytesData[190:318]))
    addProperty(properties, "publisherIdentifier", bc.bytesToText(bytesData[318:446]))
    addProperty(properties, "dataPreparerIdentifier", bc.bytesToText(bytesData[446:574]))
    addProperty(properties, "applicationIdentifier", bc.bytesToText(bytesData[574:702]))
    addProperty(properties, "copyrightFileIdentifier", bc.bytesToText(bytesData[702:740]))
    addProperty(properties, "abstractFileIdentifier", bc.bytesToText(bytesData[740:776]))
    addProperty(properties, "bibliographicFileIdentifier", bc.bytesToText(bytesData[776:813]))
    
    # Following fields are all date-time values    
    addProperty(properties, "volumeCreationDateAndTime", decDateTimeToDate(bytesData[813:830]))
    addProperty(properties, "volumeModificationDateAndTime", decDateTimeToDate(bytesData[830:847]))
    addProperty(properties, "volumeExpirationDateAndTime", decDateTimeToDate(bytesData[847:864]))
    addProperty(properties, "volumeEffectiveDateAndTime", decDateTimeToDate(bytesData[864:881]))
    
    addProperty(properties, "fileStructureVersion", bc.bytesToUnsignedChar(bytesData[881:882]))
    
    return(properties)

def parseUDFLogicalVolumeDescriptor(bytesData):

    # Set up elemement object to store extracted properties
    properties = ET.Element("logicalVolumeDescriptor")
    addProperty(properties, "tagIdentifier", bc.bytesToUShortIntL(bytesData[0:2]))
    addProperty(properties, "descriptorVersion", bc.bytesToUShortIntL(bytesData[2:4]))
    addProperty(properties, "tagSerialNumber", bc.bytesToUShortIntL(bytesData[6:8]))
    addProperty(properties, "volumeSequenceNumber", bc.bytesToUIntL(bytesData[16:20]))
    # TODO: really don't know how to interpret descriptorCharacterSet, report as
    # binhex for now
    # addProperty(properties, "descriptorCharacterSet", bc.bytesToHex(bytesData[64:84]))
    # TODO: is bytesToText encoding-safe here? Don't really understand this OSTA compressed
    # Unicode at all!
    # addProperty(properties, "compressionID", bc.bytesToUnsignedCharL(bytesData[84:85]))
    # Below line works for UTF-8
    addProperty(properties, "logicalVolumeIdentifier", bc.bytesToText(bytesData[85:212]))
    addProperty(properties, "logicalBlockSize", bc.bytesToUIntL(bytesData[212:216]))
    addProperty(properties, "domainIdentifier", bc.bytesToText(bytesData[216:248]))
    addProperty(properties, "mapTableLength", bc.bytesToUIntL(bytesData[264:268]))
    addProperty(properties, "numberOfPartitionMaps", bc.bytesToUIntL(bytesData[268:272]))
    addProperty(properties, "implementationIdentifier", bc.bytesToText(bytesData[272:304]))
    addProperty(properties, "integritySequenceExtentLength", bc.bytesToUIntL(bytesData[432:436]))
    addProperty(properties, "integritySequenceExtentLocation", bc.bytesToUIntL(bytesData[436:440]))
    return(properties)
    
def parseUDFLogicalVolumeIntegrityDescriptor(bytesData):

    # Note: parser based on ECMA TR/71 DVD Read-Only Disk - File System Specifications 
    # Link: https://www.ecma-international.org/publications/techreports/E-TR-071.htm
    #
    # This puts constraint that *freeSpaceTable* and *sizeTable* describe one partition only!
    # Not 100% sure this applies to *all* DVDs (since TR/71 only defines UDF Bridge format!) 
    # If not, make these fields repeatable, iterating over *numberOfPartitions*!

    # Set up elemement object to store extracted properties
    properties = ET.Element("logicalVolumeIntegrityDescriptor")
    addProperty(properties, "tagIdentifier", bc.bytesToUShortIntL(bytesData[0:2]))
    addProperty(properties, "descriptorVersion", bc.bytesToUShortIntL(bytesData[2:4]))
    addProperty(properties, "tagSerialNumber", bc.bytesToUShortIntL(bytesData[6:8]))
    
    # Read timestamp fields and reformat to date/time string (ignoring centiseconds ... microseconds)
    year = bc.bytesToUShortIntL(bytesData[18:20])
    month = bc.bytesToUnsignedCharL(bytesData[20:21])
    day = bc.bytesToUnsignedCharL(bytesData[21:22])
    hour = bc.bytesToUnsignedCharL(bytesData[22:23])
    minute = bc.bytesToUnsignedCharL(bytesData[23:24])
    second = bc.bytesToUnsignedCharL(bytesData[24:25])
    dateString = "%d/%02d/%02d" % (year, month, day)
    timeString = "%02d:%02d:%02d" % (hour, minute, second)
    dateTimeString = "%s, %s" % (dateString, timeString)
    addProperty(properties, "timeStamp", dateTimeString)
    
    addProperty(properties, "integrityType", bc.bytesToUIntL(bytesData[28:32]))
    addProperty(properties, "numberOfPartitions", bc.bytesToUIntL(bytesData[72:76]))
    addProperty(properties, "lengthOfImplementationUse", bc.bytesToUIntL(bytesData[76:80]))
    addProperty(properties, "freeSpaceTable", bc.bytesToUIntL(bytesData[80:84]))
    addProperty(properties, "sizeTable", bc.bytesToUIntL(bytesData[84:88]))
    
    return(properties)
    
def parseUDFPartitionDescriptor(bytesData):

    # Set up elemement object to store extracted properties
    properties = ET.Element("partitionDescriptor")
    addProperty(properties, "tagIdentifier", bc.bytesToUShortIntL(bytesData[0:2]))
    addProperty(properties, "descriptorVersion", bc.bytesToUShortIntL(bytesData[2:4]))
    addProperty(properties, "tagSerialNumber", bc.bytesToUShortIntL(bytesData[6:8]))
      
    addProperty(properties, "volumeDescriptorSequenceNumber", bc.bytesToUIntL(bytesData[16:20]))
    addProperty(properties, "partitionNumber", bc.bytesToUShortIntL(bytesData[22:24]))
    addProperty(properties, "accessType", bc.bytesToUIntL(bytesData[184:188]))
    addProperty(properties, "partitionStartingLocation", bc.bytesToUIntL(bytesData[188:192]))
    addProperty(properties, "partitionLength", bc.bytesToUIntL(bytesData[192:196]))

    return(properties)

def parseAppleZeroBlock(bytesData):

    # Based on code at:
    # https://opensource.apple.com/source/IOStorageFamily/IOStorageFamily-116/IOApplePartitionScheme.h

    # Set up elemement object to store extracted properties
    properties = ET.Element("appleZeroBlock")
            
    addProperty(properties, "signature", bc.bytesToText(bytesData[0:2]))
    addProperty(properties, "blockSize", bc.bytesToUShortInt(bytesData[2:4]))
    addProperty(properties, "blockCount", bc.bytesToUInt(bytesData[4:8]))
    addProperty(properties, "deviceType", bc.bytesToUShortInt(bytesData[8:10]))
    addProperty(properties, "deviceID", bc.bytesToUShortInt(bytesData[10:12]))
    addProperty(properties, "driverData", bc.bytesToUInt(bytesData[12:16])) 
    addProperty(properties, "driverDescriptorCount", bc.bytesToUShortInt(bytesData[80:82]))
    addProperty(properties, "driverDescriptorBlockStart", bc.bytesToUInt(bytesData[82:86]))
    addProperty(properties, "driverDescriptorBlockCount", bc.bytesToUShortInt(bytesData[86:88]))
    addProperty(properties, "driverDescriptorSystemType", bc.bytesToUShortInt(bytesData[88:90]))
        
    return(properties)

def parseApplePartitionMap(bytesData):

    # Based on description at:
    # https://en.wikipedia.org/wiki/Apple_Partition_Map#Layout
    # and code at:
    # https://opensource.apple.com/source/IOStorageFamily/IOStorageFamily-116/IOApplePartitionScheme.h
    # Variable naming mostly follows Apple's code. 

    # Set up elemement object to store extracted properties
    properties = ET.Element("applePartitionMap")
             
    addProperty(properties, "signature", bc.bytesToText(bytesData[0:2]))
    addProperty(properties, "numberOfPartitionEntries", bc.bytesToUInt(bytesData[4:8]))
    addProperty(properties, "partitionBlockStart", bc.bytesToUInt(bytesData[8:12]))
    addProperty(properties, "partitionBlockCount", bc.bytesToUInt(bytesData[12:16]))
    addProperty(properties, "partitionName", bc.bytesToText(bytesData[16:48]))
    addProperty(properties, "partitionType", bc.bytesToText(bytesData[48:80]))
    addProperty(properties, "partitionLogicalBlockStart", bc.bytesToUInt(bytesData[80:84]))
    addProperty(properties, "partitionLogicalBlockCount", bc.bytesToUInt(bytesData[84:88]))
    addProperty(properties, "partitionFlags", bc.bytesToUInt(bytesData[88:92]))
    addProperty(properties, "bootCodeBlockStart", bc.bytesToUInt(bytesData[92:96]))
    addProperty(properties, "bootCodeSizeInBytes", bc.bytesToUInt(bytesData[96:100]))
    addProperty(properties, "bootCodeLoadAddress", bc.bytesToUInt(bytesData[100:104]))
    addProperty(properties, "bootCodeJumpAddress", bc.bytesToUInt(bytesData[108:112]))
    addProperty(properties, "bootCodeChecksum", bc.bytesToUInt(bytesData[116:120]))
    addProperty(properties, "processorType", bc.bytesToText(bytesData[120:136]))
    return(properties)
    
def parseMasterDirectoryBlock(bytesData):
    # Based on description at:
    # https://developer.apple.com/legacy/library/documentation/mac/Files/Files-102.html
    # and https://github.com/libyal/libfshfs/blob/master/documentation/Hierarchical%20File%20System%20(HFS).asciidoc

    # Set up elemement object to store extracted properties
    properties = ET.Element("masterDirectoryBlock")
             
    addProperty(properties, "signature", bc.bytesToText(bytesData[0:2]))
    addProperty(properties, "blockSize", bc.bytesToUShortInt(bytesData[18:20]))
    addProperty(properties, "blockCount", bc.bytesToUInt(bytesData[20:24]))
    addProperty(properties, "volumeName", bc.bytesToText(bytesData[37:63]))
    return(properties)

def parseHFSPlusVolumeHeader(bytesData):

    # Based on https://opensource.apple.com/source/xnu/xnu-344/bsd/hfs/hfs_format.h
    
    # Set up elemement object to store extracted properties
    properties = ET.Element("hfsPlusVolumeheader")
             
    addProperty(properties, "signature", bc.bytesToText(bytesData[0:2]))
    addProperty(properties, "version", bc.bytesToUShortInt(bytesData[2:4]))
    addProperty(properties, "blockSize", bc.bytesToUInt(bytesData[40:44]))
    addProperty(properties, "blockCount", bc.bytesToUInt(bytesData[44:48]))
    
    return(properties)

def parseCommandLine():
    # Add arguments
    parser.add_argument('ISOImage', 
        action = "store", 
        type = str, 
        help = "input ISO image(s) (wildcards allowed)")
    parser.add_argument('--version', '-v',
        action = 'version', 
        version = __version__)
    parser.add_argument('--offset','-o',
        type = int,
        help = "offset (in sectors) of ISO image on CD (analogous to -N option in cdinfo)",
        action = 'store',
        dest = 'sectorOffset',
        default = 0)

    # Parse arguments
    args=parser.parse_args()

    return(args)

def processImage(image, offset):

    # Does image exist?
    checkFileExists(image)

    # Create root element for image
    imageRoot = ET.Element('image')

    # Create elements for storing file and status meta info
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
    addProperty(fileInfo, "fileName", fileNameCleaned)
    addProperty(fileInfo, "filePath", filePathCleaned)
    addProperty(fileInfo, "fileSizeInBytes", str(os.path.getsize(image)))
    try:
        lastModifiedDate = time.ctime(os.path.getmtime(image))
    except ValueError:
        # Dates earlier than 1 Jan 1970 can raise ValueError on Windows
        # Workaround: replace by lowest possible value (typically 1 Jan 1970)
        lastModifiedDate = time.ctime(0)
    addProperty(fileInfo, "fileLastModified", lastModifiedDate)
    
    tests = properties = ET.Element("tests")
    properties = ET.Element("properties")
    fileSystems = ET.Element("fileSystems")
    
    # Initialise success flag
    success = True
   
    try:    
        # Get file size in bytes
        isoFileSize = os.path.getsize(image)
        
        # Set no. of sectors to read.
        sectorsToRead = 1000
        
        # Flag indicates whether a file system could be detected at all
        containsSupportedFileSystem = False
        containsAppleMasterDirectoryBlock = False
        containsHFSPlusVolumeHeader = False
        
        byteStart = 0  
        noBytes = min(sectorsToRead*2048,isoFileSize)
        isoBytes = readFileBytes(image, byteStart,noBytes)
        
        # Does image match byte signature for an ISO 9660 image?
        containsISO9660Signature = signatureCheck(isoBytes)
        addProperty(fileSystems, "fileSystem", "ISO9660")
        addProperty(tests, "containsISO9660Signature", containsISO9660Signature)
        
        # Does image contain Apple Partition Map?
        containsApplePartitionMap = isoBytes[0:2] == b'\x45\x52' and isoBytes[512:514] == b'\x50\x4D'
        
        # Does image contain HFS Plus Header or Master Directory Block? This also allows us to identify the
        # specific file system
        # (Note: the HFS Plus Header replaces the Master Directory Block of HFS) 
        
        if isoBytes[1024:1026] == b'\x42\x44':
            # Hierarchical File System
            containsAppleMasterDirectoryBlock = True
            addProperty(fileSystems, "fileSystem", "HFS")
        if isoBytes[1024:1026] == b'\xd2\xd7':
            # Macintosh File System
            containsAppleMasterDirectoryBlock = True
            addProperty(fileSystems, "fileSystem", "MFS")
        if isoBytes[1024:1026] ==  b'\x48\x2B':
            # HFS Plus
            containsHFSPlusVolumeHeader = True
            addProperty(fileSystems, "fileSystem", "HFS+")
        if isoBytes[1024:1026] ==  b'\x48\x58':
            # HFS X (record as HFS+ for consistency with Partition Map fields)
            containsHFSPlusVolumeHeader = True
            addProperty(fileSystems, "fileSystem", "HFS+")           
  
        addProperty(tests, "containsApplePartitionMap", containsApplePartitionMap)
        addProperty(tests, "containsHFSPlusVolumeHeader", containsHFSPlusVolumeHeader)
        addProperty(tests, "containsAppleMasterDirectoryBlock", containsAppleMasterDirectoryBlock)
        
        if containsApplePartitionMap == True:
        
            containsSupportedFileSystem = True
                   
            # Based on description at: https://en.wikipedia.org/wiki/Apple_Partition_Map#Layout
            # and https://opensource.apple.com/source/IOStorageFamily/IOStorageFamily-116/IOApplePartitionScheme.h
                       
            # Get zero block data
            appleZeroBlockData = isoBytes[0:512]
            try:
                appleZeroBlockInfo = parseAppleZeroBlock(appleZeroBlockData)
                properties.append(appleZeroBlockInfo)
                parsedAppleZeroBlock = True
            except:
                parsedAppleZeroBlock = False
            
            addProperty(tests, "parsedAppleZeroBlock", str(parsedAppleZeroBlock))
            
            # Set up list to store all values of 'partionType' in partition map
            partitionTypes = [] 
            
            # Get partition map data
            applePartitionMapData = isoBytes[512:1024]
            try:
                applePartitionMapInfo = parseApplePartitionMap(applePartitionMapData)
                # Add partition type value to list
                partitionTypes.append(applePartitionMapInfo.find('partitionType').text)
                properties.append(applePartitionMapInfo)
                parsedApplePartitionMap = True
            except:
                parsedApplePartitionMap = False
                
            addProperty(tests, "parsedApplePartitionMap", str(parsedApplePartitionMap))
            
            # Iterate over remaining partition map entries
            pOffset = 1024
            for pMap in range(0, applePartitionMapInfo.find('numberOfPartitionEntries').text - 1):
                applePartitionMapData = isoBytes[pOffset:pOffset+512]
                try:
                    applePartitionMapInfo = parseApplePartitionMap(applePartitionMapData)
                    # Add partition type value to list
                    partitionTypes.append(applePartitionMapInfo.find('partitionType').text)
                    properties.append(applePartitionMapInfo)
                    parsedApplePartitionMap = True
                except:
                    parsedApplePartitionMap = False
               
                pOffset += 512
            
            # Establish file system type from partitionType values in all partition maps
            # Source: https://en.wikipedia.org/wiki/Apple_Partition_Map#Partition_identifiers
            # Note that this doesn't cover all possible types (but no idea if any of the other types
            # are used for optical media) 
            
            if 'Apple_MFS' in partitionTypes:
                # Macintosh File System
                addProperty(fileSystems, "fileSystem", "MFS")
            if 'Apple_HFS' in partitionTypes:
                # Hierarchical File System
                addProperty(fileSystems, "fileSystem", "HFS")
            if 'Apple_HFSX' in partitionTypes:
                # HFS Plus
                addProperty(fileSystems, "fileSystem", "HFS+")
                
        if containsHFSPlusVolumeHeader == True:
                        
            containsSupportedFileSystem = True
                      
            hfsPlusHeaderData = isoBytes[1024:1536]
            try:
                hfsPlusHeaderInfo = parseHFSPlusVolumeHeader(hfsPlusHeaderData)
                properties.append(hfsPlusHeaderInfo)
                parsedHFSPlusVolumeHeader = True
            except:
                parsedHFSPlusVolumeHeader = False
            
            addProperty(tests, "parsedHFSPlusVolumeHeader", str(parsedHFSPlusVolumeHeader))
                    
        if containsAppleMasterDirectoryBlock == True:
        
            containsSupportedFileSystem = True
            
            masterDirectoryBlockData = isoBytes[1024:1536] # Size of MDB?
            try:
                masterDirectoryBlockInfo = parseMasterDirectoryBlock(masterDirectoryBlockData)
                properties.append(masterDirectoryBlockInfo)
                parsedMasterDirectoryBlock = True
            except:
                parsedMasterDirectoryBlock = False
            
            addProperty(tests, "parsedMasterDirectoryBlock", str(parsedMasterDirectoryBlock))

        # This is a dummy value
        volumeDescriptorType = -1
        
        # Count volume descriptors
        noISOVolumeDescriptors = 0
        
        # Default value
        parsedPrimaryVolumeDescriptor = False

        # Skip to byte 32768, which is where actual ISO 9660 fields start
        byteStart = 32768
        
        if containsISO9660Signature == True:
        
            containsSupportedFileSystem = True

            # Read through all 2048-byte ISO volume descriptors, until Volume Descriptor Set Terminator is found
            # (or unexpected EOF, which will result in -9999 value for volumeDescriptorType)
            while volumeDescriptorType != 255 and volumeDescriptorType != -9999:
            
                volumeDescriptorType, volumeDescriptorData, byteEnd = getISOVolumeDescriptor(isoBytes, byteStart)
                noISOVolumeDescriptors += 1
                
                if volumeDescriptorType == 1:
                    # Get info from Primary Volume Descriptor (as element object)
                    try:
                        pvdInfo = parsePrimaryVolumeDescriptor(volumeDescriptorData)
                        properties.append(pvdInfo)
                        parsedPrimaryVolumeDescriptor = True
                    except:
                        parsedPrimaryVolumeDescriptor = False
                        
                    addProperty(tests, "parsedPrimaryVolumeDescriptor", str(parsedPrimaryVolumeDescriptor))             
                byteStart = byteEnd
        
        # Read through extended (UDF) volume descriptors (if present)
        
        noExtendedVolumeDescriptors = 0
        volumeDescriptorIdentifier = "CD001"
                
        while volumeDescriptorIdentifier in ["CD001", "BEA01", "NSR02", "NSR03", "BOOT2", "TEA01"]:
            volumeDescriptorIdentifier, volumeDescriptorData, byteEnd = getExtendedVolumeDescriptor(isoBytes, byteStart)
            if volumeDescriptorIdentifier in ["BEA01", "NSR02", "NSR03", "BOOT2", "TEA01"]:
                noExtendedVolumeDescriptors += 1
     
            byteStart = byteEnd
         
        containsUDF = noExtendedVolumeDescriptors > 0
        if containsUDF:
            addProperty(fileSystems, "fileSystem", "UDF")     
        addProperty(tests, "containsUDF", containsUDF)

        if containsUDF == True:
        
            containsSupportedFileSystem = True
        
            # Create udf subelement in properties tree
            udf = ET.Element("udf")
            
            # Read Anchor Volume Descriptor Pointer; located at sector 256
            byteStart = 256*2048
            anchorVolumeDescriptorPointer = isoBytes[byteStart:byteStart + 512]
            descriptorTag  = anchorVolumeDescriptorPointer[0:16]
            mainVolumeDescriptorSequenceExtent = anchorVolumeDescriptorPointer[16:24]
            reserveVolumeDescriptorSequenceExtent  = anchorVolumeDescriptorPointer[24:32]
            
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
                tagIdentifier, volumeDescriptorData, byteEnd = getUDFVolumeDescriptor(isoBytes, byteStart)
                #sys.stderr.write(str(tagIdentifier) + "\n")
                
                if tagIdentifier == 6:
                
                    # Logical Volume descriptor
                
                    try:
                        lvdInfo = parseUDFLogicalVolumeDescriptor(volumeDescriptorData)
                        udf.append(lvdInfo)
                        parsedUDFLogicalVolumeDescriptor = True
                        
                        # Start sector and length of integrity sequence
                        integritySequenceExtentLocation = lvdInfo.find("integritySequenceExtentLocation").text
                        integritySequenceExtentLength = lvdInfo.find("integritySequenceExtentLength").text
                        
                        try:
                            # Read Logical Volume Integrity Descriptor
                            lvidTagIdentifier, lvidVolumeDescriptorData, lVIDbyteEnd = getUDFVolumeDescriptor(isoBytes, 2048* integritySequenceExtentLocation)
                            lvidInfo = parseUDFLogicalVolumeIntegrityDescriptor(lvidVolumeDescriptorData)
                            udf.append(lvidInfo)                        
                            parsedUDFLogicalVolumeIntegrityDescriptor = True
                                                        
                        except:
                            parsedUDFLogicalVolumeIntegrityDescriptor = False
                            #raise
                        
                    except:
                        parsedUDFLogicalVolumeDescriptor = False
                        #raise
                    
                    addProperty(tests, "parsedUDFLogicalVolumeDescriptor", str(parsedUDFLogicalVolumeDescriptor))
                    addProperty(tests, "parsedUDFLogicalVolumeIntegrityDescriptor", str(parsedUDFLogicalVolumeIntegrityDescriptor))
                    
                if tagIdentifier == 5:
                    
                    # Partition Descriptor
                
                    try:
                        pdInfo = parseUDFPartitionDescriptor(volumeDescriptorData)
                        udf.append(pdInfo)
                        parsedUDFPartitionDescriptor = True
                                                
                    except:
                        parsedUDFPartitionDescriptor = False
                        #raise
                    
                    addProperty(tests, "parsedUDFPartitionDescriptor", str(parsedUDFPartitionDescriptor))
 
                
                noUDFVolumeDescriptors += 1
                byteStart = byteEnd
            
            # Append udf element to properties    
            properties.append(udf)
        
        addProperty(tests, "containsSupportedFileSystem", str(containsSupportedFileSystem))
        properties.append(fileSystems)
                
        calculatedSizeExpected = False
        
        # Expected ISO size (bytes) can now be calculated from 5 different places: 
        # PVD, Zero Block, Master Directory Block, HFS Plus header or UDF descriptors

        # Intialise all estimates at 0
        sizeExpectedPVD = 0
        sizeExpectedZeroBlock = 0
        sizeExpectedMDB = 0
        sizeExpectedHFSPlus = 0
        sizeExpectedUDF = 0

        if parsedPrimaryVolumeDescriptor == True:
            # Calculate from Primary Volume Descriptor
            # Subtracting offset from volumeSpaceSize gives the correct size in case of image from 2nd session of multisession disc
            sizeExpectedPVD = (pvdInfo.find('volumeSpaceSize').text - offset) * pvdInfo.find('logicalBlockSize').text
            # NOTE: this might be off if logicalBlockSize != 2048 (since Sys area and Volume Descriptors
            # are ALWAYS multiples of 2048 bytes!). Also, even for non-hybrid FS actual size is sometimes slightly larger than expected size.
            # Not entirely sure why (padding bytes?)
                
        if containsApplePartitionMap == True and parsedAppleZeroBlock == True:   
            # Calculate from zero block in Apple partition 
            sizeExpectedZeroBlock = appleZeroBlockInfo.find('blockCount').text * appleZeroBlockInfo.find('blockSize').text

        if containsAppleMasterDirectoryBlock == True and parsedMasterDirectoryBlock == True:
            # Calculate from Apple Master Directory Block 
            sizeExpectedMDB = masterDirectoryBlockInfo.find('blockCount').text * masterDirectoryBlockInfo.find('blockSize').text
            
        if containsHFSPlusVolumeHeader == True and parsedHFSPlusVolumeHeader == True:
            # Calculate from HFS Plus volume Header 
            sizeExpectedHFSPlus = hfsPlusHeaderInfo.find('blockCount').text * hfsPlusHeaderInfo.find('blockSize').text
            
        if containsUDF == True and parsedUDFLogicalVolumeDescriptor == True and parsedUDFLogicalVolumeIntegrityDescriptor == True:
            # For UDF estimating the expected file size is not straightforward, because the fields in the Partition Descriptor and the
            # Integrity Descriptor exclude the size occupied by descriptors before and after the partition. The number of sectors *before*
            # the partition equals (partitionStartingLocation - 1). The number of sectors *after* the partition is more difficult to 
            # establish, but it must be at least 1 (Anchor Volume Descriptor Pointer). So a conservative estimate is:
            #
            # number of sectors =  partitionLength + partitionStartingLocation
            # 
            # In reality this estimate may be too low because of additional descriptors after the partition.
            sizeExpectedUDF = (pdInfo.find('partitionLength').text +  pdInfo.find('partitionStartingLocation').text)* lvdInfo.find('logicalBlockSize').text

        # Assuming here that best estimate is largest out of the above values
        sizeExpected = max([sizeExpectedPVD, sizeExpectedZeroBlock, sizeExpectedMDB, sizeExpectedHFSPlus, sizeExpectedUDF])

        # Size difference
        diffSize = isoFileSize - sizeExpected
        
        imageLargerThanExpected = False
        imageSmallerThanExpected = False
        
        # If sizeExpected is 0 something is seriously wrong, which shouldn't be flagged as expected 
        if diffSize == 0 and sizeExpected != 0:
            imageHasExpectedSize = True
        elif diffSize > 0:
            # Image larger than expected, probably OK
            imageHasExpectedSize = False
            imageLargerThanExpected = True
        else:
            # Image smaller than expected size, probably indicates a problem
            imageHasExpectedSize = False
            imageSmallerThanExpected = True
            
        addProperty(tests, "sizeExpected", sizeExpected)
        addProperty(tests, "sizeActual", isoFileSize)
        addProperty(tests, "sizeDifference", diffSize) 
        addProperty(tests, "sizeAsExpected", imageHasExpectedSize)
        addProperty(tests, "smallerThanExpected", imageSmallerThanExpected)

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
            #raise
        printWarning(failureMessage)

     # Add success outcome to status info
    addProperty(statusInfo, "success", str(success))
    if success == False:
        addProperty(statusInfo, "failureMessage", failureMessage)
   
    imageRoot.append(fileInfo)
    imageRoot.append(statusInfo)
    imageRoot.append(tests)
    imageRoot.append(properties)
    
    return(imageRoot)

def main():

    global out
    global err

    # Set encoding of the terminal to UTF-8
    if sys.version.startswith("2"):
        out = codecs.getwriter("UTF-8")(sys.stdout)
        err = codecs.getwriter("UTF-8")(sys.stderr)
    elif sys.version.startswith("3"):
        out = codecs.getwriter("UTF-8")(sys.stdout.buffer)
        err = codecs.getwriter("UTF-8")(sys.stderr.buffer)

    # Get input from command line
    args = parseCommandLine()
         
    # Input
    ISOImages =  glob.glob(args.ISOImage)
    
    # Sector offset
    sectorOffset = args.sectorOffset    
    root = ET.Element("isolyzer")
      
    
    for image in ISOImages:
        result = processImage(image,sectorOffset)
        root.append(result)
    
    # Write output
    makeHumanReadable(root)
    writeElement(root, out)
 
if __name__ == "__main__":
    main()

