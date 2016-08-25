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
import codecs
import argparse
import xml.etree.ElementTree as ET
import byteconv as bc
from xml.dom import minidom
scriptPath, scriptName = os.path.split(sys.argv[0])

__version__= "0.1.0"

# Create parser
parser = argparse.ArgumentParser(
    description="Verify file size of ISO 9660 image (no support for UDF file systems yet!)")

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

    # Steps to get rid of xml declaration:
    # String to list
    xmlAsList = xmlPretty.split("\n")
    # Remove first item (xml declaration)
    del xmlAsList[0]
    # Convert back to string
    xmlOut = "\n".join(xmlAsList)

    # Write output
    codec.write(xmlOut)

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
    
    
    properties = ET.Element("properties")
    
    # Print image name to screen
    print("-----------------------")
    print("Filename: " + image)
    print("-----------------------")
    # Get file size in bytes
    isoFileSize = os.path.getsize(image)

    # We'll only read first 30 sectors of image, which should be more than enough for
    # extracting PVM
    byteStart = 0  
    noBytes = min(30*2048,isoFileSize)
    
    # File contents to bytes object (NOTE: this could cause all sorts of problems with very 
    # large ISOs, so change to part of file later)
    isoBytes = readFileBytes(image, byteStart,noBytes)
    
    # Skip bytes 0 - 32767 (system area, usually empty)
    byteStart = 32768

    # Is this really an ISO 9660 image? (Skip)
    isIso9660 = signatureCheck(isoBytes)
    
    # This is a dummy value
    volumeDescriptorType = -1
    
    # Count volume descriptors
    noVolumeDescriptors = 0

    # Read through all 2048-byte volume descriptors, until Volume Descriptor Set Terminator is found
    # (or unexpected EOF, which will result in -9999 value for volumeDescriptorType)
    while volumeDescriptorType != 255 and volumeDescriptorType != -9999:
    
        volumeDescriptorType, volumeDescriptorData, byteEnd = getVolumeDescriptor(isoBytes, byteStart)
        noVolumeDescriptors += 1
        
        if volumeDescriptorType == 1:
            
            # Get info from Primary Volume Descriptor (as element object)
            pvdInfo = parsePrimaryVolumeDescriptor(volumeDescriptorData)
            properties.append(pvdInfo)
        
        byteStart = byteEnd
    
    
    """   
    # Expected ISO size in bytes
    sizeExpected = (pvdInfo["volumeSpaceSize"]*pvdInfo["logicalBlockSize"])

            
    # NOTE: might be off if logicalBlockSize != 2048 (since Sys area and Volume Descriptors
    # are ALWAYS multiples of 2048 bytes!)

    # Difference
    diffSize = sizeExpected - isoFileSize

    # Difference expressed asnumber of sectors
    diffSectors = diffSize / 2048
    
    if diffSectors == 0:
        result = "ISO image has expected size"
    elif diffSectors < 0:
        result = "ISO image larger than expected size (probably OK)"
    else:
        result = "ISO image smaller than expected size (we're in trouble now!)"

    print("-----------------------\n   Results\n-----------------------")
    print(result)
    print ("Volume space size: " + str(pvdInfo["volumeSpaceSize"]) + " blocks")
    print ("Logical block size: " + str(pvdInfo["logicalBlockSize"]) + " bytes")
    print("Expected file size: " + str(sizeExpected) + " bytes")
    print("Actual file size: " + str(isoFileSize) + " bytes")
    print("Difference (expected - actual): " + str(diffSize) + " bytes / " + str(diffSectors) + " sectors")
    if isIso9660 == False:
        print("WARNING: signature check failed!")
    print("\n")
    """
   
    makeHumanReadable(properties)
    
    writeElement(properties, out)
    
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
    
    print(ISOImages)
    
    for image in ISOImages:
        processImage(image)
       
 
if __name__ == "__main__":
    main()

