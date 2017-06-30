#!/bin/bash

# Create ISO images with different fs layouts
# Dependencies: mkisofs, mkudffs, mkfs.hfsplus 

# Installation directory
instDir="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
# Data directory
dataDir="$instDir"/dataTestfiles
# Output directory
outDir="$instDir"/testFiles

# ISO 9660 only
mkisofs -V "ISO 9660 only demo" -J -r -R -o $outDir/iso9660.iso $dataDir/

# Hybrid ISO 9660 / HFS
mkisofs -V "ISO 9660 / HFS Hybrid demo" -J -r -R -hfs -o $outDir/iso9660_hfs.iso $dataDir/

# Hybrid ISO 9660  with Apple extensions
# TODO: not clear how this works: no Apple blocks in first 32768 bytes, also image cannot be mounted
# as hfs or hfsplus under Linux!
# mkisofs -V "ISO 9660 + Apple extensions demo" -J -r -R -apple -o $outDir/iso9660_apple.iso $dataDir/

# UDF Bridge (ISO 9660 / UDF hybrid)
mkisofs -V "UDF Bridge demo" -J -r -R -UDF -o $outDir/iso9660_udf.iso $dataDir/

# UDF (empty fs)
rm $outDir/udf.iso
truncate -s 600K $outDir/udf.iso
mkudffs --media-type=dvd $outDir/udf.iso

# HFS (empty fs)
rm $outDir/hfs.iso
truncate -s 600K $outDir/hfs.iso
mkfs.hfsplus -h -b 2048 -v "HFS demo" $outDir/hfs.iso

# HFS Plus (empty fs)
rm $outDir/hfsplus.iso
truncate -s 600K $outDir/hfsplus.iso
mkfs.hfsplus -b 2048 -v "HFS Plus demo" $outDir/hfsplus.iso

# Truncated file
cp $outDir/iso9660.iso $outDir/iso9660_trunc.iso
truncate -s 49157 $outDir/iso9660_trunc.iso

# File truncated before PVD
cp $outDir/iso9660.iso $outDir/iso9660_nopvd.iso
truncate -s 32860 $outDir/iso9660_nopvd.iso

