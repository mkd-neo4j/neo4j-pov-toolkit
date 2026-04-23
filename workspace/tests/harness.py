"""Time-slice graph test harness.

Connects to the timeslice DB via the neo4j driver, wipes, sets up schema,
and exposes helpers for running scenarios and asserting snapshot results.

Used by the scenario scripts in this directory. Run them directly with:
    uv run python workspace/tests/<scenario>.py
"""
from __future__ import annotations

import csv
import os
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv
from neo4j import GraphDatabase, Driver


PROJECT_ROOT = Path(__file__).resolve().parents[2]
CYPHER_DIR = PROJECT_ROOT / "workspace" / "cypher"
DATA_DIR = PROJECT_ROOT / "workspace" / "data"


@dataclass(frozen=True)
class Observation:
    run_time: datetime
    servers: list[dict]
    relationships: list[dict]
    offline_threshold_iso: str = "PT0S"


@dataclass(frozen=True)
class Snapshot:
    server_ids: frozenset[str]
    relationships: frozenset[tuple[str, str]]

    def pretty(self) -> str:
        nodes = ", ".join(sorted(self.server_ids)) or "(none)"
        rels = ", ".join(f"{a}->{b}" for a, b in sorted(self.relationships)) or "(none)"
        return f"nodes=[{nodes}] rels=[{rels}]"


def load_driver() -> Driver:
    load_dotenv(PROJECT_ROOT / ".env")
    uri = os.environ["NEO4J_URI"]
    user = os.environ["NEO4J_USER"]
    password = os.environ["NEO4J_PASSWORD"]
    return GraphDatabase.driver(uri, auth=(user, password))


def database_name() -> str:
    return os.environ.get("NEO4J_DATABASE", "neo4j")


def read_cypher(name: str) -> str:
    path = CYPHER_DIR / name
    return path.read_text()


def wipe(driver: Driver) -> None:
    with driver.session(database=database_name()) as s:
        s.run("MATCH (n) DETACH DELETE n").consume()


def drop_schema(driver: Driver) -> None:
    """Drop all constraints and indexes so setup is deterministic."""
    with driver.session(database=database_name()) as s:
        for row in list(s.run("SHOW CONSTRAINTS YIELD name")):
            s.run(f"DROP CONSTRAINT {row['name']} IF EXISTS").consume()
        for row in list(s.run("SHOW INDEXES YIELD name, type WHERE type <> 'LOOKUP'")):
            s.run(f"DROP INDEX {row['name']} IF EXISTS").consume()


def setup_schema(driver: Driver) -> None:
    cypher = read_cypher("setup.cypher")
    with driver.session(database=database_name()) as s:
        for stmt in split_statements(cypher):
            s.run(stmt).consume()


def split_statements(cypher: str) -> list[str]:
    """Split on semicolons outside strings, // line comments, and /* block comments */."""
    out: list[str] = []
    buf: list[str] = []
    i, n = 0, len(cypher)
    in_str: str | None = None
    in_line_c = False
    in_block_c = False
    while i < n:
        ch = cypher[i]
        nxt = cypher[i + 1] if i + 1 < n else ""
        if in_line_c:
            buf.append(ch)
            if ch == "\n":
                in_line_c = False
            i += 1
            continue
        if in_block_c:
            buf.append(ch)
            if ch == "*" and nxt == "/":
                buf.append(nxt)
                i += 2
                in_block_c = False
                continue
            i += 1
            continue
        if in_str:
            buf.append(ch)
            if ch == in_str:
                in_str = None
            i += 1
            continue
        if ch == "/" and nxt == "/":
            in_line_c = True
            buf.append(ch); buf.append(nxt)
            i += 2
            continue
        if ch == "/" and nxt == "*":
            in_block_c = True
            buf.append(ch); buf.append(nxt)
            i += 2
            continue
        if ch in ("'", '"'):
            in_str = ch
            buf.append(ch)
            i += 1
            continue
        if ch == ";":
            stmt = "".join(buf).strip()
            if stmt:
                out.append(stmt)
            buf = []
            i += 1
            continue
        buf.append(ch)
        i += 1
    tail = "".join(buf).strip()
    if tail:
        out.append(tail)
    # Filter out chunks that are purely comments/whitespace after stripping.
    return [s for s in out if _has_cypher(s)]


def _has_cypher(stmt: str) -> bool:
    """True if the statement contains at least one non-comment, non-whitespace char."""
    i, n = 0, len(stmt)
    in_line_c = False
    in_block_c = False
    while i < n:
        ch = stmt[i]
        nxt = stmt[i + 1] if i + 1 < n else ""
        if in_line_c:
            if ch == "\n":
                in_line_c = False
            i += 1
            continue
        if in_block_c:
            if ch == "*" and nxt == "/":
                i += 2
                in_block_c = False
                continue
            i += 1
            continue
        if ch == "/" and nxt == "/":
            in_line_c = True
            i += 2
            continue
        if ch == "/" and nxt == "*":
            in_block_c = True
            i += 2
            continue
        if not ch.isspace():
            return True
        i += 1
    return False


INGEST_TEMPLATE = None


def ingest(driver: Driver, obs: Observation) -> dict:
    global INGEST_TEMPLATE
    if INGEST_TEMPLATE is None:
        INGEST_TEMPLATE = read_cypher("ingest_template.cypher")
    # The template file ends with a trailing semicolon; driver is fine with that.
    with driver.session(database=database_name()) as s:
        rec = s.run(
            INGEST_TEMPLATE,
            run_time=obs.run_time,
            servers=obs.servers,
            relationships=obs.relationships,
            offline_threshold=obs.offline_threshold_iso,
        ).single()
        return dict(rec) if rec else {}


def snapshot(driver: Driver, at: datetime) -> Snapshot:
    cypher = read_cypher("snapshot.cypher")
    with driver.session(database=database_name()) as s:
        rec = s.run(cypher, at=at).single()
        nodes = rec["nodes"] or []
        rels = rec["rels"] or []
        server_ids = frozenset(n["id"] for n in nodes)
        relationships = frozenset((r["from_id"], r["to_id"]) for r in rels)
        return Snapshot(server_ids=server_ids, relationships=relationships)


def utc(iso: str) -> datetime:
    # Convenience: parse '2026-04-20T09:00:00Z'-style strings into aware UTC datetimes.
    if iso.endswith("Z"):
        iso = iso[:-1] + "+00:00"
    dt = datetime.fromisoformat(iso)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


def assert_snapshot(actual: Snapshot, expected_nodes: set[str], expected_rels: set[tuple[str, str]], label: str) -> None:
    exp = Snapshot(frozenset(expected_nodes), frozenset(expected_rels))
    if actual != exp:
        raise AssertionError(
            f"FAIL [{label}]\n  actual:   {actual.pretty()}\n  expected: {exp.pretty()}"
        )
    print(f"  PASS [{label}] {actual.pretty()}")


def reset(driver: Driver) -> None:
    wipe(driver)
    drop_schema(driver)
    setup_schema(driver)


def load_observations_from_csv(
    servers_csv: Path | None = None,
    relationships_csv: Path | None = None,
    offline_threshold_iso: str = "PT0S",
) -> list[Observation]:
    """Read the two scan CSVs and return Observations grouped by run_time, chronological."""
    servers_csv = servers_csv or DATA_DIR / "scans_servers.csv"
    relationships_csv = relationships_csv or DATA_DIR / "scans_relationships.csv"

    servers_by_run: dict[datetime, list[dict]] = defaultdict(list)
    with open(servers_csv) as f:
        for row in csv.DictReader(f):
            rt = utc(row["run_time"])
            servers_by_run[rt].append({"id": row["id"], "name": row["name"]})

    rels_by_run: dict[datetime, list[dict]] = defaultdict(list)
    with open(relationships_csv) as f:
        for row in csv.DictReader(f):
            rt = utc(row["run_time"])
            rels_by_run[rt].append({"from_id": row["from_id"], "to_id": row["to_id"]})

    all_runs = sorted(set(servers_by_run) | set(rels_by_run))
    observations: list[Observation] = []
    for rt in all_runs:
        servers = servers_by_run.get(rt, [])
        relationships = rels_by_run.get(rt, [])
        # Cheap sanity check: every relationship endpoint must also appear in this run's servers.
        server_ids = {s["id"] for s in servers}
        for r in relationships:
            if r["from_id"] not in server_ids or r["to_id"] not in server_ids:
                raise ValueError(
                    f"Run {rt.isoformat()}: relationship {r['from_id']}->{r['to_id']} has "
                    f"endpoint missing from servers list (observed servers: {sorted(server_ids)})"
                )
        observations.append(Observation(
            run_time=rt, servers=servers, relationships=relationships,
            offline_threshold_iso=offline_threshold_iso,
        ))
    return observations


def ingest_all(driver: Driver, observations: list[Observation]) -> list[dict]:
    return [ingest(driver, o) for o in observations]
