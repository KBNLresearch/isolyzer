#! /usr/bin/env python
"""Parser functions for High Sierra file systems"""

import xml.etree.ElementTree as ET
from . import byteconv as bc
from . import shared as shared


def decDateTimeToDate(datetime):
    """Convert 17 bit dec-datetime field to formatted  date-time string"""
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
        dateTimeString = ""
    return dateTimeString


def getVolumeDescriptor(bytesData, byteStart):

    """Read one 2048-byte HSF volume descriptor and return its descriptor
    code and contents
    """
    byteEnd = byteStart + 2048
    volumeDescriptorType = bc.bytesToUnsignedChar(bytesData[byteStart+8:byteStart+9])
    volumeDescriptorData = bytesData[byteStart:byteEnd]

    return(volumeDescriptorType, volumeDescriptorData, byteEnd)


def parseSFSVolumeDescriptor(bytesData):

    """Parse Standard File Structure Volume Descriptor
    and return extracted properties. Based on section
    11.4 in:
    https://www.os2museum.com/files/docs/cdrom/CDROM_Working_Paper-1986.pdf

    For fields that are stored as both little-endian and big-endian, only
    big-endian values are read here!
    """

    # Set up elemement object to store extracted properties
    properties = ET.Element("standardFileStructureVolumeDescriptor")

    shared.addProperty(properties, "volumeDescriptorLBN",
                       bc.bytesToUInt(bytesData[4:8]))
    shared.addProperty(properties, "volumeDescriptorType",
                       bc.bytesToUnsignedChar(bytesData[8:9]))
    shared.addProperty(properties, "volumeStructureStandardIdentifier",
                       bc.bytesToText(bytesData[9:14]))
    shared.addProperty(properties, "volumeStructureStandardVersion",
                       bc.bytesToUnsignedChar(bytesData[14:15]))
    shared.addProperty(properties, "systemIdentifier",
                       bc.bytesToText(bytesData[16:48]))
    shared.addProperty(properties, "volumeIdentifier",
                       bc.bytesToText(bytesData[48:80]))
    shared.addProperty(properties, "volumeSpaceSize",
                       bc.bytesToUInt(bytesData[92:96]))
    shared.addProperty(properties, "volumeSetSize",
                       bc.bytesToUShortInt(bytesData[130:132]))
    shared.addProperty(properties, "volumeSetSequenceNumber",
                       bc.bytesToUShortInt(bytesData[134:136]))
    shared.addProperty(properties, "logicalBlockSize",
                       bc.bytesToUShortInt(bytesData[138:140]))
    shared.addProperty(properties, "pathTableSize",
                       bc.bytesToUInt(bytesData[144:148]))

    # Following fields are stored as little-endian only, hence
    # byte swap
    shared.addProperty(properties, "firstMandatoryPathTableLocation",
                       bc.swap32(bc.bytesToUInt(bytesData[148:152])))
    shared.addProperty(properties, "optionalPathTableLocation",
                       bc.swap32(bc.bytesToUInt(bytesData[152:156])))
    shared.addProperty(properties, "optionalPathTableLocation",
                       bc.swap32(bc.bytesToUInt(bytesData[156:160])))
    shared.addProperty(properties, "optionalPathTableLocation",
                       bc.swap32(bc.bytesToUInt(bytesData[160:164])))
    shared.addProperty(properties, "secondMandatoryPathTableLocation",
                       bc.swap32(bc.bytesToUInt(bytesData[164:168])))
    shared.addProperty(properties, "optionalPathTableLocation",
                       bc.swap32(bc.bytesToUInt(bytesData[168:172])))
    shared.addProperty(properties, "optionalPathTableLocation",
                       bc.swap32(bc.bytesToUInt(bytesData[172:176])))
    shared.addProperty(properties, "optionalPathTableLocation",
                       bc.swap32(bc.bytesToUInt(bytesData[176:180])))

    # Following fields are all text strings
    shared.addProperty(properties, "volumeSetIdentifier",
                       bc.bytesToText(bytesData[214:342]))
    shared.addProperty(properties, "publisherIdentifier",
                       bc.bytesToText(bytesData[342:470]))
    shared.addProperty(properties, "dataPreparerIdentifier",
                       bc.bytesToText(bytesData[470:598]))
    shared.addProperty(properties, "applicationIdentifier",
                       bc.bytesToText(bytesData[598:726]))
    shared.addProperty(properties, "copyrightFileIdentifier",
                       bc.bytesToText(bytesData[726:758]))
    shared.addProperty(properties, "abstractFileIdentifier",
                       bc.bytesToText(bytesData[758:790]))

    # Following fields are all date-time values
    shared.addProperty(properties, "volumeCreationDateAndTime",
                       decDateTimeToDate(bytesData[790:806]))
    shared.addProperty(properties, "volumeModificationDateAndTime",
                       decDateTimeToDate(bytesData[806:822]))
    shared.addProperty(properties, "volumeExpirationDateAndTime",
                       decDateTimeToDate(bytesData[822:838]))
    shared.addProperty(properties, "volumeEffectiveDateAndTime",
                       decDateTimeToDate(bytesData[838:854]))

    shared.addProperty(properties, "fileStructureStandardVersion",
                       bc.bytesToUnsignedChar(bytesData[854:855]))

    return properties
