# Use Case: Point-in-Time Infrastructure Graph (Banking, DORA)

## Business context

A bank needs to answer a deceptively simple regulator question:

> "What did your infrastructure look like at 09:00 on Tuesday last week?"

Under **DORA** (Digital Operational Resilience Act), the bank must be able to
reconstruct — at any point in time — the state of its operational estate:
which servers existed, how they were connected, what was online, what was
offline, and what had been retired. The long-term vision is a **digital twin
of the bank** that extends the same primitives to data lineage, warehouse
tables, data centres, and applications.

This document specifies **v1**: the smallest possible model that proves the
core temporal primitive works end-to-end, on a trivially small dataset, with
a visual demo that a regulator or exec can understand in thirty seconds.

Once v1 is solid, the same model scales out to lineage and the rest of the
estate without structural change.

## The core problem

The bank discovers its estate via **periodic scans**. Each scan only reports
what it *can see* (known knowns). The graph must capture three signals from
each scan:

1. **New entities** (first-ever observation → start a new lifespan).
2. **Continued presence** (seen again → extend the current lifespan).
3. **Absence** (previously seen, not seen this run → close the current
   lifespan; this entity is now "offline").

And then, crucially, entities can **come back**. A server that went offline
Thursday and reappears Friday must be recognised as the *same* server, but
with a clear history showing it had two distinct "lives" in between.

## Scope (v1 — deliberately minimal)

- **One node label**: `Server`.
- **One relationship type**: `CONNECTED_TO` (directional: A talks to B).
- **Five daily scans** at 09:00 on five consecutive weekdays:
  - Monday    `2026-04-20 09:00`
  - Tuesday   `2026-04-21 09:00`
  - Wednesday `2026-04-22 09:00`
  - Thursday  `2026-04-23 09:00`
  - Friday    `2026-04-24 09:00`
- **Timezone**: UTC for all timestamps in v1. We can add zones later.
- **Hand-crafted Cypher per day** (no CSV). One ingest file per scan so the
  demo narrative is obvious from the file list.

## The worked example

| Day | Scan sees | Graph outcome |
|---|---|---|
| Mon | `A` | `A` born. |
| Tue | `A`, `B`, `A→B` | `B` born. `A→B` relationship born. `A`'s lifespan extended. |
| Wed | `A`, `B`, `C`, `A→B`, `B→C` | `C` born. `B→C` relationship born. All extended. |
| Thu | `A`, `C` (B is offline) | `B`'s current lifespan closes at Thu 09:00. Relationships `A→B` and `B→C` close at Thu 09:00. `A` and `C` extended. Note: `A` and `C` are no longer transitively reachable. |
| Fri | `A`, `B`, `C`, `A→B`, `B→C` | `B` reappears — a **new** `ServerState` is attached to the same `Server` node. Two **new** `CONNECTED_TO` relationships are created (the Thursday ones stay closed). |

This is the full dataset for v1. Five runs. That's it.

## Data model

### Why two places for validity?

The model versions **both** node existence (`ServerState`) and
relationship existence (`CONNECTED_TO`). At first glance this looks like
duplication — surely if a relationship is closed, its endpoint being
offline is implied? It isn't, and the reason is important enough to spell
out before the schema.

Each scan emits **two independent signals**:

1. *"I saw server X."*
2. *"I saw a relationship X→Y."*

Signal 2 implies signal 1 for both endpoints — you can't observe a
relationship without observing its ends. But the reverse doesn't hold. A
scan can see a server and no relationships. And the two signals can go
*absent* independently: a server can be up while every one of its links is
down (network partition, firewall flap, service on one side crashed) —
genuinely different from the server itself being offline.

Because the scan emits two independent streams of facts, the graph needs
two independent places to version them.

Three concrete cases where relying on relationships alone breaks down:

- **Standalone servers.** Monday's scan sees `A` with no relationships.
  Without `ServerState`, there is nowhere to record "A existed at 09:00
  Monday," and Monday's snapshot query returns an empty graph. The demo
  dies on slide one.
- **Network partition vs. host down.** If both of B's relationships close
  because a switch failed, B itself might still be up. With only
  relationship-validity, "B offline" and "B isolated but healthy" are
  indistinguishable. With `ServerState`, the next scan that sees B (even
  with no relationships) proves it was up the whole time.
- **Scans with separate probes.** Real discovery tools often report hosts
  and flows from different probes. The two signal streams arrive
  independently, sometimes at different cadences; the graph has to
  represent both faithfully.

Put simply: `ServerState` versions **node existence**. `CONNECTED_TO`
versions **relationship existence**. They are not duplicates — they are
the same temporal mechanism applied to two different kinds of fact, which
is exactly what we want, because it means every part of the graph speaks
the same temporal language.

### Recommended approach

```
(:Server {id, name, first_observed_at})
   -[:HAS_STATE]->
(:ServerState {valid_from, valid_to, last_seen_alive})

(:Server)-[:CONNECTED_TO {valid_from, valid_to, last_seen_alive}]->(:Server)
```

**Stable identity is on `Server`.** Name, id, and the first-ever sighting
are immutable once set.

**Temporal validity lives on `ServerState`.** Each lifespan is its own node.
A server that went offline and came back has two `ServerState` nodes
attached to the same `Server`. When the model grows (IP address, datacenter,
OS version, etc.), those time-varying attributes live on `ServerState`, not
on `Server`.

**Parallel relationships between the same pair.** Neo4j allows multiple
`CONNECTED_TO` relationships between the same pair of servers. Each
lifespan of the link is its own relationship, stamped with its own
`valid_from` / `valid_to`. If A↔B drops Thursday and comes back Friday,
Thursday's relationship stays as a closed historical record and Friday
creates a new one.

### Validity interval semantics

- `valid_from`: timestamp of the scan run that first observed this lifespan.
- `valid_to`: `null` while the lifespan is open; set to the timestamp of
  the run that confirmed absence when closed. **We close at run time, not at
  last-seen time**, so the graph is honest about when we *knew* something
  was gone, not when it might have gone.
- `last_seen_alive`: timestamp of the most recent scan that confirmed the
  entity alive. Preserved across close so "last known good" is queryable
  independently of `valid_to`.
- A point-in-time query at `$at` includes a lifespan iff
  `valid_from <= $at AND (valid_to IS NULL OR valid_to > $at)`.

### Alternatives considered (and why not)

- **Intervals as an array property on `Server`**: simpler at a glance but
  clumsy to update ("set the open interval's valid_to") and awkward to
  filter in Cypher. Rejected.
- **Reify the relationship** (`(:Server)-[:IN]->(:Connection)-[:OUT]->(:Server)`):
  needed for complex relationship attributes later, but for v1 it adds
  three nodes per link per lifespan. Parallel relationships are cheaper
  and work identically for the snapshot query. Rejected for v1; revisit
  if relationships grow attributes.
- **Full event-sourcing** (one `:Observation` node per scan per entity):
  gives a perfect audit log but quadruples node count and complicates the
  snapshot query. Rejected for v1; the chosen model can still reconstruct
  any run's exact output from the intervals.

## Observations on disk: two CSVs

The scans themselves are expressed as two CSVs — deliberately the simplest
possible representation, so a customer can look at the input and understand
the entire week in twenty rows. In a real deployment these would be dumped
by whatever discovery tool the bank runs.

`workspace/data/scans_servers.csv` — one row per (scan, observed server):

```
run_time,id,name
2026-04-20T09:00:00Z,A,server-a
2026-04-21T09:00:00Z,A,server-a
2026-04-21T09:00:00Z,B,server-b
...
```

`workspace/data/scans_relationships.csv` — one row per (scan, observed relationship):

```
run_time,from_id,to_id
2026-04-21T09:00:00Z,A,B
2026-04-22T09:00:00Z,A,B
2026-04-22T09:00:00Z,B,C
...
```

That's the full source of truth for the five days. The ingest pipeline
reads both files, groups by `run_time` in chronological order, and calls a
single piece of Cypher once per scan.

## Ingest rules (one Cypher template, five invocations)

There is **one** ingest Cypher file: `workspace/cypher/ingest_template.cypher`.
It is called once per scan with parameters derived from the CSVs:

| parameter            | type            | description                                       |
|----------------------|-----------------|---------------------------------------------------|
| `$run_time`          | `datetime`      | when this scan ran                                |
| `$servers`           | list of maps    | `[{id, name}, ...]` — servers observed this run   |
| `$relationships`     | list of maps    | `[{from_id, to_id}, ...]` — relationships observed |
| `$offline_threshold` | ISO-8601 string | e.g. `"PT0S"` = close on first miss               |

Each invocation performs five steps inside a single query:

1. **Upsert identity**: `MERGE (s:Server {id: ...})` — set
   `first_observed_at = $run_time` on create only.
2. **Open or extend node state**: if the server has no open `ServerState`,
   create one with `valid_from = $run_time`; if it has an open state,
   bump `last_seen_alive = $run_time`.
3. **Open or extend relationships**: same logic for `CONNECTED_TO` — if no
   open relationship exists between the pair, create one; otherwise bump
   `last_seen_alive`.
4. **Close absent node states**: for every currently-open `ServerState`
   whose server was *not* in `$servers`, and where
   `$run_time - last_seen_alive >= $offline_threshold`, set
   `valid_to = $run_time`.
5. **Close absent relationships**: same rule for `CONNECTED_TO`.

With `$offline_threshold = duration("PT0S")` this is the "1 miss = offline"
rule used in v1. Customer-specific policies ("offline after 3 missed runs"
/ "offline after 6h") change the parameter value, not the model.

## The one query that matters

A single file, `workspace/cypher/snapshot.cypher`, takes a parameter `$at`
(a `datetime`) and returns the graph as it existed at that instant:

```cypher
MATCH (a:Server)-[:HAS_STATE]->(sa:ServerState)
WHERE sa.valid_from <= $at
  AND (sa.valid_to IS NULL OR sa.valid_to > $at)
OPTIONAL MATCH (a)-[c:CONNECTED_TO]->(b:Server)-[:HAS_STATE]->(sb:ServerState)
WHERE c.valid_from  <= $at AND (c.valid_to  IS NULL OR c.valid_to  > $at)
  AND sb.valid_from <= $at AND (sb.valid_to IS NULL OR sb.valid_to > $at)
WITH
  collect(DISTINCT {
    id: a.id, name: a.name, first_observed_at: a.first_observed_at
  }) AS nodes,
  collect(DISTINCT CASE WHEN c IS NOT NULL THEN {
    from_id: a.id, to_id: b.id,
    valid_from: c.valid_from, valid_to: c.valid_to,
    last_seen_alive: c.last_seen_alive
  } END) AS rels_nullable
RETURN nodes, [r IN rels_nullable WHERE r IS NOT NULL] AS rels;
```

The NVL UI calls this query on every slider movement and re-renders.

## Demo (the visible thing)

A single static HTML page using **NVL** (Neo4j Visualization Library),
served locally. No Streamlit, no backend. The page talks to Neo4j directly
via the JS driver using credentials from `.env`-sourced config.

**Layout:**

- **Top bar — five day buttons**: `Monday`, `Tuesday`, `Wednesday`,
  `Thursday`, `Friday`. Clicking a button reads that day's rows from the
  CSVs and invokes `ingest_template.cypher` once with the resulting
  `$servers` / `$relationships` / `$run_time` parameters. Buttons disable once
  clicked (or indicate "already run").
- **Time slider**: range is `[earliest valid_from in graph, latest valid_from in graph]`.
  Grows as days get ingested. Default position: latest. Tick marks at
  09:00 each weekday so the regulator moments are obvious.
- **Graph canvas**: NVL renders the snapshot returned by `snapshot.cypher`
  for the slider's current `$at`. Offline nodes and relationships are
  simply absent — not greyed out — because the point is that the snapshot
  query *returns* the estate at that instant.
- **Timestamp label**: shows the exact `datetime` the slider is on.

**Interactions that illustrate the primitive:**

- Click through Mon → Tue → Wed, slider at "now", watch the graph grow.
- Click Thu, slider stays at now → B vanishes from the canvas.
- Slide back to Wed 09:00 → B is back, relationships restored.
- Slide to Mon 14:00 → only A, because no other scan had observed anything
  by that instant.
- Click Fri, slide to Fri 09:00 → B is back again, but inspecting the
  underlying data shows two distinct `ServerState` nodes on the same
  `Server`.

## Deliverables

```
workspace/
  use_case.md                      (this file)
  data/
    scans_servers.csv              (run_time, id, name)
    scans_relationships.csv        (run_time, from_id, to_id)
    README.md
  cypher/
    setup.cypher                   (constraints, indexes)
    ingest_template.cypher         (parameterised by $run_time/$servers/$relationships/$offline_threshold)
    snapshot.cypher                (parameterised by $at)
  tests/
    harness.py                     (driver wiring, CSV loader, assertion helpers)
    scenario_worked_example.py     (inline Mon-Fri + boundary probes)
    scenario_csv.py                (same scenario, driven from CSVs — proves equivalence)
    scenario_corner_cases.py       (flapping, link drop, self-loop, retirement, threshold, idempotency, ...)
    run_all.py                     (one-shot runner over every scenario file)
  web/                             (v1-UI phase, not yet built)
    index.html                     (NVL + day buttons + slider)
    app.js                         (driver, query wiring, render)
    styles.css
```

Run everything from the project root:

```
uv run python workspace/tests/run_all.py
```

## Out of scope for v1 (explicit non-goals)

- Multiple node labels or relationship types.
- Sub-daily scan cadence.
- Configurable offline threshold beyond "1 miss = offline" (the parameter
  is in the model; no UI for it).
- Authentication / authorisation / audit log on the ingest actions.
- Handling entities that permanently retire (closed but never reopened is
  fine; no "retired" flag needed — the absence of future lifespans is
  sufficient signal).
- Timezones other than UTC.

## What this v1 proves (and why the bank cares)

If v1 renders the right graph for any slider position across the five-day
window — including the Thursday gap and the Friday return — then the same
model, ingest rules, and snapshot query work unchanged for:

- Data lineage graphs (Pipeline → Table → Column with validity intervals).
- Warehouse topology (Database → Schema → Table).
- Application topology (Service → API → Dependency).
- Datacenter/network topology.

The v2+ work is therefore **more labels, more relationship types, more
scans** — not a new temporal model. That's the pitch.
