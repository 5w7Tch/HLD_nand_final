"""
Data models for HDL parser and simulator.
"""

from dataclasses import dataclass, field
from typing import List, Set


@dataclass
class Connection:
    """Represents a connection between chip pins."""
    source: str
    destination: str
    
    def __repr__(self):
        return f"{self.destination}={self.source}"


@dataclass
class ChipInstance:
    """Represents an instance of a chip within another chip."""
    chip_type: str
    name: str
    connections: List[Connection] = field(default_factory=list)
    
    def __repr__(self):
        conn_str = ", ".join(str(c) for c in self.connections)
        return f"{self.chip_type}({conn_str})"


@dataclass
class ChipDefinition:
    """Represents a complete chip definition."""
    name: str
    inputs: List[str] = field(default_factory=list)
    outputs: List[str] = field(default_factory=list)
    parts: List[ChipInstance] = field(default_factory=list)
    internal_pins: Set[str] = field(default_factory=set)
    
    def __repr__(self):
        return (f"ChipDefinition(name={self.name}, "
                f"inputs={self.inputs}, outputs={self.outputs}, "
                f"parts={len(self.parts)} components)")
    
    def is_builtin(self) -> bool:
        """Check if this is a built-in chip."""
        return self.name in ['Nand', 'Not', 'And', 'Or'] and not self.parts