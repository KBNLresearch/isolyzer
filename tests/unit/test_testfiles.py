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

# Directory that contains this script
SCRIPT_DIR = os.path.dirname(os.path.realpath(__file__))

# Root dir of isolyzer repo
ISOLYZER_DIR = os.path.split(os.path.split(SCRIPT_DIR)[0])[0]

# Directory with test files
testFilesDir = os.path.join(ISOLYZER_DIR, "testFiles")

# All files in test files dir, excluding .md file
testFiles = glob.glob(os.path.join(testFilesDir, '*.iso'))

@pytest.mark.parametrize('input', testFiles)

def test_status(input):
    """
    Tests for any internal errors based on statusInfo value
    """
    outIsolyzer = processImage(input, 0)
    assert outIsolyzer.findtext('./statusInfo/success') == "True"
