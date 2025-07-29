"""
Entry point for running the HDL parser as a module.

Allows running with: python -m hdl_parser
"""

from .cli import main

if __name__ == "__main__":
    main()