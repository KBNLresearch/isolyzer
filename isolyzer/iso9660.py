#! /usr/bin/env python
# 
# Parser functions for ISO 9660 file systems


import xml.etree.ElementTree as ET

if __package__ is "isolyzer":
    # Use relative imports if run from package
    from . import byteconv as bc
    from . import shared as shared
else:
    import byteconv as bc
    import shared as shared

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

    # Read one 2048-byte ISO volume descriptor and return its descriptor
    # code and contents
    byteEnd = byteStart + 2048
    volumeDescriptorType = bc.bytesToUnsignedChar(bytesData[byteStart:byteStart+1])
    volumeDescriptorData = bytesData[byteStart:byteEnd]
    
    return(volumeDescriptorType, volumeDescriptorData, byteEnd)
    
def parsePrimaryVolumeDescriptor(bytesData):

    # Set up elemement object to store extracted properties
    properties = ET.Element("primaryVolumeDescriptor")
           
    shared.addProperty(properties, "typeCode", bc.bytesToUnsignedChar(bytesData[0:1]))
    shared.addProperty(properties, "standardIdentifier", bc.bytesToText(bytesData[1:6]))
    shared.addProperty(properties, "version", bc.bytesToUnsignedChar(bytesData[6:7]))
    shared.addProperty(properties, "systemIdentifier", bc.bytesToText(bytesData[8:40]))
    shared.addProperty(properties, "volumeIdentifier", bc.bytesToText(bytesData[40:72]))

    # Fields below are stored as both little-endian and big-endian; only
    # big-endian values read here!
    
    # Number of Logical Blocks in which the volume is recorded
    shared.addProperty(properties, "volumeSpaceSize", bc.bytesToUInt(bytesData[84:88]))
    # The size of the set in this logical volume (number of disks)
    shared.addProperty(properties, "volumeSetSize", bc.bytesToUShortInt(bytesData[122:124]))
    # The number of this disk in the Volume Set
    shared.addProperty(properties, "volumeSequenceNumber", bc.bytesToUShortInt(bytesData[126:128]))
    # The size in bytes of a logical block
    shared.addProperty(properties, "logicalBlockSize", bc.bytesToUShortInt(bytesData[130:132]))
    # The size in bytes of the path table
    shared.addProperty(properties, "pathTableSize", bc.bytesToUInt(bytesData[136:140]))
	# Location of Type-L Path Table (note this is stored as little-endian only, hence
	# byte swap!)
    shared.addProperty(properties, "typeLPathTableLocation", bc.swap32(bc.bytesToUInt(bytesData[140:144])))
    # Location of Optional Type-L Path Table
    shared.addProperty(properties, "optionalTypeLPathTableLocation", bc.swap32(bc.bytesToUInt(bytesData[144:148])))
    # Location of Type-M Path Table
    shared.addProperty(properties, "typeMPathTableLocation", bc.bytesToUInt(bytesData[148:152]))
    # Location of Optional Type-M Path Table
    shared.addProperty(properties, "optionalTypeMPathTableLocation", bc.bytesToUInt(bytesData[152:156]))

    # Following fields are all text strings
    shared.addProperty(properties, "volumeSetIdentifier", bc.bytesToText(bytesData[190:318]))
    shared.addProperty(properties, "publisherIdentifier", bc.bytesToText(bytesData[318:446]))
    shared.addProperty(properties, "dataPreparerIdentifier", bc.bytesToText(bytesData[446:574]))
    shared.addProperty(properties, "applicationIdentifier", bc.bytesToText(bytesData[574:702]))
    shared.addProperty(properties, "copyrightFileIdentifier", bc.bytesToText(bytesData[702:740]))
    shared.addProperty(properties, "abstractFileIdentifier", bc.bytesToText(bytesData[740:776]))
    shared.addProperty(properties, "bibliographicFileIdentifier", bc.bytesToText(bytesData[776:813]))
    
    # Following fields are all date-time values    
    shared.addProperty(properties, "volumeCreationDateAndTime", decDateTimeToDate(bytesData[813:830]))
    shared.addProperty(properties, "volumeModificationDateAndTime", decDateTimeToDate(bytesData[830:847]))
    shared.addProperty(properties, "volumeExpirationDateAndTime", decDateTimeToDate(bytesData[847:864]))
    shared.addProperty(properties, "volumeEffectiveDateAndTime", decDateTimeToDate(bytesData[864:881]))
    
    shared.addProperty(properties, "fileStructureVersion", bc.bytesToUnsignedChar(bytesData[881:882]))
    
    return(properties)

