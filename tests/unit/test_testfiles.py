#! /usr/bin/env python3
# pylint: disable=missing-docstring
"""
Tests on isolyzer test files.
"""

import os
import glob
import pytest
from lxml import etree

from isolyzer.isolyzer import processImage

sizeDifferenceSectors = {
"hfs.iso":2.0,
"hfsplus.iso":0.0,
"is9660_udf_imgburn.iso":9.0,
"iso9660_apple.iso":0.0,
"iso9660_hfs.iso":0.0,
"iso9660_hfs_part.iso":0.0,
"iso9660_hfs_part_wrongblksize.iso":-1173.0,
"iso9660.iso":0.0,
"iso9660_nopvd.iso":16.044921875,
"iso9660_roxioecc.iso":265.0,
"iso9660_trunc.iso":-191.99755859375,
"iso9660_udf_hfs.iso":0.0,
"iso9660_udf.iso":0.0,
"multisession.iso":-21915.0,
"udf.iso":48.0
}

fileSystems = {
"hfs.iso":["HFS"],
"hfsplus.iso":["HFS+"],
"is9660_udf_imgburn.iso":["ISO 9660","UDF"],
"iso9660_apple.iso":["ISO 9660"],
"iso9660_hfs.iso":["ISO 9660","HFS"],
"iso9660_hfs_part.iso":["ISO 9660","HFS"],
"iso9660_hfs_part_wrongblksize.iso":["ISO 9660","HFS"],
"iso9660.iso":["ISO 9660"],
"iso9660_nopvd.iso":[],
"iso9660_roxioecc.iso":["ISO 9660"],
"iso9660_trunc.iso":["ISO 9660"],
"iso9660_udf_hfs.iso":["ISO 9660","HFS","UDF"],
"iso9660_udf.iso":["ISO 9660","UDF"],
"multisession.iso":["ISO 9660"],
"udf.iso":["UDF"]
}

# Directory that contains this script
SCRIPT_DIR = os.path.dirname(os.path.realpath(__file__))

# Root dir of isolyzer repo
ISOLYZER_DIR = os.path.split(os.path.split(SCRIPT_DIR)[0])[0]

# Directory with test files
testFilesDir = os.path.join(ISOLYZER_DIR, "testFiles")

# All files in test files dir, excluding .md file
testFiles = glob.glob(os.path.join(testFilesDir, '*.iso'))

def test_groundtruth_complete():
    """
    Test if all files in sizeDifferenceSectors
    dictionary really exist
    """
    for key in sizeDifferenceSectors:
        thisFile = os.path.join(testFilesDir, key)
        assert os.path.isfile(thisFile)

@pytest.mark.parametrize('input', testFiles)

def test_status(input):
    """
    Tests for any internal errors based on statusInfo value
    """
    outIsolyzer = processImage(input, 0)
    assert outIsolyzer.findtext('./statusInfo/success') == "True"

@pytest.mark.parametrize('input', testFiles)

def test_sizeDifference(input):
    """
    Tests size difference against known values
    Note: not using findtext here, because that will fail on
    zero values: https://github.com/python/cpython/issues/91447
    """
    fName = os.path.basename(input)
    outIsolyzer = processImage(input, 0)
    if fName in sizeDifferenceSectors.keys():
        sizeDif = sizeDifferenceSectors[fName]
        elt = outIsolyzer.find('./tests/sizeDifferenceSectors')
        assert elt.text == pytest.approx(sizeDif)
