# pylint: disable=missing-docstring
import sys
import pytest

from isolyzer.isolyzer import __version__

def test_version():
    assert __version__
