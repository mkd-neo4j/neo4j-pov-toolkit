"""Runs every scenario script in sequence and exits non-zero on any failure."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path


HERE = Path(__file__).resolve().parent
SCENARIOS = [
    "scenario_worked_example.py",
    "scenario_csv.py",
    "scenario_corner_cases.py",
]


def main() -> int:
    failures: list[str] = []
    for name in SCENARIOS:
        print(f"\n{'#' * 70}\n# {name}\n{'#' * 70}")
        result = subprocess.run(
            [sys.executable, str(HERE / name)],
            capture_output=True,
            text=True,
        )
        # Drop noisy driver notification lines from stdout/stderr.
        for line in result.stdout.splitlines():
            if "Notification" in line or line.startswith("Received"):
                continue
            print(line)
        if result.returncode != 0:
            failures.append(name)
            print(f"--- stderr from {name} ---")
            print(result.stderr)

    print(f"\n{'=' * 70}")
    if failures:
        print(f"FAILED: {', '.join(failures)}")
        return 1
    print(f"All {len(SCENARIOS)} scenario scripts passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
