from pathlib import Path

from kash.exec import import_and_register

# TODO: Find a way to match action docstrings with CLI command docstrings
# (without paying import cost in CLI).

import_and_register(__package__, Path(__file__).parent)
