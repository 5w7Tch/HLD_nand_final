"""
HDL Parser and Chip Testing Framework

A tool for parsing Hardware Description Language (HDL) files and testing
chip implementations against test vectors.
"""

__version__ = "1.0.0"
__author__ = "HDL Parser Team"

from .models import ChipDefinition, ChipInstance, Connection
from .parser import HDLParser
from .simulator import ChipSimulator
from .test_runner import TestRunner

__all__ = [
    "ChipDefinition",
    "ChipInstance", 
    "Connection",
    "HDLParser",
    "ChipSimulator",
    "TestRunner",
]