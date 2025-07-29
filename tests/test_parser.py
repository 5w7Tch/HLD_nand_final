"""
Unit tests for the HDL parser module.
"""

import pytest
from hdl_parser.parser import HDLParser
from hdl_parser.models import ChipDefinition, ChipInstance, Connection


class TestHDLParser:
    """Test cases for HDLParser class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.parser = HDLParser()
    
    def test_parse_simple_chip(self):
        """Test parsing a simple chip with basic structure."""
        hdl_content = """
        CHIP TestChip {
            IN a, b;
            OUT out;
            
            PARTS:
            And(a=a, b=b, out=out);
        }
        """
        
        chip = self.parser.parse_hdl(hdl_content, "TestChip")
        
        assert chip.name == "TestChip"
        assert chip.inputs == ["a", "b"]
        assert chip.outputs == ["out"]
        assert len(chip.parts) == 1
        assert chip.parts[0].chip_type == "And"
    
    def test_parse_chip_with_internal_pins(self):
        """Test parsing a chip with internal connections."""
        hdl_content = """
        CHIP AndGate {
            IN a, b;
            OUT out;
            
            PARTS:
            Nand(a=a, b=b, out=nandOut);
            Not(in=nandOut, out=out);
        }
        """
        
        chip = self.parser.parse_hdl(hdl_content, "AndGate")
        
        assert chip.name == "AndGate"
        assert len(chip.parts) == 2
        assert "nandOut" in chip.internal_pins
    
    def test_parse_connections(self):
        """Test parsing pin connections."""
        hdl_content = """
        CHIP Test {
            IN x, y;
            OUT z;
            
            PARTS:
            And(a=x, b=y, out=z);
        }
        """
        
        chip = self.parser.parse_hdl(hdl_content, "Test")
        part = chip.parts[0]
        
        # Check connections
        connections = {(c.source, c.destination) for c in part.connections}
        assert ("x", "a") in connections
        assert ("y", "b") in connections
        assert ("z", "out") in connections
    
    def test_parse_comments(self):
        """Test that comments are properly removed."""
        hdl_content = """
        // This is a comment
        CHIP Test {
            IN a; // Input comment
            OUT out;
            /* Multi-line
               comment */
            PARTS:
            Not(in=a, out=out);
        }
        """
        
        chip = self.parser.parse_hdl(hdl_content, "Test")
        
        assert chip.name == "Test"
        assert chip.inputs == ["a"]
        assert chip.outputs == ["out"]
    
    def test_parse_empty_parts(self):
        """Test parsing chip with no parts (built-in)."""
        hdl_content = """
        CHIP Nand {
            IN a, b;
            OUT out;
            
            PARTS:
        }
        """
        
        chip = self.parser.parse_hdl(hdl_content, "Nand")
        
        assert chip.name == "Nand"
        assert len(chip.parts) == 0
    
    def test_builtin_chips_initialized(self):
        """Test that built-in chips are properly initialized."""
        assert "Nand" in self.parser.built_in_chips
        assert "Not" in self.parser.built_in_chips
        assert "And" in self.parser.built_in_chips
        assert "Or" in self.parser.built_in_chips
        
        # Check Nand structure
        nand = self.parser.built_in_chips["Nand"]
        assert nand.inputs == ["a", "b"]
        assert nand.outputs == ["out"]
    
    def test_parse_multiple_outputs(self):
        """Test parsing chip with multiple outputs."""
        hdl_content = """
        CHIP HalfAdder {
            IN a, b;
            OUT sum, carry;
            
            PARTS:
            Xor(a=a, b=b, out=sum);
            And(a=a, b=b, out=carry);
        }
        """
        
        chip = self.parser.parse_hdl(hdl_content, "HalfAdder")
        
        assert chip.outputs == ["sum", "carry"]
        assert len(chip.parts) == 2
    
    def test_cache_mechanism(self):
        """Test that parsed chips are cached."""
        hdl_content = """
        CHIP Test {
            IN a;
            OUT out;
            PARTS:
            Not(in=a, out=out);
        }
        """
        
        chip1 = self.parser.parse_hdl(hdl_content, "Test")
        assert "Test" in self.parser.chips_cache
        
        # Should return cached version
        chip2 = self.parser.chips_cache["Test"]
        assert chip1 is chip2
    
    def test_invalid_hdl_format(self):
        """Test error handling for invalid HDL format."""
        hdl_content = "This is not valid HDL"
        
        with pytest.raises(ValueError, match="Invalid HDL format"):
            self.parser.parse_hdl(hdl_content, "Test")
    
    def test_whitespace_handling(self):
        """Test that extra whitespace is handled correctly."""
        hdl_content = """
        CHIP   Test   {
            IN   a  ,  b  ;
            OUT   out  ;
            
            PARTS:
            And( a = a , b = b , out = out );
        }
        """
        
        chip = self.parser.parse_hdl(hdl_content, "Test")
        
        assert chip.inputs == ["a", "b"]
        assert chip.outputs == ["out"]
        assert len(chip.parts) == 1