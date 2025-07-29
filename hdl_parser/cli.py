"""
Command-line interface for the HDL parser and tester.
"""

import sys
from pathlib import Path

from .parser import HDLParser
from .simulator import ChipSimulator
from .test_runner import TestRunner


def print_usage():
    """Print usage information."""
    print("HDL Parser and Chip Testing Framework")
    print("=====================================")
    print()
    print("Usage: python -m hdl_parser <chip.hdl> <test.txt>")
    print()
    print("Arguments:")
    print("  chip.hdl   - HDL file containing the chip definition")
    print("  test.txt   - Test vector file with input/output test cases")
    print()
    print("Example:")
    print("  python -m hdl_parser examples/chips/And.hdl examples/tests/And.tst")


def main():
    """Main entry point for the CLI."""
    # Check command line arguments
    if len(sys.argv) != 3:
        print_usage()
        sys.exit(1)
    
    chip_file = sys.argv[1]
    test_file = sys.argv[2]
    
    # Validate file paths
    chip_path = Path(chip_file)
    test_path = Path(test_file)
    
    if not chip_path.exists():
        print(f"Error: Chip file not found: {chip_file}")
        sys.exit(2)
    
    if not test_path.exists():
        print(f"Error: Test file not found: {test_file}")
        sys.exit(2)
    
    try:
        # Initialize components
        parser = HDLParser()
        simulator = ChipSimulator(parser)
        runner = TestRunner(parser, simulator)
        
        # Run tests
        passed, total = runner.run_tests(chip_file, test_file)
        
        # Exit with appropriate code
        if passed == total:
            sys.exit(0)  # All tests passed
        else:
            sys.exit(1)  # Some tests failed
    
    except Exception as e:
        print(f"\nError: {e}")
        sys.exit(2)


if __name__ == "__main__":
    main()