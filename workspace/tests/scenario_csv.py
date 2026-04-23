"""Worked example, but driven from the two scan CSVs.

If this test produces the same snapshots as scenario_worked_example.py, the
CSV-driven pipeline is equivalent to the inline one and we know the CSV
loader/ingest loop is correct.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from harness import (
    assert_snapshot,
    ingest_all,
    load_driver,
    load_observations_from_csv,
    reset,
    snapshot,
    utc,
)


def main() -> int:
    driver = load_driver()
    try:
        reset(driver)
        observations = load_observations_from_csv()
        print(f"Loaded {len(observations)} scan runs from CSVs:")
        for o in observations:
            print(
                f"  {o.run_time.isoformat()} — "
                f"{len(o.servers)} server(s), {len(o.relationships)} relationship(s)"
            )
        ingest_all(driver, observations)

        print("\nAsserting snapshots at each scan time:")
        assert_snapshot(snapshot(driver, utc("2026-04-20T09:00:00Z")), {"A"}, set(), "Mon 09:00")
        assert_snapshot(snapshot(driver, utc("2026-04-21T09:00:00Z")), {"A", "B"}, {("A", "B")}, "Tue 09:00")
        assert_snapshot(
            snapshot(driver, utc("2026-04-22T09:00:00Z")),
            {"A", "B", "C"}, {("A", "B"), ("B", "C")}, "Wed 09:00",
        )
        assert_snapshot(snapshot(driver, utc("2026-04-23T09:00:00Z")), {"A", "C"}, set(), "Thu 09:00 (B offline)")
        assert_snapshot(
            snapshot(driver, utc("2026-04-24T09:00:00Z")),
            {"A", "B", "C"}, {("A", "B"), ("B", "C")}, "Fri 09:00 (B returned)",
        )

        print("\nCSV-driven pipeline produced the expected snapshots.")
        return 0
    finally:
        driver.close()


if __name__ == "__main__":
    sys.exit(main())
