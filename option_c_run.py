#!/usr/bin/env python3
"""Root-level entrypoint for one-item Option C discovery run."""

import sys
from pathlib import Path

repo_root = Path(__file__).resolve().parent
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

from src.discovery.option_c_run import main

if __name__ == "__main__":
    sys.exit(main())
