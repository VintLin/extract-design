#!/usr/bin/env python3
"""
Run validation fixture expectations.
"""

import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
VALIDATOR = ROOT / "scripts/validate-extraction.py"


CASES = [
    ("examples/good-static", 0),
    ("examples/good-motion", 0),
    ("examples/bad-missing-evidence", 1),
    ("examples/bad-placeholder-specimen", 1),
]


def run_case(relpath, expected):
    command = [sys.executable, str(VALIDATOR), "--strict", str(ROOT / relpath)]
    completed = subprocess.run(command, cwd=ROOT, text=True, capture_output=True)
    output = completed.stdout + completed.stderr
    if completed.returncode != expected:
        print(f"[error] {relpath}: expected exit {expected}, got {completed.returncode}")
        print(output)
        return False
    if expected != 0 and "[error]" not in output:
        print(f"[error] {relpath}: expected at least one [error] finding")
        print(output)
        return False
    print(f"[ok] {relpath}: exit {completed.returncode}")
    return True


def main():
    ok = True
    for relpath, expected in CASES:
        ok = run_case(relpath, expected) and ok
    raise SystemExit(0 if ok else 1)


if __name__ == "__main__":
    main()
