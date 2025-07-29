"""
Integration tests for the complete HDL parser system.
"""

import pytest
import tempfile
import os
from pathlib import Path

from hdl_parser.parser import HDLParser
from hdl_parser.simulator import ChipSimulator
from hdl_parser.test_runner import TestRunner


class TestIntegration:
    """Integration tests for the complete system."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.parser = HDLParser()
        self.simulator = ChipSimulator(self.parser)
        self.runner = TestRunner(self.parser, self.simulator)
        self.temp_dir = tempfile.mkdtemp()
    
    def teardown_method(self):
        """Clean up temp files."""
        import shutil
        shutil.rmtree(self.temp_dir)
    
    def create_temp_file(self, filename, content):
        """Create a temporary file with given content."""
        filepath = os.path.join(self.temp_dir, filename)
        with open(filepath, 'w') as f:
            f.write(content)
        return filepath
    
    def test_and_gate_integration(self):
        """Test complete flow with And gate."""
        # Create HDL file
        hdl_content = """
        CHIP And {
            IN a, b;
            OUT out;
            
            PARTS:
            Nand(a=a, b=b, out=nandOut);
            Not(in=nandOut, out=out);
        }
        """
        hdl_file = self.create_temp_file("And.hdl", hdl_content)
        
        # Create test file
        test_content = """a,b; out
0,0; 0
0,1; 0
1,0; 0
1,1; 1"""
        test_file = self.create_temp_file("And.tst", test_content)
        
        # Run tests
        passed, total = self.runner.run_tests(hdl_file, test_file)
        
        assert passed == 4
        assert total == 4
    
    def test_xor_gate_integration(self):
        """Test complete flow with Xor gate."""
        # Create HDL file
        hdl_content = """
        CHIP Xor {
            IN a, b;
            OUT out;
            
            PARTS:
            Not(in=a, out=nota);
            Not(in=b, out=notb);
            And(a=a, b=notb, out=aAndNotb);
            And(a=nota, b=b, out=notaAndb);
            Or(a=aAndNotb, b=notaAndb, out=out);
        }
        """
        hdl_file = self.create_temp_file("Xor.hdl", hdl_content)
        
        # Create test file
        test_content = """a,b; out
0,0; 0
0,1; 1
1,0; 1
1,1; 0"""
        test_file = self.create_temp_file("Xor.tst", test_content)
        
        # Run tests
        passed, total = self.runner.run_tests(hdl_file, test_file)
        
        assert passed == 4
        assert total == 4
    
    def test_nested_custom_chips(self):
        """Test loading nested custom chips."""
        # Create And.hdl (will be referenced by Xor)
        and_hdl = """
        CHIP And {
            IN a, b;
            OUT out;
            
            PARTS:
            Nand(a=a, b=b, out=nandOut);
            Not(in=nandOut, out=out);
        }
        """
        self.create_temp_file("And.hdl", and_hdl)
        
        # Create Xor.hdl that uses And
        xor_hdl = """
        CHIP Xor {
            IN a, b;
            OUT out;
            
            PARTS:
            Not(in=a, out=nota);
            Not(in=b, out=notb);
            And(a=a, b=notb, out=aAndNotb);
            And(a=nota, b=b, out=notaAndb);
            Or(a=aAndNotb, b=notaAndb, out=out);
        }
        """
        xor_file = self.create_temp_file("Xor.hdl", xor_hdl)
        
        # Change to temp directory so And.hdl can be found
        original_dir = os.getcwd()
        os.chdir(self.temp_dir)
        
        try:
            # Parse Xor which should automatically load And
            chip = self.parser.parse_file("Xor.hdl")
            
            # Verify And was loaded
            assert "And" in self.parser.chips_cache
            
            # Test simulation
            result = self.simulator.simulate(chip, {"a": 1, "b": 0})
            assert result == {"out": 1}
            
        finally:
            os.chdir(original_dir)
    
    def test_halfadder_integration(self):
        """Test HalfAdder with multiple outputs."""
        # Need Xor.hdl for HalfAdder
        xor_hdl = """
        CHIP Xor {
            IN a, b;
            OUT out;
            
            PARTS:
            Not(in=a, out=nota);
            Not(in=b, out=notb);
            And(a=a, b=notb, out=aAndNotb);
            And(a=nota, b=b, out=notaAndb);
            Or(a=aAndNotb, b=notaAndb, out=out);
        }
        """
        self.create_temp_file("Xor.hdl", xor_hdl)
        
        # Create HalfAdder
        halfadder_hdl = """
        CHIP HalfAdder {
            IN a, b;
            OUT sum, carry;
            
            PARTS:
            Xor(a=a, b=b, out=sum);
            And(a=a, b=b, out=carry);
        }
        """
        halfadder_file = self.create_temp_file("HalfAdder.hdl", halfadder_hdl)
        
        # Test file
        test_content = """a,b; sum,carry
0,0; 0,0
0,1; 1,0
1,0; 1,0
1,1; 0,1"""
        test_file = self.create_temp_file("HalfAdder.tst", test_content)
        
        # Change directory
        original_dir = os.getcwd()
        os.chdir(self.temp_dir)
        
        try:
            passed, total = self.runner.run_tests("HalfAdder.hdl", "HalfAdder.tst")
            assert passed == 4
            assert total == 4
        finally:
            os.chdir(original_dir)
    
    def test_test_file_with_comments(self):
        """Test that test files can contain comments."""
        hdl_content = """
        CHIP Not {
            IN in;
            OUT out;
            
            PARTS:
        }
        """
        hdl_file = self.create_temp_file("Not.hdl", hdl_content)
        
        test_content = """// Test file for Not gate
in; out
// Test case 1
0; 1
// Test case 2
1; 0

// Empty lines are ok"""
        test_file = self.create_temp_file("Not.tst", test_content)
        
        passed, total = self.runner.run_tests(hdl_file, test_file)
        assert passed == 2
        assert total == 2
    
    def test_failed_tests_reporting(self):
        """Test that failed tests are reported correctly."""
        # Create a broken And gate
        hdl_content = """
        CHIP And {
            IN a, b;
            OUT out;
            
            PARTS:
            Or(a=a, b=b, out=out);  // Wrong! Should be And logic
        }
        """
        hdl_file = self.create_temp_file("BrokenAnd.hdl", hdl_content)
        
        test_content = """a,b; out
0,0; 0
0,1; 0
1,0; 0
1,1; 1"""
        test_file = self.create_temp_file("And.tst", test_content)
        
        passed, total = self.runner.run_tests(hdl_file, test_file)
        
        # Should fail some tests
        assert passed < total
        assert total == 4