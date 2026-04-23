"""The canonical Mon-Fri worked example from the use-case doc.

Mon   sees {A}                         -> A alive.
Tue   sees {A,B} and A->B              -> B joins, A->B opens.
Wed   sees {A,B,C} and A->B, B->C      -> C joins, B->C opens.
Thu   sees {A,C}                       -> B goes offline, A->B and B->C close.
Fri   sees {A,B,C} and A->B, B->C      -> B returns with NEW state, new relationships.

Each day's snapshot is asserted against the expected visible set. Then we
probe between-scan instants to verify the interval semantics.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from harness import (
    Observation,
    assert_snapshot,
    ingest,
    load_driver,
    reset,
    snapshot,
    utc,
)


def main() -> int:
    driver = load_driver()
    try:
        reset(driver)

        MON = utc("2026-04-20T09:00:00Z")
        TUE = utc("2026-04-21T09:00:00Z")
        WED = utc("2026-04-22T09:00:00Z")
        THU = utc("2026-04-23T09:00:00Z")
        FRI = utc("2026-04-24T09:00:00Z")

        print("Ingesting Mon-Fri...")
        ingest(driver, Observation(
            run_time=MON,
            servers=[{"id": "A", "name": "server-a"}],
            relationships=[],
        ))
        ingest(driver, Observation(
            run_time=TUE,
            servers=[{"id": "A", "name": "server-a"}, {"id": "B", "name": "server-b"}],
            relationships=[{"from_id": "A", "to_id": "B"}],
        ))
        ingest(driver, Observation(
            run_time=WED,
            servers=[
                {"id": "A", "name": "server-a"},
                {"id": "B", "name": "server-b"},
                {"id": "C", "name": "server-c"},
            ],
            relationships=[{"from_id": "A", "to_id": "B"}, {"from_id": "B", "to_id": "C"}],
        ))
        ingest(driver, Observation(
            run_time=THU,
            servers=[{"id": "A", "name": "server-a"}, {"id": "C", "name": "server-c"}],
            relationships=[],
        ))
        ingest(driver, Observation(
            run_time=FRI,
            servers=[
                {"id": "A", "name": "server-a"},
                {"id": "B", "name": "server-b"},
                {"id": "C", "name": "server-c"},
            ],
            relationships=[{"from_id": "A", "to_id": "B"}, {"from_id": "B", "to_id": "C"}],
        ))

        print("\nSnapshots at each scan time:")
        assert_snapshot(snapshot(driver, MON), {"A"}, set(), "Mon 09:00 = {A}")
        assert_snapshot(snapshot(driver, TUE), {"A", "B"}, {("A", "B")}, "Tue 09:00 = {A,B; A->B}")
        assert_snapshot(
            snapshot(driver, WED),
            {"A", "B", "C"},
            {("A", "B"), ("B", "C")},
            "Wed 09:00 = {A,B,C; A->B, B->C}",
        )
        assert_snapshot(snapshot(driver, THU), {"A", "C"}, set(), "Thu 09:00 = {A,C} (B offline, relationships closed)")
        assert_snapshot(
            snapshot(driver, FRI),
            {"A", "B", "C"},
            {("A", "B"), ("B", "C")},
            "Fri 09:00 = {A,B,C; A->B, B->C} (B returned)",
        )

        print("\nSlider probes between scans:")
        assert_snapshot(snapshot(driver, utc("2026-04-20T14:00:00Z")), {"A"}, set(), "Mon 14:00 = {A}")
        assert_snapshot(snapshot(driver, utc("2026-04-21T03:00:00Z")), {"A"}, set(), "Tue 03:00 (pre-Tue scan) = {A}")
        assert_snapshot(
            snapshot(driver, utc("2026-04-22T20:00:00Z")),
            {"A", "B", "C"},
            {("A", "B"), ("B", "C")},
            "Wed 20:00 (post-Wed scan, pre-Thu) = all three",
        )
        assert_snapshot(
            snapshot(driver, utc("2026-04-23T10:00:00Z")),
            {"A", "C"},
            set(),
            "Thu 10:00 (1h after B goes offline) = {A,C}",
        )
        assert_snapshot(
            snapshot(driver, utc("2026-04-23T23:59:59Z")),
            {"A", "C"},
            set(),
            "Thu 23:59:59 (still in B-offline window) = {A,C}",
        )
        assert_snapshot(
            snapshot(driver, utc("2026-04-24T08:59:59Z")),
            {"A", "C"},
            set(),
            "Fri 08:59:59 (one second before Fri scan) = {A,C}",
        )

        print("\nBoundary semantics — valid_from inclusive, valid_to exclusive:")
        # Thu 09:00 is the exact close moment for B's first state. The query
        # uses `valid_to > $at`, so at $at == valid_to, the old state is NOT
        # included — which is the honest reading: "by 09:00 we knew B was
        # gone." The snapshot therefore does not show B at Thu 09:00.
        assert_snapshot(snapshot(driver, THU), {"A", "C"}, set(), "Thu 09:00 exactly: B excluded (valid_to exclusive)")
        # One microsecond before Thu 09:00, B is still considered online.
        assert_snapshot(
            snapshot(driver, utc("2026-04-23T08:59:59.999999Z")),
            {"A", "B", "C"},
            {("A", "B"), ("B", "C")},
            "Thu 08:59:59.999999: B's first state still open",
        )

        print("\nAll worked-example assertions passed.")
        return 0
    finally:
        driver.close()


if __name__ == "__main__":
    sys.exit(main())
