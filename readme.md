# verifyISOSize

## About
*verifyISOSize* verifies if the file size of a CD-ROM ISO 9660 image is consistent with the information in its Volume Descriptors. This can be useful for detecting incomplete (e.g. truncated) ISO images. 

Unfinished work in progress! UDF file systems not (yet) supported.

## Structure of ISO 9660 image

From what I understand (based on <http://wiki.osdev.org/ISO_9660>): 

    ++++++++++++++++++++++++++++++++++++++
    + System area (32768 bytes)          +
    ++++++++++++++++++++++++++++++++++++++
    + First Volume Descriptor            +
    ++++++++++++++++++++++++++++++++++++++
    +   {........}                       +
    ++++++++++++++++++++++++++++++++++++++
    + Volume Descriptor Set Terminator   +
    ++++++++++++++++++++++++++++++++++++++
    +  Type-L Path Table                 +
    ++++++++++++++++++++++++++++++++++++++
    +  {Optional Type-L Path Table}      +
    ++++++++++++++++++++++++++++++++++++++
    +  Type-M Path Table                 +
    ++++++++++++++++++++++++++++++++++++++
    +  {Optional Type-M Path Table}      +
    ++++++++++++++++++++++++++++++++++++++
    +  Actual data?                      +
    ++++++++++++++++++++++++++++++++++++++

Note that:

* Volume descriptors are 2048 bytes each
* Path tables are size *logicalBlockSize* each (typically 2048 bytes, but other values are possible!) 
* Value of *pathTableSize* is number of bytes occupied by actual data (excluding padding bytes)
* Actual data arranged in blocks of size *logicalBlockSize*
