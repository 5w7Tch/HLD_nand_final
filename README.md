# HDL Parser

## Installation

### From Source

```bash
git clone https://github.com/yourusername/hdl-parser.git
```

## Quick Start

### Command Line Usage


### Example

```bash
# Test an And gate
python -m hdl_parser examples/chips/And.hdl examples/tests/And.tst
```

## HDL File Format

HDL files define chip structure using the following syntax:

```hdl
CHIP ChipName {
    IN input1, input2, ...;
    OUT output1, output2, ...;
    
    PARTS:
    Component1(pin1=signal1, pin2=signal2, ...);
    Component2(pin1=signal3, pin2=signal4, ...);
}
```

### Example: And Gate

```hdl
CHIP And {
    IN a, b;
    OUT out;
    
    PARTS:
    Nand(a=a, b=b, out=nandOut);
    Not(in=nandOut, out=out);
}
```

## Test Vector Format

Test files use CSV-style format with inputs and expected outputs:

```
input1,input2; output1,output2
0,0; 0,0
0,1; 0,1
1,0; 0,1
1,1; 1,0
```

### Example: And Gate Test

```
a,b; out
0,0; 0
0,1; 0
1,0; 0
1,1; 1
```

## Built-in Chips

The following chips are built-in and don't require HDL files:

| Chip | Inputs | Outputs | Logic |
|------|---------|----------|--------|
| Nand | a, b | out | !(a & b) |
| Not | in | out | !in |
| And | a, b | out | a & b |
| Or | a, b | out | a \| b |

## Project Structure

```
hdl_parser/
├── __init__.py       # Package initialization
├── __main__.py       # Module entry point
├── models.py         # Data models
├── parser.py         # HDL parsing logic
├── simulator.py      # Chip simulation
├── test_runner.py    # Test execution
└── cli.py           # Command-line interface
```

## Development

### Running Tests

```bash
# Run unit tests
python -m pytest tests/

# Run with coverage
python -m pytest --cov=hdl_parser tests/
```

### Code Style

The project uses standard Python formatting. Run linting with:

```bash
# Check code style
flake8 hdl_parser/

# Format code
black hdl_parser/
```

## Limitations

- Only single-bit inputs/outputs are supported
- No support for multi-bit buses or sub-buses
- Sequential chips (with clocks/memory) are not supported
- Assumes all HDL files are syntactically correct

## License

MIT License - see LICENSE file for details

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request
