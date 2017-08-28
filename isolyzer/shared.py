#! /usr/bin/env python
"""Shared functions"""

import xml.etree.ElementTree as ET


def addProperty(element, tag, text):
    """Append childnode with text"""

    el = ET.SubElement(element, tag)
    el.text = text
