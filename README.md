# HDL Parser

## Installation

### From Source

```bash
git https://github.com/azhgh22/HDL_Simulator.git
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


## Development

### Running Tests

```bash
# Run unit tests
python -m pytest tests/
pytest -v

# Run with coverage
python -m pytest --cov=hdl_parser tests/
```

