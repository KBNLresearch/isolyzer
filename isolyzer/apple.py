#! /usr/bin/env python
# 
# Parser functions for Apple file systems

import xml.etree.ElementTree as ET
if __package__ is None:
    import byteconv as bc
    import shared as shared
else:
    # Use relative imports if run from package
    from . import byteconv as bc
    from . import shared as shared

def parseZeroBlock(bytesData):

    # Based on code at:
    # https://opensource.apple.com/source/IOStorageFamily/IOStorageFamily-116/IOApplePartitionScheme.h

    # Set up elemement object to store extracted properties
    properties = ET.Element("appleZeroBlock")
            
    shared.addProperty(properties, "signature", bc.bytesToText(bytesData[0:2]))
    shared.addProperty(properties, "blockSize", bc.bytesToUShortInt(bytesData[2:4]))
    shared.addProperty(properties, "blockCount", bc.bytesToUInt(bytesData[4:8]))
    shared.addProperty(properties, "deviceType", bc.bytesToUShortInt(bytesData[8:10]))
    shared.addProperty(properties, "deviceID", bc.bytesToUShortInt(bytesData[10:12]))
    shared.addProperty(properties, "driverData", bc.bytesToUInt(bytesData[12:16])) 
    shared.addProperty(properties, "driverDescriptorCount", bc.bytesToUShortInt(bytesData[80:82]))
    shared.addProperty(properties, "driverDescriptorBlockStart", bc.bytesToUInt(bytesData[82:86]))
    shared.addProperty(properties, "driverDescriptorBlockCount", bc.bytesToUShortInt(bytesData[86:88]))
    shared.addProperty(properties, "driverDescriptorSystemType", bc.bytesToUShortInt(bytesData[88:90]))
        
    return(properties)

def parsePartitionMap(bytesData):

    # Based on description at:
    # https://en.wikipedia.org/wiki/Apple_Partition_Map#Layout
    # and code at:
    # https://opensource.apple.com/source/IOStorageFamily/IOStorageFamily-116/IOApplePartitionScheme.h
    # Variable naming mostly follows Apple's code. 

    # Set up elemement object to store extracted properties
    properties = ET.Element("applePartitionMap")
             
    shared.addProperty(properties, "signature", bc.bytesToText(bytesData[0:2]))
    shared.addProperty(properties, "numberOfPartitionEntries", bc.bytesToUInt(bytesData[4:8]))
    shared.addProperty(properties, "partitionBlockStart", bc.bytesToUInt(bytesData[8:12]))
    shared.addProperty(properties, "partitionBlockCount", bc.bytesToUInt(bytesData[12:16]))
    shared.addProperty(properties, "partitionName", bc.bytesToText(bytesData[16:48]))
    shared.addProperty(properties, "partitionType", bc.bytesToText(bytesData[48:80]))
    shared.addProperty(properties, "partitionLogicalBlockStart", bc.bytesToUInt(bytesData[80:84]))
    shared.addProperty(properties, "partitionLogicalBlockCount", bc.bytesToUInt(bytesData[84:88]))
    shared.addProperty(properties, "partitionFlags", bc.bytesToUInt(bytesData[88:92]))
    shared.addProperty(properties, "bootCodeBlockStart", bc.bytesToUInt(bytesData[92:96]))
    shared.addProperty(properties, "bootCodeSizeInBytes", bc.bytesToUInt(bytesData[96:100]))
    shared.addProperty(properties, "bootCodeLoadAddress", bc.bytesToUInt(bytesData[100:104]))
    shared.addProperty(properties, "bootCodeJumpAddress", bc.bytesToUInt(bytesData[108:112]))
    shared.addProperty(properties, "bootCodeChecksum", bc.bytesToUInt(bytesData[116:120]))
    shared.addProperty(properties, "processorType", bc.bytesToText(bytesData[120:136]))
    return(properties)
    
def parseMasterDirectoryBlock(bytesData):
    # Based on description at:
    # https://developer.apple.com/legacy/library/documentation/mac/Files/Files-102.html
    # and https://github.com/libyal/libfshfs/blob/master/documentation/Hierarchical%20File%20System%20(HFS).asciidoc

    # Set up elemement object to store extracted properties
    properties = ET.Element("masterDirectoryBlock")
             
    shared.addProperty(properties, "signature", bc.bytesToText(bytesData[0:2]))
    shared.addProperty(properties, "blockSize", bc.bytesToUShortInt(bytesData[18:20]))
    shared.addProperty(properties, "blockCount", bc.bytesToUInt(bytesData[20:24]))
    shared.addProperty(properties, "volumeName", bc.bytesToText(bytesData[37:63]))
    return(properties)

def parseHFSPlusVolumeHeader(bytesData):

    # Based on https://opensource.apple.com/source/xnu/xnu-344/bsd/hfs/hfs_format.h
    
    # Set up elemement object to store extracted properties
    properties = ET.Element("hfsPlusVolumeheader")
             
    shared.addProperty(properties, "signature", bc.bytesToText(bytesData[0:2]))
    shared.addProperty(properties, "version", bc.bytesToUShortInt(bytesData[2:4]))
    shared.addProperty(properties, "blockSize", bc.bytesToUInt(bytesData[40:44]))
    shared.addProperty(properties, "blockCount", bc.bytesToUInt(bytesData[44:48]))
    
    return(properties)

