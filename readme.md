# verifyISOSize

## About
*verifyISOSize* verifies if the file size of a CD-ROM ISO 9660 image is consistent with the information in its Volume Descriptors. This can be useful for detecting incomplete (e.g. truncated) ISO images. 


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


