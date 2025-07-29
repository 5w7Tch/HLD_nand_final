"""
HDL file parser module.
"""

import re
from pathlib import Path
from typing import Dict, Optional

from .models import ChipDefinition, ChipInstance, Connection


class HDLParser:
    """Parses HDL files and builds chip definitions."""
    
    def __init__(self):
        self.chips_cache: Dict[str, ChipDefinition] = {}
        self._init_builtin_chips()
    
    def _init_builtin_chips(self):
        """Initialize built-in chip definitions."""
        self.built_in_chips = {
            'Nand': ChipDefinition('Nand', ['a', 'b'], ['out']),
            'Not': ChipDefinition('Not', ['in'], ['out']),
            'And': ChipDefinition('And', ['a', 'b'], ['out']),
            'Or': ChipDefinition('Or', ['a', 'b'], ['out'])
        }
        # Add built-ins to cache
        self.chips_cache.update(self.built_in_chips)
    
    def parse_file(self, filename: str) -> ChipDefinition:
        """Parse an HDL file and return the chip definition."""
        path = Path(filename)
        if not path.exists():
            raise FileNotFoundError(f"HDL file not found: {filename}")
        
        with open(path, 'r') as f:
            content = f.read()
        
        return self.parse_hdl(content, path.stem)
    
    def parse_hdl(self, content: str, expected_name: Optional[str] = None) -> ChipDefinition:
        """Parse HDL content and build chip definition."""
        # Remove comments
        content = self._remove_comments(content)
        
        # Extract chip definition
        chip_match = re.search(r'CHIP\s+(\w+)\s*{(.*?)}', content, re.DOTALL)
        if not chip_match:
            raise ValueError("Invalid HDL format - no CHIP definition found")
        
        chip_name = chip_match.group(1)
        chip_body = chip_match.group(2)
        
        # Parse sections
        inputs = self._parse_io_section(chip_body, 'IN')
        outputs = self._parse_io_section(chip_body, 'OUT')
        parts, internal_pins = self._parse_parts_section(chip_body, inputs, outputs)
        
        # Create chip definition
        chip_def = ChipDefinition(chip_name, inputs, outputs, parts, internal_pins)
        
        # Cache the chip
        self.chips_cache[chip_name] = chip_def
        
        return chip_def
    
    def _remove_comments(self, content: str) -> str:
        """Remove single-line and multi-line comments from HDL content."""
        # Remove single-line comments
        content = re.sub(r'//.*$', '', content, flags=re.MULTILINE)
        # Remove multi-line comments
        content = re.sub(r'/\*.*?\*/', '', content, flags=re.DOTALL)
        return content
    
    def _parse_io_section(self, chip_body: str, section_name: str) -> list:
        """Parse IN or OUT section and return list of pin names."""
        pattern = rf'{section_name}\s+(.*?);'
        match = re.search(pattern, chip_body)
        
        if not match:
            return []
        
        pins_str = match.group(1)
        # Split by comma and clean up whitespace
        pins = [pin.strip() for pin in pins_str.split(',') if pin.strip()]
        
        return pins
    
    def _parse_parts_section(self, chip_body: str, inputs: list, outputs: list) -> tuple:
        """Parse PARTS section and return list of chip instances and internal pins."""
        parts_match = re.search(r'PARTS:\s*(.*?)(?:}|$)', chip_body, re.DOTALL)
        
        if not parts_match:
            return [], set()
        
        parts = []
        internal_pins = set()
        parts_content = parts_match.group(1)
        
        # Parse each part instantiation
        part_pattern = r'(\w+)\s*\((.*?)\)\s*;'
        
        for match in re.finditer(part_pattern, parts_content, re.DOTALL):
            chip_type = match.group(1)
            connections_str = match.group(2)
            
            # Create unique instance name
            instance_name = f"{chip_type}_{len(parts)}"
            instance = ChipInstance(chip_type, instance_name)
            
            # Parse connections
            connections = self._parse_connections(connections_str)
            instance.connections = connections
            
            # Track internal pins
            for conn in connections:
                # Source pin
                if conn.source not in inputs and conn.source not in outputs:
                    internal_pins.add(conn.source)
                # Destination pin (for sub-chip inputs that might be internal)
                if conn.destination in ['a', 'b', 'in'] and conn.source not in inputs:
                    if conn.source not in outputs:
                        internal_pins.add(conn.source)
            
            parts.append(instance)
        
        return parts, internal_pins
    
    def _parse_connections(self, connections_str: str) -> list:
        """Parse connection string and return list of Connection objects."""
        connections = []
        
        # Pattern to match pin=signal connections
        conn_pattern = r'(\w+)\s*=\s*(\w+)'
        
        for match in re.finditer(conn_pattern, connections_str):
            destination = match.group(1)  # Pin name on the sub-chip
            source = match.group(2)       # Signal name in parent chip
            connections.append(Connection(source, destination))
        
        return connections
    
    def get_chip_definition(self, chip_name: str) -> Optional[ChipDefinition]:
        """Get a chip definition from cache or try to load it."""
        # Check cache first
        if chip_name in self.chips_cache:
            return self.chips_cache[chip_name]
        
        # Try to load from file
        try:
            chip_file = f"{chip_name}.hdl"
            return self.parse_file(chip_file)
        except FileNotFoundError:
            return None