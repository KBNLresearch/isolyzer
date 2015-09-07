# verifyISOSize

## About
*verifyISOSize* verifies if the file size of a CD / DVD ISO 9660 image is consistent with the information in its [Primary Volume Descriptor](http://wiki.osdev.org/ISO_9660#The_Primary_Volume_Descriptor). This can be useful for detecting incomplete (e.g. truncated) ISO images. What the tool does is this:

1. Locate the image's Primary Volume Descriptor (PVD).
2. From the PVD, read the Volume Space Size (number of sectors/blocks) and Logical Block Size (number of bytes for each block) fields.
3. Calculate expected file size as ( Volume Space Size x Logical Block Size ).
4. Compare this against the actual size of the image files.

In practice the following 3 situations can occur:

1. Actual size equals expected size - perfect!
2. Actual size smaller than expected size: in this case the image is damaged or otherwise incomplete.
3. Actual size larger than expected size: this seems to be the case for many ISO images. Not really sure about the exact cause, but this does not typically indicate a damaged image (I suppose lots of images just don't fully conform to ISO 9660?).

I wrote this tool after encountering [incomplete ISO images after running ddrescue](http://qanda.digipres.org/1076/incomplete-image-after-imaging-rom-prevent-and-detect-this) (most likely caused by some hardware issue), and subsequently discovering that [isovfy](http://manpages.ubuntu.com/manpages/hardy/man1/devdump.1.html) doesn't detect this at all (tried with version 1.1.11 on Linux Mint 17.1).

## Limitations
Currently the check *only* works for CDs or DVDs with [ISO9660](http://wiki.osdev.org/ISO_9660) or [Joliet](https://en.wikipedia.org/wiki/Joliet_%28file_system%29) file systems. The [Universal Disk Format (UDF)](https://en.wikipedia.org/wiki/Universal_Disk_Format) file system is not (yet) supported. 

Finally a correct file *size* alone does not guarantee the integrity of the image (for this there's not getting around running a checksum on both the image and the physical source medium). 

## Command line use

### Usage

    verifyISOSize.py [-h] [--version] ISOImage
    
### Positional arguments

`ISOImage` : input ISO image

### Optional arguments

`-h, --help` : show this help message and exit;

`-v, --version` : show program's version number and exit;

## Examples

(All files available in *testFiles* folder of this repo.) 

### Example 1: ISO image has expected size 

    verifyISOSize.py minimal.iso
    
Output:

    -----------------------
       Results
    -----------------------
    ISO image has expected size
    Volume space size: 175 blocks
    Logical block size: 2048 bytes
    Expected file size: 358400 bytes
    Actual file size: 358400 bytes
    Difference (expected - actual): 0 bytes / 0 sectors

### Example 2: ISO image smaller than expected size

    verifyISOSize.py minimal_trunc.iso

Output:

    -----------------------
       Results
    -----------------------
    ISO image smaller than expected size (we're in trouble now!)
    Volume space size: 175 blocks
    Logical block size: 2048 bytes
    Expected file size: 358400 bytes
    Actual file size: 91582 bytes
    Difference (expected - actual): 266818 bytes / 130 sectors

### Example 3: ISO truncated before Primary Volume Descriptor

    verifyISOSize.py minimal_trunc_nopvd.iso
    
Output:

    -----------------------
       Results
    -----------------------
    ISO image smaller than expected size (we're in trouble now!)
    Volume space size: -9999 blocks
    Logical block size: -9999 bytes
    Expected file size: 99980001 bytes
    Actual file size: 32840 bytes
    Difference (expected - actual): 99947161 bytes / 48802 sectors

(Note bogus values of -9999, which occur because no meaningful data can be extracted from the PVD).


