"""
Unit tests for the chip simulator module.
"""

import pytest
from hdl_parser.parser import HDLParser
from hdl_parser.simulator import ChipSimulator
from hdl_parser.models import ChipDefinition, ChipInstance, Connection


class TestChipSimulator:
    """Test cases for ChipSimulator class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.parser = HDLParser()
        self.simulator = ChipSimulator(self.parser)
    
    def test_simulate_nand_gate(self):
        """Test NAND gate simulation."""
        chip = self.parser.built_in_chips["Nand"]
        
        # Test all input combinations
        test_cases = [
            ({"a": 0, "b": 0}, {"out": 1}),
            ({"a": 0, "b": 1}, {"out": 1}),
            ({"a": 1, "b": 0}, {"out": 1}),
            ({"a": 1, "b": 1}, {"out": 0}),
        ]
        
        for inputs, expected in test_cases:
            result = self.simulator.simulate(chip, inputs)
            assert result == expected
    
    def test_simulate_not_gate(self):
        """Test NOT gate simulation."""
        chip = self.parser.built_in_chips["Not"]
        
        test_cases = [
            ({"in": 0}, {"out": 1}),
            ({"in": 1}, {"out": 0}),
        ]
        
        for inputs, expected in test_cases:
            result = self.simulator.simulate(chip, inputs)
            assert result == expected
    
    def test_simulate_and_gate(self):
        """Test AND gate simulation."""
        chip = self.parser.built_in_chips["And"]
        
        test_cases = [
            ({"a": 0, "b": 0}, {"out": 0}),
            ({"a": 0, "b": 1}, {"out": 0}),
            ({"a": 1, "b": 0}, {"out": 0}),
            ({"a": 1, "b": 1}, {"out": 1}),
        ]
        
        for inputs, expected in test_cases:
            result = self.simulator.simulate(chip, inputs)
            assert result == expected
    
    def test_simulate_or_gate(self):
        """Test OR gate simulation."""
        chip = self.parser.built_in_chips["Or"]
        
        test_cases = [
            ({"a": 0, "b": 0}, {"out": 0}),
            ({"a": 0, "b": 1}, {"out": 1}),
            ({"a": 1, "b": 0}, {"out": 1}),
            ({"a": 1, "b": 1}, {"out": 1}),
        ]
        
        for inputs, expected in test_cases:
            result = self.simulator.simulate(chip, inputs)
            assert result == expected
    
    def test_simulate_composite_chip(self):
        """Test simulating a composite chip (And gate made from Nand and Not)."""
        # Create And gate from Nand and Not
        and_chip = ChipDefinition("And", ["a", "b"], ["out"])
        
        # Nand(a=a, b=b, out=nandOut)
        nand_part = ChipInstance("Nand", "Nand_0")
        nand_part.connections = [
            Connection("a", "a"),
            Connection("b", "b"),
            Connection("nandOut", "out")
        ]
        
        # Not(in=nandOut, out=out)
        not_part = ChipInstance("Not", "Not_0")
        not_part.connections = [
            Connection("nandOut", "in"),
            Connection("out", "out")
        ]
        
        and_chip.parts = [nand_part, not_part]
        and_chip.internal_pins = {"nandOut"}
        
        # Test And gate behavior
        test_cases = [
            ({"a": 0, "b": 0}, {"out": 0}),
            ({"a": 0, "b": 1}, {"out": 0}),
            ({"a": 1, "b": 0}, {"out": 0}),
            ({"a": 1, "b": 1}, {"out": 1}),
        ]
        
        for inputs, expected in test_cases:
            result = self.simulator.simulate(and_chip, inputs)
            assert result == expected
    
    def test_signal_propagation(self):
        """Test that signals propagate correctly through internal connections."""
        # Create a simple chain: Not -> Not (should act as a buffer)
        buffer_chip = ChipDefinition("Buffer", ["in"], ["out"])
        
        not1 = ChipInstance("Not", "Not_0")
        not1.connections = [
            Connection("in", "in"),
            Connection("temp", "out")
        ]
        
        not2 = ChipInstance("Not", "Not_1")
        not2.connections = [
            Connection("temp", "in"),
            Connection("out", "out")
        ]
        
        buffer_chip.parts = [not1, not2]
        buffer_chip.internal_pins = {"temp"}
        
        # Test buffer behavior
        assert self.simulator.simulate(buffer_chip, {"in": 0}) == {"out": 0}
        assert self.simulator.simulate(buffer_chip, {"in": 1}) == {"out": 1}
    
    def test_multiple_outputs(self):
        """Test chip with multiple outputs."""
        # Create a chip that outputs both AND and OR of inputs
        multi_chip = ChipDefinition("MultiOut", ["a", "b"], ["and_out", "or_out"])
        
        and_part = ChipInstance("And", "And_0")
        and_part.connections = [
            Connection("a", "a"),
            Connection("b", "b"),
            Connection("and_out", "out")
        ]
        
        or_part = ChipInstance("Or", "Or_0")
        or_part.connections = [
            Connection("a", "a"),
            Connection("b", "b"),
            Connection("or_out", "out")
        ]
        
        multi_chip.parts = [and_part, or_part]
        
        # Test
        result = self.simulator.simulate(multi_chip, {"a": 1, "b": 0})
        assert result == {"and_out": 0, "or_out": 1}
    
    def test_default_values(self):
        """Test that unconnected pins default to 0."""
        # Create chip with unconnected internal pin
        chip = ChipDefinition("Test", ["a"], ["out"])
        chip.internal_pins = {"unconnected"}
        
        not_part = ChipInstance("Not", "Not_0")
        not_part.connections = [
            Connection("a", "in"),
            Connection("out", "out")
        ]
        chip.parts = [not_part]
        
        result = self.simulator.simulate(chip, {"a": 1})
        assert result == {"out": 0}
        
        # Verify internal pin was initialized to 0
        assert self.simulator.signal_values.get("unconnected") == 0
    
    def test_complex_circuit(self):
        """Test a more complex circuit (XOR gate)."""
        # Build XOR from basic gates
        xor_chip = ChipDefinition("Xor", ["a", "b"], ["out"])
        
        # Create the parts for XOR
        # nota = Not(a)
        not_a = ChipInstance("Not", "Not_0")
        not_a.connections = [Connection("a", "in"), Connection("nota", "out")]
        
        # notb = Not(b)
        not_b = ChipInstance("Not", "Not_1")
        not_b.connections = [Connection("b", "in"), Connection("notb", "out")]
        
        # aAndNotb = And(a, notb)
        and1 = ChipInstance("And", "And_0")
        and1.connections = [
            Connection("a", "a"),
            Connection("notb", "b"),
            Connection("aAndNotb", "out")
        ]
        
        # notaAndb = And(nota, b)
        and2 = ChipInstance("And", "And_1")
        and2.connections = [
            Connection("nota", "a"),
            Connection("b", "b"),
            Connection("notaAndb", "out")
        ]
        
        # out = Or(aAndNotb, notaAndb)
        or_gate = ChipInstance("Or", "Or_0")
        or_gate.connections = [
            Connection("aAndNotb", "a"),
            Connection("notaAndb", "b"),
            Connection("out", "out")
        ]
        
        xor_chip.parts = [not_a, not_b, and1, and2, or_gate]
        xor_chip.internal_pins = {"nota", "notb", "aAndNotb", "notaAndb"}
        
        # Test XOR behavior
        test_cases = [
            ({"a": 0, "b": 0}, {"out": 0}),
            ({"a": 0, "b": 1}, {"out": 1}),
            ({"a": 1, "b": 0}, {"out": 1}),
            ({"a": 1, "b": 1}, {"out": 0}),
        ]
        
        for inputs, expected in test_cases:
            result = self.simulator.simulate(xor_chip, inputs)
            assert result == expected