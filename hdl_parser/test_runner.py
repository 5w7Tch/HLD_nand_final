"""
Test runner module for executing test vectors against chips.
"""

from pathlib import Path
from typing import List, Tuple, Dict

from .models import ChipDefinition
from .parser import HDLParser
from .simulator import ChipSimulator


class TestCase:
    """Represents a single test case."""

    def __init__(self, inputs: Dict[str, int], expected_outputs: Dict[str, int]):
        self.inputs = inputs
        self.expected_outputs = expected_outputs
        self.actual_outputs = {}
        self.passed = False

    def __repr__(self):
        return f"TestCase(inputs={self.inputs}, expected={self.expected_outputs})"


class TestRunner:
    """Runs test vectors against chips and reports results."""

    def __init__(self, parser: HDLParser, simulator: ChipSimulator):
        self.parser = parser
        self.simulator = simulator

    def run_tests(self, chip_file: str, test_file: str) -> Tuple[int, int]:
        """
        Run test vectors from a file against a chip.

        Args:
            chip_file: Path to the HDL file
            test_file: Path to the test vector file

        Returns:
            Tuple of (passed_count, total_count)
        """
        # Parse the chip
        chip_def = self.parser.parse_file(chip_file)

        # Read and parse test vectors
        test_cases = self._read_test_file(test_file)

        if not test_cases:
            print("No test cases found!")
            return 0, 0

        # Run tests
        passed = 0
        total = len(test_cases)

        self._print_header(chip_def.name)

        for i, test_case in enumerate(test_cases):
            # Simulate the chip
            test_case.actual_outputs = self.simulator.simulate(
                chip_def, test_case.inputs
            )

            # Check if test passed
            test_case.passed = self._check_outputs(
                test_case.expected_outputs, test_case.actual_outputs
            )

            if test_case.passed:
                passed += 1

            # Print test result
            self._print_test_result(i + 1, test_case)

        # Print summary
        self._print_summary(passed, total)

        return passed, total

    def _read_test_file(self, filename: str) -> List[TestCase]:
        """Read and parse test vector file."""
        test_cases = []

        path = Path(filename)
        if not path.exists():
            raise FileNotFoundError(f"Test file not found: {filename}")

        with open(path, "r") as f:
            lines = f.readlines()

        if not lines:
            return test_cases

        # Find the header line (first non-comment line)
        header_line = None
        header_index = 0

        for i, line in enumerate(lines):
            line = line.strip()
            # Skip empty lines and comments
            if not line or line.startswith("//"):
                continue
            # This is the header
            header_line = line
            header_index = i
            break

        if not header_line:
            raise ValueError("No header line found in test file")

        if ";" not in header_line:
            raise ValueError("Invalid test file format - header must contain ';'")

        # Parse header
        parts = header_line.split(";")
        input_names = [name.strip() for name in parts[0].split(",") if name.strip()]
        output_names = [name.strip() for name in parts[1].split(",") if name.strip()]

        # Parse test cases (lines after header)
        for line_num, line in enumerate(
            lines[header_index + 1 :], start=header_index + 2
        ):
            line = line.strip()

            # Skip empty lines and comments
            if not line or line.startswith("//"):
                continue

            if ";" not in line:
                print(f"Warning: Skipping invalid line {line_num}: {line}")
                continue

            parts = line.split(";")

            try:
                # Parse input values
                input_vals = [int(val.strip()) for val in parts[0].split(",")]
                inputs = dict(zip(input_names, input_vals))

                # Parse output values
                output_vals = [int(val.strip()) for val in parts[1].split(",")]
                outputs = dict(zip(output_names, output_vals))

                test_cases.append(TestCase(inputs, outputs))

            except (ValueError, IndexError) as e:
                print(f"Warning: Error parsing line {line_num}: {line}")
                continue

        return test_cases

    def _check_outputs(self, expected: Dict[str, int], actual: Dict[str, int]) -> bool:
        """Check if actual outputs match expected outputs."""
        for pin_name, expected_val in expected.items():
            if actual.get(pin_name, 0) != expected_val:
                return False
        return True

    def _print_header(self, chip_name: str):
        """Print test run header."""
        print(f"\nTesting {chip_name} chip")
        print("=" * 50)

    def _print_test_result(self, test_num: int, test_case: TestCase):
        """Print result for a single test case."""
        status = "PASS" if test_case.passed else "FAIL"

        # Format input/output strings
        input_str = ", ".join(f"{k}={v}" for k, v in sorted(test_case.inputs.items()))
        expected_str = ", ".join(
            f"{k}={v}" for k, v in sorted(test_case.expected_outputs.items())
        )

        print(f"Test {test_num}: {status}")
        print(f"  Inputs:   {input_str}")
        print(f"  Expected: {expected_str}")

        if not test_case.passed:
            actual_str = ", ".join(
                f"{k}={v}" for k, v in sorted(test_case.actual_outputs.items())
            )
            print(f"  Actual:   {actual_str}")

        print()  # Empty line between tests

    def _print_summary(self, passed: int, total: int):
        """Print test run summary."""
        print("=" * 50)
        print(f"Summary: {passed}/{total} tests passed")

        if passed == total:
            print("All tests passed! ✓")
        else:
            failed = total - passed
            print(f"{failed} test(s) failed ✗")
