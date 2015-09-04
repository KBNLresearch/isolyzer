#! /usr/bin/env python
# 
# Verify if size of CD-ROM ISO image matches information in
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
    description="Verify file size of ISO 9660")

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
    
def readFileBytes(file):
    # Read file, return contents as a byte object

    # Open file
    f = open(file,"rb")

    # Put contents of file into a byte object.
    fileData=f.read()
    f.close()

    return(fileData)

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
    
    print(pvdFields)
    
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
    
    # File contents to bytes object (NOTE: this could cause all sorts of problems with very 
    # large ISOs, so change to part of file later)
    isoBytes = readFileBytes(ISOImage)
    
    # Skip bytes 0 - 32767 (system area, usually empty)
    byteStart = 32768
    
    # This is a dummy value
    volumeDescriptorType = -1
    
    # Count volume descriptors
    noVolumeDescriptors = 0
   
    # Read through all 2048-byte volume descriptors, until Volume Descriptor Set Terminator is found
    while volumeDescriptorType != 255:
    
        volumeDescriptorType, volumeDescriptorData, byteEnd = getVolumeDescriptor(isoBytes, byteStart)
        noVolumeDescriptors += 1
        
        if volumeDescriptorType == 1:
            
            # Get info from Primary Volume Descriptor (as a dictionary)
            pvdInfo = parsePrimaryVolumeDescriptor(volumeDescriptorData)
        
        byteStart = byteEnd
    
    print(noVolumeDescriptors)
    
    # Expected ISO size in bytes
    sizeExpected = 32768 + (noVolumeDescriptors*2048) +  pvdInfo["pathTableSize"] + \
        (pvdInfo["volumeSpaceSize"]*pvdInfo["logicalBlockSize"])

    # Difference
    diffSize = sizeExpected - isoFileSize

    # Difference expressed asnumber of sectors
    diffSectors = diffSize / 2048
    
    print("Actual ISO file size: " + str(isoFileSize))
    print("Expected file size: " + str(sizeExpected))
    print("Difference (bytes): " + str(diffSize))
    print("Difference (sectors): " + str(diffSectors))

if __name__ == "__main__":
    main()

