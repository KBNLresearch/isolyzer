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
import argparse
import byteconv as bc
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

def signatureCheck(bytesData):
    # Check if file matches binary signature for ISO9660
    # (Check for occurrence at offsets 32769 and 34817; 
    # apparently 3rd ocurrece at offset 36865 is optional)

    print("Signature matches:")
    print("offset 32669: " + bytesData[32769:32774])
    print("offset 34817: " + bytesData[34817:34822])
    print("offset 36865: " + bytesData[36865:36870])
    
    if bytesData[32769:32774] == b'CD001'\
        and bytesData[34817:34822] == b'CD001':
        iso9660Match = True
    else:
        iso9660Match = False
    
    return(iso9660Match)
    
def getVolumeDescriptor(bytesData, byteStart):

    # Read one 2048-byte volume descriptor and return its descriptor
    # code and contents
    byteEnd = byteStart + 2048
    volumeDescriptorType = bc.bytesToUnsignedChar(bytesData[byteStart:byteStart+1])
    volumeDescriptorData = bytesData[byteStart:byteEnd]
    
    return(volumeDescriptorType, volumeDescriptorData, byteEnd)
    
def parsePrimaryVolumeDescriptor(bytesData):
   
    # Dictionary to store interesting (size-related) fields from the PVD
    pvdFields = {}
    pvdFields["identifier"] = bc.bytesToText(bytesData[1:6])
    
    # Note: fields below are stored as both little-endian and big-endian; only
    # big-endian values read here!
    
    # Number of Logical Blocks in which the volume is recorded
    pvdFields["volumeSpaceSize"] = bc.bytesToUInt(bytesData[84:88])
    
    # The size of the set in this logical volume (number of disks)
    pvdFields["volumeSetSize"] = bc.bytesToUShortInt(bytesData[122:124])
    
    # The number of this disk in the Volume Set
    pvdFields["volumeSequenceNumber"] = bc.bytesToUShortInt(bytesData[126:128])

    # The size in bytes of a logical block
    pvdFields["logicalBlockSize"] = bc.bytesToUShortInt(bytesData[130:132])

    # The size in bytes of the path table
    pvdFields["pathTableSize"] = bc.bytesToUInt(bytesData[136:140])

	# Location of Type-L Path Table (note this is stored as little-endian only, hence
	# byte swap!)
    pvdFields["typeLPathTableLocation"] = bc.swap32(bc.bytesToUInt(bytesData[140:144]))

    # Location of Optional Type-L Path Table
    pvdFields["optionalTypeLPathTableLocation"] = bc.swap32(bc.bytesToUInt(bytesData[144:148]))

    # Location of Type-M Path Table
    pvdFields["typeMPathTableLocation"] = bc.bytesToUInt(bytesData[148:152])

    # Location of Optional Type-M Path Table
    pvdFields["optionalTypeMPathTableLocation"] = bc.bytesToUInt(bytesData[152:156])
    
    # print(pvdFields)
    
    return(pvdFields)
    
def parseCommandLine():
    # Add arguments
    parser.add_argument('ISOImage', 
        action = "store", 
        type = str, 
        help = "input ISO image")
    parser.add_argument('--version', '-v',
        action = 'version', 
        version = __version__)

    # Parse arguments
    args=parser.parse_args()

    return(args)

def main():
    # Get input from command line
    args = parseCommandLine()
     
    # Input
    ISOImage = args.ISOImage
    
    # Does input image exist?
    checkFileExists(ISOImage)
    
    # Get file size in bytes
    isoFileSize = os.path.getsize(ISOImage)

    # We'll only read first 30 sectors of image, which should be more than enough for
    # extracting PVM
    byteStart = 0  
    noBytes = min(30*2048,isoFileSize)
    
    # File contents to bytes object (NOTE: this could cause all sorts of problems with very 
    # large ISOs, so change to part of file later)
    isoBytes = readFileBytes(ISOImage, byteStart,noBytes)
    
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
            
            # Get info from Primary Volume Descriptor (as a dictionary)
            pvdInfo = parsePrimaryVolumeDescriptor(volumeDescriptorData)
        
        byteStart = byteEnd
       
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
if __name__ == "__main__":
    main()

