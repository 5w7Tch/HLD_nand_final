
import re
import sys
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Set
from dataclasses import dataclass, field


@dataclass
class Connection:
    """Represents a connection between chip pins"""
    source: str
    destination: str


@dataclass
class ChipInstance:
    """Represents an instance of a chip within another chip"""
    chip_type: str
    name: str
    connections: List[Connection] = field(default_factory=list)


@dataclass
class ChipDefinition:
    """Represents a complete chip definition"""
    name: str
    inputs: List[str] = field(default_factory=list)
    outputs: List[str] = field(default_factory=list)
    parts: List[ChipInstance] = field(default_factory=list)
    internal_pins: Set[str] = field(default_factory=set)


class HDLParser:
    """Parses HDL files and builds chip definitions"""
    
    def __init__(self):
        self.chips_cache: Dict[str, ChipDefinition] = {}
        self.built_in_chips = {
            'Nand': ChipDefinition('Nand', ['a', 'b'], ['out']),
            'Not': ChipDefinition('Not', ['in'], ['out']),
            'And': ChipDefinition('And', ['a', 'b'], ['out']),
            'Or': ChipDefinition('Or', ['a', 'b'], ['out'])
        }
    
    def parse_file(self, filename: str) -> ChipDefinition:
        """Parse an HDL file and return the chip definition"""
        path = Path(filename)
        if not path.exists():
            raise FileNotFoundError(f"HDL file not found: {filename}")
        
        with open(path, 'r') as f:
            content = f.read()
        
        return self.parse_hdl(content, path.stem)
    
    def parse_hdl(self, content: str, chip_name: str) -> ChipDefinition:
        """Parse HDL content and build chip definition"""
        # Remove comments
        content = re.sub(r'//.*$', '', content, flags=re.MULTILINE)
        content = re.sub(r'/\*.*?\*/', '', content, flags=re.DOTALL)
        
        # Extract chip sections
        chip_match = re.search(r'CHIP\s+(\w+)\s*{(.*?)}', content, re.DOTALL)
        if not chip_match:
            raise ValueError(f"Invalid HDL format - no CHIP definition found")
        
        found_name = chip_match.group(1)
        chip_body = chip_match.group(2)
        
        # Parse IN section
        in_match = re.search(r'IN\s+(.*?);', chip_body)
        inputs = []
        if in_match:
            inputs = [pin.strip() for pin in in_match.group(1).split(',')]
        
        # Parse OUT section
        out_match = re.search(r'OUT\s+(.*?);', chip_body)
        outputs = []
        if out_match:
            outputs = [pin.strip() for pin in out_match.group(1).split(',')]
        
        # Parse PARTS section
        parts_match = re.search(r'PARTS:\s*(.*?)(?:}|$)', chip_body, re.DOTALL)
        parts = []
        internal_pins = set()
        
        if parts_match:
            parts_content = parts_match.group(1)
            # Parse each part instantiation
            part_pattern = r'(\w+)\s*\((.*?)\)\s*;'
            for match in re.finditer(part_pattern, parts_content, re.DOTALL):
                chip_type = match.group(1)
                connections_str = match.group(2)
                
                instance = ChipInstance(chip_type, f"{chip_type}_{len(parts)}")
                
                # Parse connections
                conn_pattern = r'(\w+)\s*=\s*(\w+)'
                for conn_match in re.finditer(conn_pattern, connections_str):
                    dest = conn_match.group(1)
                    src = conn_match.group(2)
                    instance.connections.append(Connection(src, dest))
                    
                    # Track internal pins
                    if src not in inputs and src not in outputs:
                        internal_pins.add(src)
                    if dest not in inputs and dest not in outputs:
                        internal_pins.add(dest)
                
                parts.append(instance)
        
        chip_def = ChipDefinition(found_name, inputs, outputs, parts, internal_pins)
        self.chips_cache[found_name] = chip_def
        return chip_def


class ChipSimulator:
    """Simulates chip behavior"""
    
    def __init__(self, parser: HDLParser):
        self.parser = parser
        self.signal_values: Dict[str, int] = {}
    
    def simulate(self, chip_def: ChipDefinition, inputs: Dict[str, int]) -> Dict[str, int]:
        """Simulate a chip with given inputs and return outputs"""
        # Reset signal values
        self.signal_values = {}
        
        # Set input values
        for inp, val in inputs.items():
            self.signal_values[inp] = val
        
        # Initialize internal pins to 0
        for pin in chip_def.internal_pins:
            self.signal_values[pin] = 0
        
        # Simulate until stable (simple iterative approach)
        max_iterations = 100
        for _ in range(max_iterations):
            changed = False
            
            for part in chip_def.parts:
                # Get chip definition for this part
                if part.chip_type in self.parser.built_in_chips:
                    # Simulate built-in chip
                    changed |= self._simulate_builtin(part)
                else:
                    # Load and simulate custom chip
                    if part.chip_type not in self.parser.chips_cache:
                        # Parse the chip file
                        chip_file = f"{part.chip_type}.hdl"
                        sub_chip_def = self.parser.parse_file(chip_file)
                    else:
                        sub_chip_def = self.parser.chips_cache[part.chip_type]
                    
                    changed |= self._simulate_custom(part, sub_chip_def)
            
            if not changed:
                break
        
        # Extract output values
        outputs = {}
        for out in chip_def.outputs:
            outputs[out] = self.signal_values.get(out, 0)
        
        return outputs
    
    def _simulate_builtin(self, part: ChipInstance) -> bool:
        """Simulate a built-in chip"""
        changed = False
        
        # Get input values for the chip
        input_vals = {}
        for conn in part.connections:
            if conn.destination in ['a', 'b', 'in']:  # Input pins
                input_vals[conn.destination] = self.signal_values.get(conn.source, 0)
        
        # Calculate output based on chip type
        output_val = 0
        if part.chip_type == 'Nand':
            if 'a' in input_vals and 'b' in input_vals:
                output_val = 0 if (input_vals['a'] and input_vals['b']) else 1
        elif part.chip_type == 'Not':
            if 'in' in input_vals:
                output_val = 0 if input_vals['in'] else 1
        elif part.chip_type == 'And':
            if 'a' in input_vals and 'b' in input_vals:
                output_val = 1 if (input_vals['a'] and input_vals['b']) else 0
        elif part.chip_type == 'Or':
            if 'a' in input_vals and 'b' in input_vals:
                output_val = 1 if (input_vals['a'] or input_vals['b']) else 0
        
        # Set output value
        for conn in part.connections:
            if conn.destination == 'out':  # Output pin
                old_val = self.signal_values.get(conn.source, 0)
                self.signal_values[conn.source] = output_val
                if old_val != output_val:
                    changed = True
        
        return changed
    
    def _simulate_custom(self, part: ChipInstance, chip_def: ChipDefinition) -> bool:
        """Simulate a custom chip"""
        changed = False
        
        # Map connections to create input values for sub-chip
        sub_inputs = {}
        for conn in part.connections:
            if conn.destination in chip_def.inputs:
                sub_inputs[conn.destination] = self.signal_values.get(conn.source, 0)
        
        # Simulate the sub-chip
        sub_outputs = self.simulate(chip_def, sub_inputs)
        
        # Map outputs back to parent chip signals
        for conn in part.connections:
            if conn.destination in chip_def.outputs:
                output_val = sub_outputs[conn.destination]
                old_val = self.signal_values.get(conn.source, 0)
                self.signal_values[conn.source] = output_val
                if old_val != output_val:
                    changed = True
        
        return changed


class TestRunner:
    """Runs test vectors against chips"""
    
    def __init__(self, parser: HDLParser, simulator: ChipSimulator):
        self.parser = parser
        self.simulator = simulator
    
    def run_tests(self, chip_file: str, test_file: str) -> Tuple[int, int]:
        """Run test vectors and return (passed, total) counts"""
        # Parse the chip
        chip_def = self.parser.parse_file(chip_file)
        
        # Read test vectors
        test_cases = self._read_test_file(test_file)
        
        passed = 0
        total = len(test_cases)
        
        print(f"\nTesting {chip_def.name} chip")
        print("=" * 50)
        
        for i, (inputs, expected) in enumerate(test_cases):
            # Simulate
            outputs = self.simulator.simulate(chip_def, inputs)
            
            # Check results
            test_passed = True
            for out_name, expected_val in expected.items():
                actual_val = outputs.get(out_name, 0)
                if actual_val != expected_val:
                    test_passed = False
            
            # Print result
            if test_passed:
                passed += 1
                status = "PASS"
            else:
                status = "FAIL"
            
            input_str = ", ".join(f"{k}={v}" for k, v in inputs.items())
            expected_str = ", ".join(f"{k}={v}" for k, v in expected.items())
            actual_str = ", ".join(f"{k}={v}" for k, v in outputs.items())
            
            print(f"Test {i+1}: {status}")
            print(f"  Inputs:   {input_str}")
            print(f"  Expected: {expected_str}")
            if not test_passed:
                print(f"  Actual:   {actual_str}")
            print()
        
        print("=" * 50)
        print(f"Summary: {passed}/{total} tests passed")
        
        return passed, total
    
    def _read_test_file(self, filename: str) -> List[Tuple[Dict[str, int], Dict[str, int]]]:
        """Read test vectors from file"""
        test_cases = []
        
        with open(filename, 'r') as f:
            lines = f.readlines()
        
        if not lines:
            return test_cases
        
        # Parse header
        header = lines[0].strip()
        parts = header.split(';')
        input_names = [name.strip() for name in parts[0].split(',')]
        output_names = [name.strip() for name in parts[1].split(',')]
        
        # Parse test cases
        for line in lines[1:]:
            line = line.strip()
            if not line:
                continue
            
            parts = line.split(';')
            input_vals = [int(val.strip()) for val in parts[0].split(',')]
            output_vals = [int(val.strip()) for val in parts[1].split(',')]
            
            inputs = dict(zip(input_names, input_vals))
            outputs = dict(zip(output_names, output_vals))
            
            test_cases.append((inputs, outputs))
        
        return test_cases


def main():
    """Main entry point"""
    if len(sys.argv) != 3:
        print("Usage: python hdl_parser.py <chip.hdl> <test.txt>")
        sys.exit(1)
    
    chip_file = sys.argv[1]
    test_file = sys.argv[2]
    
    # Initialize components
    parser = HDLParser()
    simulator = ChipSimulator(parser)
    runner = TestRunner(parser, simulator)
    
    try:
        # Run tests
        passed, total = runner.run_tests(chip_file, test_file)
        
        # Exit with appropriate code
        if passed == total:
            sys.exit(0)
        else:
            sys.exit(1)
    
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(2)


if __name__ == "__main__":
    main()