"""Corner-case pack for the time-slice model.

Each case is an isolated scenario — we wipe and re-setup the DB before
running. Asserts a handful of snapshots per case.

Covered cases:
  1. Query before any data has been ingested      -> empty snapshot
  2. Query far in the future (after latest scan)  -> latest known state
  3. Multi-flap (B off/on/off/on)                 -> multiple ServerStates
  4. Relationship drops while endpoints stay up   -> nodes visible, rel gone
  5. Self-loop relationship (A -> A)              -> supported and queryable
  6. Disjoint subgraphs in same run               -> both render at snapshot
  7. Server permanently retired mid-week          -> not shown after close
  8. Standalone server across multiple scans      -> always visible, no rels
  9. Configurable offline threshold (PT24H)       -> 1 miss does NOT close
 10. Ingest idempotency (re-run same scan)        -> no duplicate states/rels
 11. last_seen_alive preserved across close       -> closed state keeps last real sighting
 12. Bidirectional relationships (A->B and B->A)  -> independent lifespans
 13. valid_from inclusive lower bound             -> µs-before / at / µs-after
 14. Out-of-order ingest with stable observations -> no duplicate states/rels
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from harness import (
    Observation,
    assert_snapshot,
    database_name,
    ingest,
    load_driver,
    reset,
    snapshot,
    utc,
)


def run_case(driver, label: str, fn) -> None:
    print(f"\n=== {label} ===")
    reset(driver)
    fn(driver)


def case_before_any_data(driver) -> None:
    # No data ingested yet. Any $at should return an empty snapshot.
    assert_snapshot(snapshot(driver, utc("2026-04-20T09:00:00Z")), set(), set(), "empty DB at any $at")
    assert_snapshot(snapshot(driver, utc("2020-01-01T00:00:00Z")), set(), set(), "empty DB far in the past")


def case_after_latest(driver) -> None:
    ingest(driver, Observation(
        run_time=utc("2026-04-20T09:00:00Z"),
        servers=[{"id": "A", "name": "server-a"}, {"id": "B", "name": "server-b"}],
        relationships=[{"from_id": "A", "to_id": "B"}],
    ))
    # Far future: the open states/relationships still satisfy valid_to IS NULL,
    # so they appear. This is the "current known state" semantic, consistent
    # with the slider's right-hand end.
    assert_snapshot(
        snapshot(driver, utc("2099-01-01T00:00:00Z")),
        {"A", "B"}, {("A", "B")},
        "far future returns latest known (open) state",
    )


def case_multi_flap(driver) -> None:
    # B flaps: on, off, on, off, on across five daily scans.
    A = {"id": "A", "name": "server-a"}
    B = {"id": "B", "name": "server-b"}
    ingest(driver, Observation(utc("2026-04-20T09:00:00Z"), [A, B], [{"from_id": "A", "to_id": "B"}]))
    ingest(driver, Observation(utc("2026-04-21T09:00:00Z"), [A],    []))
    ingest(driver, Observation(utc("2026-04-22T09:00:00Z"), [A, B], [{"from_id": "A", "to_id": "B"}]))
    ingest(driver, Observation(utc("2026-04-23T09:00:00Z"), [A],    []))
    ingest(driver, Observation(utc("2026-04-24T09:00:00Z"), [A, B], [{"from_id": "A", "to_id": "B"}]))

    assert_snapshot(snapshot(driver, utc("2026-04-20T09:00:00Z")), {"A", "B"}, {("A", "B")}, "day 1 — B alive")
    assert_snapshot(snapshot(driver, utc("2026-04-21T09:00:00Z")), {"A"},       set(),        "day 2 — B offline")
    assert_snapshot(snapshot(driver, utc("2026-04-22T09:00:00Z")), {"A", "B"}, {("A", "B")}, "day 3 — B back")
    assert_snapshot(snapshot(driver, utc("2026-04-23T09:00:00Z")), {"A"},       set(),        "day 4 — B offline again")
    assert_snapshot(snapshot(driver, utc("2026-04-24T09:00:00Z")), {"A", "B"}, {("A", "B")}, "day 5 — B back again")

    # Verify graph structure: three distinct ServerState intervals on B.
    with driver.session(database=database_name()) as s:
        rec = s.run(
            """
            MATCH (srv:Server {id: 'B'})-[:HAS_STATE]->(st:ServerState)
            RETURN count(st) AS total, sum(CASE WHEN st.valid_to IS NULL THEN 1 ELSE 0 END) AS open_count
            """
        ).single()
        assert rec["total"] == 3, f"expected 3 ServerStates on B, got {rec['total']}"
        assert rec["open_count"] == 1, f"expected exactly 1 open ServerState, got {rec['open_count']}"
    print("  PASS [structural: B has 3 ServerStates, 1 open]")

    # And three CONNECTED_TO relationships between A and B.
    with driver.session(database=database_name()) as s:
        rec = s.run(
            """
            MATCH (:Server {id: 'A'})-[c:CONNECTED_TO]->(:Server {id: 'B'})
            RETURN count(c) AS total, sum(CASE WHEN c.valid_to IS NULL THEN 1 ELSE 0 END) AS open_count
            """
        ).single()
        assert rec["total"] == 3, f"expected 3 CONNECTED_TO relationships, got {rec['total']}"
        assert rec["open_count"] == 1, f"expected exactly 1 open relationship, got {rec['open_count']}"
    print("  PASS [structural: A->B has 3 relationships, 1 open]")


def case_relationship_drops_endpoints_stay(driver) -> None:
    # A and B are observed every day, but the A->B relationship is dropped on Wed.
    A = {"id": "A", "name": "server-a"}
    B = {"id": "B", "name": "server-b"}
    AB = {"from_id": "A", "to_id": "B"}
    ingest(driver, Observation(utc("2026-04-20T09:00:00Z"), [A, B], [AB]))
    ingest(driver, Observation(utc("2026-04-21T09:00:00Z"), [A, B], [AB]))
    ingest(driver, Observation(utc("2026-04-22T09:00:00Z"), [A, B], []))  # link flap
    ingest(driver, Observation(utc("2026-04-23T09:00:00Z"), [A, B], [AB]))

    assert_snapshot(snapshot(driver, utc("2026-04-20T09:00:00Z")), {"A", "B"}, {("A", "B")}, "Mon — linked")
    assert_snapshot(snapshot(driver, utc("2026-04-22T09:00:00Z")), {"A", "B"}, set(),        "Wed — endpoints up, link down")
    assert_snapshot(snapshot(driver, utc("2026-04-23T09:00:00Z")), {"A", "B"}, {("A", "B")}, "Thu — link restored")


def case_self_loop(driver) -> None:
    A = {"id": "A", "name": "server-a"}
    ingest(driver, Observation(utc("2026-04-20T09:00:00Z"), [A], [{"from_id": "A", "to_id": "A"}]))
    assert_snapshot(snapshot(driver, utc("2026-04-20T09:00:00Z")), {"A"}, {("A", "A")}, "self-loop relationship visible")


def case_disjoint_subgraphs(driver) -> None:
    # Two unrelated clusters observed simultaneously. Snapshot returns both.
    A = {"id": "A", "name": "server-a"}
    B = {"id": "B", "name": "server-b"}
    X = {"id": "X", "name": "server-x"}
    Y = {"id": "Y", "name": "server-y"}
    ingest(driver, Observation(
        utc("2026-04-20T09:00:00Z"),
        [A, B, X, Y],
        [{"from_id": "A", "to_id": "B"}, {"from_id": "X", "to_id": "Y"}],
    ))
    assert_snapshot(
        snapshot(driver, utc("2026-04-20T09:00:00Z")),
        {"A", "B", "X", "Y"}, {("A", "B"), ("X", "Y")},
        "two disjoint clusters render together",
    )


def case_retired_mid_week(driver) -> None:
    # B appears Mon/Tue, then never again. Forever offline from Wed onward.
    A = {"id": "A", "name": "server-a"}
    B = {"id": "B", "name": "server-b"}
    ingest(driver, Observation(utc("2026-04-20T09:00:00Z"), [A, B], [{"from_id": "A", "to_id": "B"}]))
    ingest(driver, Observation(utc("2026-04-21T09:00:00Z"), [A, B], [{"from_id": "A", "to_id": "B"}]))
    ingest(driver, Observation(utc("2026-04-22T09:00:00Z"), [A],    []))
    ingest(driver, Observation(utc("2026-04-23T09:00:00Z"), [A],    []))

    assert_snapshot(snapshot(driver, utc("2026-04-21T09:00:00Z")), {"A", "B"}, {("A", "B")}, "Tue — B alive")
    assert_snapshot(snapshot(driver, utc("2026-04-22T09:00:00Z")), {"A"},       set(),        "Wed — B retired")
    assert_snapshot(snapshot(driver, utc("2099-01-01T00:00:00Z")), {"A"},       set(),        "far future — B still retired")


def case_standalone_server(driver) -> None:
    # A is seen every day with no relationships. Must always render.
    A = {"id": "A", "name": "server-a"}
    for day in (20, 21, 22):
        ingest(driver, Observation(utc(f"2026-04-{day:02d}T09:00:00Z"), [A], []))
    for day in (20, 21, 22):
        assert_snapshot(
            snapshot(driver, utc(f"2026-04-{day:02d}T09:00:00Z")),
            {"A"}, set(), f"day {day} — standalone A visible",
        )


def case_offline_threshold_pt24h(driver) -> None:
    # With a 24h threshold, a single missed daily scan does NOT close the state
    # (run_time - last_seen_alive == 24h, not strictly greater; our predicate
    # is `>= threshold` so it DOES close at exactly 24h). Let's use PT25H so
    # one miss leaves state open.
    A = {"id": "A", "name": "server-a"}
    B = {"id": "B", "name": "server-b"}

    # Mon 09:00 — see both.
    ingest(driver, Observation(
        utc("2026-04-20T09:00:00Z"), [A, B], [{"from_id": "A", "to_id": "B"}],
        offline_threshold_iso="PT25H",
    ))
    # Tue 09:00 — miss B. Gap is 24h, less than 25h threshold; B STAYS open.
    ingest(driver, Observation(
        utc("2026-04-21T09:00:00Z"), [A], [],
        offline_threshold_iso="PT25H",
    ))
    assert_snapshot(
        snapshot(driver, utc("2026-04-21T09:00:00Z")),
        {"A", "B"}, {("A", "B")},
        "PT25H threshold: one-miss does not close B",
    )
    # Wed 09:00 — still no B. Gap is 48h, above threshold; B closes now.
    ingest(driver, Observation(
        utc("2026-04-22T09:00:00Z"), [A], [],
        offline_threshold_iso="PT25H",
    ))
    assert_snapshot(
        snapshot(driver, utc("2026-04-22T09:00:00Z")),
        {"A"}, set(),
        "PT25H threshold: two consecutive misses closes B",
    )


def case_idempotent_ingest(driver) -> None:
    # Re-running the same run should not produce duplicate states or relationships.
    A = {"id": "A", "name": "server-a"}
    B = {"id": "B", "name": "server-b"}
    obs = Observation(utc("2026-04-20T09:00:00Z"), [A, B], [{"from_id": "A", "to_id": "B"}])
    ingest(driver, obs)
    ingest(driver, obs)  # run again
    ingest(driver, obs)  # and again

    with driver.session(database=database_name()) as s:
        rec = s.run(
            """
            MATCH (srv:Server)-[:HAS_STATE]->(st:ServerState)
            RETURN count(srv) AS servers, count(st) AS states
            """
        ).single()
        assert rec["servers"] == 2, f"expected 2 Servers, got {rec['servers']}"
        assert rec["states"] == 2, f"expected 2 ServerStates (one per server), got {rec['states']}"
        rec2 = s.run("MATCH ()-[c:CONNECTED_TO]->() RETURN count(c) AS n").single()
        assert rec2["n"] == 1, f"expected 1 CONNECTED_TO relationship, got {rec2['n']}"
    print("  PASS [idempotent: re-ingesting same scan does not duplicate states/relationships]")

    # Snapshot should still be correct.
    assert_snapshot(
        snapshot(driver, utc("2026-04-20T09:00:00Z")),
        {"A", "B"}, {("A", "B")},
        "snapshot unchanged after repeated ingest",
    )


def case_last_seen_alive_preserved(driver) -> None:
    # B: seen Mon & Tue, missed Wed (closes), returns Thu (new state).
    # The closed state must retain last_seen_alive = Tue (last real sighting),
    # NOT Wed (the close timestamp). The new open state starts fresh.
    A = {"id": "A", "name": "server-a"}
    B = {"id": "B", "name": "server-b"}
    AB = {"from_id": "A", "to_id": "B"}
    MON = utc("2026-04-20T09:00:00Z")
    TUE = utc("2026-04-21T09:00:00Z")
    WED = utc("2026-04-22T09:00:00Z")
    THU = utc("2026-04-23T09:00:00Z")
    ingest(driver, Observation(MON, [A, B], [AB]))
    ingest(driver, Observation(TUE, [A, B], [AB]))
    ingest(driver, Observation(WED, [A],    []))   # B missed -> closes
    ingest(driver, Observation(THU, [A, B], [AB])) # B returns -> new state

    with driver.session(database=database_name()) as s:
        rows = s.run(
            """
            MATCH (:Server {id: 'B'})-[:HAS_STATE]->(st:ServerState)
            RETURN st.valid_from AS vf, st.valid_to AS vt, st.last_seen_alive AS lsa
            ORDER BY st.valid_from
            """
        ).data()

    assert len(rows) == 2, f"expected 2 ServerStates on B, got {len(rows)}"
    closed, reopened = rows[0], rows[1]

    assert closed["vf"].to_native() == MON, f"closed vf: got {closed['vf']}"
    assert closed["vt"].to_native() == WED, f"closed vt: got {closed['vt']}"
    assert closed["lsa"].to_native() == TUE, (
        f"closed last_seen_alive should be Tue (last real sighting), got {closed['lsa']}"
    )
    print("  PASS [closed state: last_seen_alive preserved at last real sighting]")

    assert reopened["vf"].to_native() == THU
    assert reopened["vt"] is None
    assert reopened["lsa"].to_native() == THU
    print("  PASS [new state: last_seen_alive fresh on re-open]")

    # Same rule for the A->B relationship.
    with driver.session(database=database_name()) as s:
        rel_rows = s.run(
            """
            MATCH (:Server {id: 'A'})-[c:CONNECTED_TO]->(:Server {id: 'B'})
            RETURN c.valid_from AS vf, c.valid_to AS vt, c.last_seen_alive AS lsa
            ORDER BY c.valid_from
            """
        ).data()
    assert len(rel_rows) == 2, f"expected 2 relationships, got {len(rel_rows)}"
    assert rel_rows[0]["lsa"].to_native() == TUE, (
        f"closed relationship last_seen_alive should be Tue, got {rel_rows[0]['lsa']}"
    )
    assert rel_rows[1]["lsa"].to_native() == THU
    print("  PASS [relationship: last_seen_alive preserved on close, fresh on re-open]")


def case_bidirectional_relationships(driver) -> None:
    # A->B and B->A are distinct relationships. Their lifespans are independent.
    A = {"id": "A", "name": "server-a"}
    B = {"id": "B", "name": "server-b"}
    MON = utc("2026-04-20T09:00:00Z")
    TUE = utc("2026-04-21T09:00:00Z")

    ingest(driver, Observation(
        MON, [A, B],
        [{"from_id": "A", "to_id": "B"}, {"from_id": "B", "to_id": "A"}],
    ))
    assert_snapshot(
        snapshot(driver, MON),
        {"A", "B"}, {("A", "B"), ("B", "A")},
        "Mon: both A->B and B->A visible",
    )

    with driver.session(database=database_name()) as s:
        n_rels = s.run("MATCH ()-[c:CONNECTED_TO]->() RETURN count(c) AS n").single()["n"]
    assert n_rels == 2, f"expected 2 CONNECTED_TO relationships, got {n_rels}"
    print("  PASS [structural: 2 independent CONNECTED_TO relationships]")

    # Drop A->B on Tue; B->A remains observed.
    ingest(driver, Observation(TUE, [A, B], [{"from_id": "B", "to_id": "A"}]))
    assert_snapshot(
        snapshot(driver, TUE),
        {"A", "B"}, {("B", "A")},
        "Tue: A->B closed, B->A still open",
    )
    # Historical Mon view must be unchanged.
    assert_snapshot(
        snapshot(driver, MON),
        {"A", "B"}, {("A", "B"), ("B", "A")},
        "Mon historical: both directions still visible",
    )


def case_valid_from_inclusive_lower_bound(driver) -> None:
    # Mirror of the worked-example's upper-bound check: µs-before, exactly-at,
    # µs-after valid_from. The predicate is `valid_from <= $at` (inclusive).
    A = {"id": "A", "name": "server-a"}
    RUN = utc("2026-04-20T09:00:00Z")
    ingest(driver, Observation(RUN, [A], []))

    assert_snapshot(
        snapshot(driver, utc("2026-04-20T08:59:59.999999Z")),
        set(), set(),
        "1µs before valid_from: A not yet visible",
    )
    assert_snapshot(
        snapshot(driver, RUN),
        {"A"}, set(),
        "exactly at valid_from: A visible (inclusive lower bound)",
    )
    assert_snapshot(
        snapshot(driver, utc("2026-04-20T09:00:00.000001Z")),
        {"A"}, set(),
        "1µs after valid_from: A visible",
    )


def case_out_of_order_ingest(driver) -> None:
    # use_case.md names in-order ingest as an invariant. This case exercises
    # the common "delayed scan arrives late" failure mode for that invariant:
    # observations are stable across the period (no opens, no closes), so
    # order shouldn't matter for point-in-time answers.
    A = {"id": "A", "name": "server-a"}
    B = {"id": "B", "name": "server-b"}
    AB = {"from_id": "A", "to_id": "B"}
    MON = utc("2026-04-20T09:00:00Z")
    TUE = utc("2026-04-21T09:00:00Z")
    WED = utc("2026-04-22T09:00:00Z")

    # Ingest order: Mon, Wed, then Tue arriving late.
    ingest(driver, Observation(MON, [A, B], [AB]))
    ingest(driver, Observation(WED, [A, B], [AB]))
    ingest(driver, Observation(TUE, [A, B], [AB]))

    assert_snapshot(snapshot(driver, MON), {"A", "B"}, {("A", "B")}, "Mon: A,B; A->B")
    assert_snapshot(snapshot(driver, TUE), {"A", "B"}, {("A", "B")}, "Tue: A,B; A->B (late-arriving scan)")
    assert_snapshot(snapshot(driver, WED), {"A", "B"}, {("A", "B")}, "Wed: A,B; A->B")

    # One ServerState per server, one relationship — no duplication from the late scan.
    with driver.session(database=database_name()) as s:
        states = s.run("MATCH (:Server)-[:HAS_STATE]->(st) RETURN count(st) AS n").single()["n"]
        rels = s.run("MATCH ()-[c:CONNECTED_TO]->() RETURN count(c) AS n").single()["n"]
    assert states == 2, f"expected 2 ServerStates, got {states}"
    assert rels == 1, f"expected 1 CONNECTED_TO relationship, got {rels}"
    print("  PASS [out-of-order but stable observations: no duplicate states/relationships]")


def main() -> int:
    driver = load_driver()
    try:
        cases = [
            ("1. before any data",                         case_before_any_data),
            ("2. after latest scan",                       case_after_latest),
            ("3. multi-flap (B off/on/off/on)",            case_multi_flap),
            ("4. relationship drops while endpoints stay", case_relationship_drops_endpoints_stay),
            ("5. self-loop relationship",                  case_self_loop),
            ("6. disjoint subgraphs",                      case_disjoint_subgraphs),
            ("7. server retired mid-week",                 case_retired_mid_week),
            ("8. standalone server",                       case_standalone_server),
            ("9. offline threshold = PT25H",               case_offline_threshold_pt24h),
            ("10. idempotent ingest",                      case_idempotent_ingest),
            ("11. last_seen_alive preserved",              case_last_seen_alive_preserved),
            ("12. bidirectional relationships",            case_bidirectional_relationships),
            ("13. valid_from inclusive bound",             case_valid_from_inclusive_lower_bound),
            ("14. out-of-order ingest (stable)",           case_out_of_order_ingest),
        ]
        for label, fn in cases:
            run_case(driver, label, fn)
        print(f"\nAll {len(cases)} corner-case scenarios passed.")
        return 0
    finally:
        driver.close()


if __name__ == "__main__":
    sys.exit(main())
