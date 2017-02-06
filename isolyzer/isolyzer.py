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

__version__ = '0.2.2'

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
    
def getVolumeDescriptor(bytesData, byteStart):

    # Read one 2048-byte volume descriptor and return its descriptor
    # code and contents
    byteEnd = byteStart + 2048
    volumeDescriptorType = bc.bytesToUnsignedChar(bytesData[byteStart:byteStart+1])
    volumeDescriptorData = bytesData[byteStart:byteEnd]
    
    return(volumeDescriptorType, volumeDescriptorData, byteEnd)
    
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

    # Set up elemement object to store extracted properties
    properties = ET.Element("masterDirectoryBlock")
             
    addProperty(properties, "signature", bc.bytesToText(bytesData[0:2]))
    addProperty(properties, "blockSize", bc.bytesToUShortInt(bytesData[18:20]))
    addProperty(properties, "blockCount", bc.bytesToUInt(bytesData[20:24]))
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

    # Parse arguments
    args=parser.parse_args()

    return(args)

def processImage(image):

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
    

    # Initialise success flag
    success = True
   
    try:    
        # Get file size in bytes
        isoFileSize = os.path.getsize(image)

        # We'll only read first 30 sectors of image, which should be more than enough for
        # extracting PVD
        # TODO: is this enough for any possible hybrid FS?
        byteStart = 0  
        noBytes = min(30*2048,isoFileSize)
        isoBytes = readFileBytes(image, byteStart,noBytes)
        
        # Does image match byte signature for an ISO 9660 image?
        addProperty(tests, "containsISO9660Signature", signatureCheck(isoBytes))
        
        # Does image contain Apple Partition Map, HFS Header or Master Directory Block?
        containsApplePartitionMap = isoBytes[0:2] == b'\x45\x52' and isoBytes[512:514] == b'\x50\x4D'
        containsAppleHFSHeader = isoBytes[1024:1026] == b'\x4C\x4B'
        containsAppleMasterDirectoryBlock = isoBytes[1024:1026] in [b'\x42\x44',b'\xd2\xd7']        

        addProperty(tests, "containsApplePartitionMap", containsApplePartitionMap)
        addProperty(tests, "containsAppleHFSHeader", containsAppleHFSHeader)
        addProperty(tests, "containsAppleMasterDirectoryBlock", containsAppleMasterDirectoryBlock)
        
        if containsApplePartitionMap == True:
                   
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
            
            """
            # Get partition map data
            applePartitionMapData = isoBytes[512:1024]
            # Parse partition map
            applePartitionMapInfo = parseApplePartitionMap(applePartitionMapData)
            properties.append(applePartitionMapInfo)
            
            # TODO
            # Not entirely clear how references between multiple partition map entries works, offset to next PM seems to be
            #  offset_current_PM +  (partitionBlockStart * blockSize)
            
            # TEST
            applePartitionMapData = isoBytes[1024:1548]
            # Parse partition map
            applePartitionMapInfo = parseApplePartitionMap(applePartitionMapData)
            properties.append(applePartitionMapInfo)
            """
        if containsAppleHFSHeader == True:
            # Extract some info from HFS header
            pass
        
        if containsAppleMasterDirectoryBlock == True:
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
        noVolumeDescriptors = 0

        # Skip to byte 32768, which is where actual ISO 9660 fields start
        byteStart = 32768

        # Read through all 2048-byte volume descriptors, until Volume Descriptor Set Terminator is found
        # (or unexpected EOF, which will result in -9999 value for volumeDescriptorType)
        while volumeDescriptorType != 255 and volumeDescriptorType != -9999:
        
            volumeDescriptorType, volumeDescriptorData, byteEnd = getVolumeDescriptor(isoBytes, byteStart)
            noVolumeDescriptors += 1
            
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
                
        calculatedSizeExpected = False
        
        # Expected ISO size (bytes) can now be calculated from 3 different places: Zero Block, PVD and/or Master Directory Block

        # Intialise 3 estimates at 0
        sizeExpectedPVD = 0
        sizeExpectedZeroBlock = 0
        sizeExpectedMDB = 0

        if parsedPrimaryVolumeDescriptor == True:
            # Calculate from Primary Volume Descriptor
            sizeExpectedPVD = pvdInfo.find('volumeSpaceSize').text * pvdInfo.find('logicalBlockSize').text
            # NOTE: this might be off if logicalBlockSize != 2048 (since Sys area and Volume Descriptors
            # are ALWAYS multiples of 2048 bytes!). Also, even for non-hybrid FS actual size is sometimes slightly larger than expected size.
            # Not entirely sure why (padding bytes?)
                
        if containsApplePartitionMap == True and parsedAppleZeroBlock == True:   
            # Calculate from zero block in Apple partition 
            sizeExpectedZeroBlock = appleZeroBlockInfo.find('blockCount').text * appleZeroBlockInfo.find('blockSize').text

        if containsAppleMasterDirectoryBlock == True and parsedMasterDirectoryBlock == True:
            # Calculate from Apple Master Directory Block 
            sizeExpectedMDB = masterDirectoryBlockInfo.find('blockCount').text * masterDirectoryBlockInfo.find('blockSize').text

        # Assuming here that best estimate is largest out of the above values
        sizeExpected = max([sizeExpectedPVD, sizeExpectedZeroBlock, sizeExpectedMDB])

        # Size difference
        diffSize = isoFileSize - sizeExpected

        # Difference expressed as number of sectors
        #diffSectors = diffSize / 2048
        
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
        
    root = ET.Element("isolyzer")
      
    
    for image in ISOImages:
        result = processImage(image)
        root.append(result)
    
    # Write output
    makeHumanReadable(root)
    writeElement(root, out)
 
if __name__ == "__main__":
    main()

