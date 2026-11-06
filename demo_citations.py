"""Demo citation script at repository root for ContextCon 04."""

import sys
from pathlib import Path

# Ensure repository root is on sys.path for direct execution (e.g. plain 'python demo_citations.py' or isolated environments)
repo_root = Path(__file__).resolve().parent
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

from src.discovery.demo_citation import run_demo

if __name__ == "__main__":
    live_flag = "--live" in sys.argv
    sys.exit(run_demo(live=live_flag))
