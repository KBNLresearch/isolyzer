#! /usr/bin/env python
# 
# Parser functions for UDF file systems


import xml.etree.ElementTree as ET

if __package__ is "isolyzer":
    # Use relative imports if run from package
    from . import byteconv as bc
    from . import shared as shared
else:
    import byteconv as bc
    import shared as shared

def getExtendedVolumeDescriptor(bytesData, byteStart):

    # Read one 2048-byte extended (UDF only) volume descriptor and return its descriptor
    # code and contents
    byteEnd = byteStart + 2048
    volumeDescriptorIdentifier = bc.bytesToText(bytesData[byteStart+1:byteStart+6])
    volumeDescriptorData = bytesData[byteStart:byteEnd]
    
    return(volumeDescriptorIdentifier, volumeDescriptorData, byteEnd)

def getVolumeDescriptor(bytesData, byteStart):
    byteEnd = byteStart + 2048
    volumeDescriptorData = bytesData[byteStart:byteEnd]
    
    # Descriptor tag
    descriptorTag  = volumeDescriptorData[0:16]
    tagIdentifier = bc.bytesToUShortIntL(descriptorTag[0:2]) 
    descriptorVersion = bc.bytesToUShortIntL(descriptorTag[2:4])
       
    return(tagIdentifier, volumeDescriptorData, byteEnd)

def parseLogicalVolumeDescriptor(bytesData):

    # Set up elemement object to store extracted properties
    properties = ET.Element("logicalVolumeDescriptor")
    shared.addProperty(properties, "tagIdentifier", bc.bytesToUShortIntL(bytesData[0:2]))
    shared.addProperty(properties, "descriptorVersion", bc.bytesToUShortIntL(bytesData[2:4]))
    shared.addProperty(properties, "tagSerialNumber", bc.bytesToUShortIntL(bytesData[6:8]))
    shared.addProperty(properties, "volumeSequenceNumber", bc.bytesToUIntL(bytesData[16:20]))
    # TODO: really don't know how to interpret descriptorCharacterSet, report as
    # binhex for now
    # shared.addProperty(properties, "descriptorCharacterSet", bc.bytesToHex(bytesData[64:84]))
    # TODO: is bytesToText encoding-safe here? Don't really understand this OSTA compressed
    # Unicode at all!
    # shared.addProperty(properties, "compressionID", bc.bytesToUnsignedCharL(bytesData[84:85]))
    # Below line works for UTF-8
    shared.addProperty(properties, "logicalVolumeIdentifier", bc.bytesToText(bytesData[85:212]))
    shared.addProperty(properties, "logicalBlockSize", bc.bytesToUIntL(bytesData[212:216]))
    shared.addProperty(properties, "domainIdentifier", bc.bytesToText(bytesData[216:248]))
    shared.addProperty(properties, "mapTableLength", bc.bytesToUIntL(bytesData[264:268]))
    shared.addProperty(properties, "numberOfPartitionMaps", bc.bytesToUIntL(bytesData[268:272]))
    shared.addProperty(properties, "implementationIdentifier", bc.bytesToText(bytesData[272:304]))
    shared.addProperty(properties, "integritySequenceExtentLength", bc.bytesToUIntL(bytesData[432:436]))
    shared.addProperty(properties, "integritySequenceExtentLocation", bc.bytesToUIntL(bytesData[436:440]))
    return(properties)
    
def parseLogicalVolumeIntegrityDescriptor(bytesData):

    # Note: parser based on ECMA TR/71 DVD Read-Only Disk - File System Specifications 
    # Link: https://www.ecma-international.org/publications/techreports/E-TR-071.htm
    #
    # This puts constraint that *freeSpaceTable* and *sizeTable* describe one partition only!
    # Not 100% sure this applies to *all* DVDs (since TR/71 only defines UDF Bridge format!) 
    # If not, make these fields repeatable, iterating over *numberOfPartitions*!

    # Set up elemement object to store extracted properties
    properties = ET.Element("logicalVolumeIntegrityDescriptor")
    shared.addProperty(properties, "tagIdentifier", bc.bytesToUShortIntL(bytesData[0:2]))
    shared.addProperty(properties, "descriptorVersion", bc.bytesToUShortIntL(bytesData[2:4]))
    shared.addProperty(properties, "tagSerialNumber", bc.bytesToUShortIntL(bytesData[6:8]))
    
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
    shared.addProperty(properties, "timeStamp", dateTimeString)
    
    shared.addProperty(properties, "integrityType", bc.bytesToUIntL(bytesData[28:32]))
    shared.addProperty(properties, "numberOfPartitions", bc.bytesToUIntL(bytesData[72:76]))
    shared.addProperty(properties, "lengthOfImplementationUse", bc.bytesToUIntL(bytesData[76:80]))
    shared.addProperty(properties, "freeSpaceTable", bc.bytesToUIntL(bytesData[80:84]))
    shared.addProperty(properties, "sizeTable", bc.bytesToUIntL(bytesData[84:88]))
    
    return(properties)
    
def parsePartitionDescriptor(bytesData):

    # Set up elemement object to store extracted properties
    properties = ET.Element("partitionDescriptor")
    shared.addProperty(properties, "tagIdentifier", bc.bytesToUShortIntL(bytesData[0:2]))
    shared.addProperty(properties, "descriptorVersion", bc.bytesToUShortIntL(bytesData[2:4]))
    shared.addProperty(properties, "tagSerialNumber", bc.bytesToUShortIntL(bytesData[6:8]))
      
    shared.addProperty(properties, "volumeDescriptorSequenceNumber", bc.bytesToUIntL(bytesData[16:20]))
    shared.addProperty(properties, "partitionNumber", bc.bytesToUShortIntL(bytesData[22:24]))
    shared.addProperty(properties, "accessType", bc.bytesToUIntL(bytesData[184:188]))
    shared.addProperty(properties, "partitionStartingLocation", bc.bytesToUIntL(bytesData[188:192]))
    shared.addProperty(properties, "partitionLength", bc.bytesToUIntL(bytesData[192:196]))

    return(properties)

