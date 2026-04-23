# Point-in-Time Infrastructure Graph

> *"What did your infrastructure look like at 09:00 on Tuesday last week?"*

A Neo4j demo that answers regulator-style questions like this one by
versioning both the existence of servers *and* the connections between
them across a week of discovery scans. It backs a **DORA** (Digital
Operational Resilience Act) conversation with a bank: reconstruct the
operational estate at any instant — which servers existed, how they were
connected, what was online, what was offline, what had been retired — and
watch it change as the week unfolds.

This branch contains **v1**: the smallest possible model that proves the
core temporal primitive works end-to-end, on a trivially small dataset,
with a live NVL visualization.

---

## What you'll see

Five daily scans, Mon–Fri at 09:00 UTC:

| Day | Scan sees | Graph outcome |
|---|---|---|
| Mon | `A` | `A` born |
| Tue | `A`, `B`, `A→B` | `B` born; `A→B` born |
| Wed | `A`, `B`, `C`, `A→B`, `B→C` | `C` born; `B→C` born |
| Thu | `A`, `C` | `B`'s lifespan closes; `A→B` and `B→C` close |
| Fri | `A`, `B`, `C`, `A→B`, `B→C` | `B` reappears — a **new** `ServerState` on the same `Server` |

A single-page NVL UI lets you click through the week and drag a
time-slider to any instant — the graph re-renders as it would have looked
at exactly that moment. Offline servers aren't greyed out, they're simply
absent, because the point is that the snapshot query *returns* the estate
at that instant.

---

## Why this matters for the bank

Once the primitive works for `Server` + `CONNECTED_TO`, the same model
scales without structural change to:

- Data lineage (`Pipeline → Table → Column`)
- Warehouse topology (`Database → Schema → Table`)
- Application topology (`Service → API → Dependency`)
- Datacenter / network topology

v2+ is therefore **more labels and more relationship types** — not a new
temporal model. That's the pitch.

---

## The model in one picture

```
(:Server {id, name, first_observed_at})
   -[:HAS_STATE]->
(:ServerState {valid_from, valid_to, last_seen_alive})

(:Server)-[:CONNECTED_TO {valid_from, valid_to, last_seen_alive}]->(:Server)
```

Stable identity lives on `Server`. Temporal validity lives on
`ServerState` *and* on `CONNECTED_TO`. A server that disappeared Thursday
and came back Friday has two `ServerState` nodes attached to the same
`Server` — same identity, two distinct lives. The same applies to parallel
`CONNECTED_TO` relationships between the same pair of endpoints.

See [workspace/use_case.md](workspace/use_case.md) for the full rationale
— including why both nodes and relationships carry validity (scans emit
two independent signals), why we close at run time and not last-seen time,
and what was deliberately left out of v1.

---

## Running the demo

See **[SETUP.md](SETUP.md)** for the full walkthrough. In short:

```bash
# 1. Install deps and configure Neo4j credentials
cp .env.example .env          # fill in NEO4J_URI / USER / PASSWORD / DATABASE
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# 2. Sanity-check the model against every scenario
python workspace/tests/run_all.py

# 3. Launch the NVL visualization (from the project root)
python -m http.server 8000
# then open http://localhost:8000/workspace/web/index.html
```

---

## Project layout

```
.
├── README.md                          ← this file
├── SETUP.md                           ← step-by-step setup
├── .env.example                       ← Neo4j connection template
├── requirements.txt
├── workspace/
│   ├── use_case.md                    ← full v1 spec
│   ├── cypher/
│   │   ├── setup.cypher               ← constraints + indexes
│   │   ├── ingest_template.cypher     ← one file, called once per scan
│   │   └── snapshot.cypher            ← one file, called on every slider move
│   ├── data/
│   │   ├── scans_servers.csv          ← (run_time, id, name)
│   │   └── scans_relationships.csv    ← (run_time, from_id, to_id)
│   ├── tests/                         ← scenario harness + corner cases
│   └── web/                           ← NVL single-page demo
└── neo4j-branding/                    ← fonts / logos / CSS used by the demo
```

Three Cypher files. Two CSVs. Twenty rows of data. That's the whole
thing — deliberately small, so a customer can look at the input and
understand the entire week at a glance.

---

## Where to read more

- **[workspace/use_case.md](workspace/use_case.md)** — the full spec:
  problem statement, model rationale, ingest rules, snapshot query, demo
  narrative, alternatives considered, explicit non-goals.
- **[workspace/cypher/](workspace/cypher/)** — all the Cypher.
- **[workspace/tests/](workspace/tests/)** — scenario scripts exercising
  the worked example, CSV equivalence, and corner cases (flapping,
  link-only drops, self-loops, retirement, threshold policies,
  idempotency).
