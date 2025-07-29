"""
Chip simulation module.
"""

from typing import Dict, Optional

from .models import ChipDefinition, ChipInstance
from .parser import HDLParser


class ChipSimulator:
    """Simulates chip behavior based on HDL definitions."""

    def __init__(self, parser: HDLParser):
        self.parser = parser
        self.signal_values: Dict[str, int] = {}
        self.max_iterations = 100  # Prevent infinite loops

    def simulate(
        self, chip_def: ChipDefinition, inputs: Dict[str, int]
    ) -> Dict[str, int]:
        """
        Simulate a chip with given inputs and return outputs.

        Args:
            chip_def: The chip definition to simulate
            inputs: Dictionary mapping input pin names to values (0 or 1)

        Returns:
            Dictionary mapping output pin names to computed values
        """
        # Check if this is a built-in chip (no parts)
        if chip_def.name in self.parser.built_in_chips and not chip_def.parts:
            return self._simulate_builtin_chip(chip_def, inputs)

        # Reset signal values
        self.signal_values = {}

        # Set input values
        for pin_name, value in inputs.items():
            self.signal_values[pin_name] = value

        # Initialize internal pins to 0
        for pin in chip_def.internal_pins:
            self.signal_values[pin] = 0

        # Initialize output pins to 0
        for pin in chip_def.outputs:
            if pin not in self.signal_values:
                self.signal_values[pin] = 0

        # Simulate until stable
        for iteration in range(self.max_iterations):
            changed = False

            # Evaluate each part
            for part in chip_def.parts:
                if self._simulate_part(part):
                    changed = True

            # If no changes, we've reached a stable state
            if not changed:
                break

        # Extract output values
        outputs = {}
        for output_pin in chip_def.outputs:
            outputs[output_pin] = self.signal_values.get(output_pin, 0)

        return outputs

    def _simulate_builtin_chip(
        self, chip_def: ChipDefinition, inputs: Dict[str, int]
    ) -> Dict[str, int]:
        """Simulate a built-in chip directly."""
        output_val = 0

        if chip_def.name == "Nand":
            a = inputs.get("a", 0)
            b = inputs.get("b", 0)
            output_val = 0 if (a and b) else 1
        elif chip_def.name == "Not":
            in_val = inputs.get("in", 0)
            output_val = 0 if in_val else 1
        elif chip_def.name == "And":
            a = inputs.get("a", 0)
            b = inputs.get("b", 0)
            output_val = 1 if (a and b) else 0
        elif chip_def.name == "Or":
            a = inputs.get("a", 0)
            b = inputs.get("b", 0)
            output_val = 1 if (a or b) else 0

        # Return the output
        return {"out": output_val}

    def _simulate_part(self, part: ChipInstance) -> bool:
        """
        Simulate a single chip instance.

        Returns:
            True if any signal changed, False otherwise
        """
        # Check if it's a built-in chip
        if part.chip_type in self.parser.built_in_chips:
            return self._simulate_builtin_part(part)
        else:
            return self._simulate_custom(part)

    def _simulate_builtin_part(self, part: ChipInstance) -> bool:
        """Simulate a built-in chip part."""
        changed = False

        # Get input values
        input_vals = {}
        output_pin = None
        output_signal = None

        for conn in part.connections:
            if conn.destination in ["a", "b", "in"]:  # Input pins
                input_vals[conn.destination] = self.signal_values.get(conn.source, 0)
            elif conn.destination == "out":  # Output pin
                output_pin = conn.destination
                output_signal = conn.source

        # Calculate output based on chip type
        output_val = self._evaluate_builtin(part.chip_type, input_vals)

        # Update output signal if changed
        if output_signal is not None:
            old_val = self.signal_values.get(output_signal, 0)
            if old_val != output_val:
                self.signal_values[output_signal] = output_val
                changed = True

        return changed

    def _evaluate_builtin(self, chip_type: str, inputs: Dict[str, int]) -> int:
        """Evaluate a built-in chip logic."""
        if chip_type == "Nand":
            a = inputs.get("a", 0)
            b = inputs.get("b", 0)
            return 0 if (a and b) else 1

        elif chip_type == "Not":
            in_val = inputs.get("in", 0)
            return 0 if in_val else 1

        elif chip_type == "And":
            a = inputs.get("a", 0)
            b = inputs.get("b", 0)
            return 1 if (a and b) else 0

        elif chip_type == "Or":
            a = inputs.get("a", 0)
            b = inputs.get("b", 0)
            return 1 if (a or b) else 0

        return 0

    def _simulate_custom(self, part: ChipInstance) -> bool:
        """Simulate a custom (non-builtin) chip."""
        changed = False

        # Get the chip definition
        chip_def = self.parser.get_chip_definition(part.chip_type)
        if not chip_def:
            raise ValueError(f"Unknown chip type: {part.chip_type}")

        # Map connections to create input values for sub-chip
        sub_inputs = {}
        output_mappings = {}  # Maps sub-chip output to parent signal

        for conn in part.connections:
            if conn.destination in chip_def.inputs:
                # This is an input to the sub-chip
                sub_inputs[conn.destination] = self.signal_values.get(conn.source, 0)
            elif conn.destination in chip_def.outputs:
                # This is an output from the sub-chip
                output_mappings[conn.destination] = conn.source

        # Simulate the sub-chip
        sub_outputs = self.simulate(chip_def, sub_inputs)

        # Map outputs back to parent chip signals
        for sub_output, parent_signal in output_mappings.items():
            new_val = sub_outputs.get(sub_output, 0)
            old_val = self.signal_values.get(parent_signal, 0)

            if old_val != new_val:
                self.signal_values[parent_signal] = new_val
                changed = True

        return changed
