# Setup & run the demo

This guide gets the Point-in-Time Infrastructure Graph demo running
end-to-end on your machine. Budget ~10 minutes.

If you just want the elevator pitch and the worked example first, read
[README.md](README.md) and [workspace/use_case.md](workspace/use_case.md).

---

## 1. Prerequisites

- **Neo4j 5.x or 6.x** — Neo4j Desktop, a local Docker container, or
  Aura. You need one empty database dedicated to this demo (default name:
  `timeslice`).
- **Python 3.10+**.
- A **modern browser**. The demo uses ES modules served from `unpkg` /
  `esm.sh`, so it needs internet access on first load.

There is no build step and no Node.js requirement. The web UI is a single
static HTML page that talks to Neo4j directly via the JS driver.

---

## 2. Clone + Python environment

```bash
git clone <repo-url> neo4j-pov-toolkit
cd neo4j-pov-toolkit
git checkout point-in-time-temporal-graph

python -m venv .venv
source .venv/bin/activate           # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

The only dependencies are the `neo4j` driver and `python-dotenv` (plus a
few transitive). If you prefer `uv`, `uv run python ...` works against
the same `.venv` — see the command examples in §5.

---

## 3. Create a Neo4j database for the demo

The demo expects a dedicated database named **`timeslice`**. The name is
hardcoded in the web UI (see §7 if you need to override it).

### Option A — Neo4j Desktop

Create a local DBMS, start it, open Neo4j Browser, and on the system DB:

```cypher
CREATE DATABASE timeslice;
```

### Option B — Docker

```bash
docker run -d --name neo4j-pov \
  -p 7474:7474 -p 7687:7687 \
  -e NEO4J_AUTH=neo4j/your-password \
  neo4j:5
```

Then in Neo4j Browser at <http://localhost:7474> (on the system DB):

```cypher
CREATE DATABASE timeslice;
```

### Option C — Aura

Create a new instance. Aura's default database is `neo4j` and you can't
create additional ones on the free tier — in that case, leave
`NEO4J_DATABASE=neo4j` in `.env` and change `CONFIG.database` in
`workspace/web/app.js` to `"neo4j"` (see §7).

---

## 4. Configure `.env`

```bash
cp .env.example .env
```

Edit `.env` with your connection details:

```
NEO4J_URI=neo4j://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your-password-here
NEO4J_DATABASE=timeslice
```

These values are read by the Python test harness. The web UI has its own
config block (see §7) and defaults to the same values.

---

## 5. Sanity-check with the test suite

The scenario scripts wipe the database, apply the schema, run ingests,
and assert the snapshot query returns the correct graph at every
boundary. Passing tests mean the model is correctly installed.

```bash
python workspace/tests/run_all.py
```

You should see `All 3 scenario scripts passed.` at the end.

Running individual scenarios is useful when debugging:

```bash
python workspace/tests/scenario_worked_example.py
python workspace/tests/scenario_csv.py
python workspace/tests/scenario_corner_cases.py
```

Each scenario starts from a clean database, so running them out of order
is fine.

---

## 6. Launch the web UI

The demo is a single static HTML page. Serve the **project root** over
HTTP so the relative paths to `workspace/` and `neo4j-branding/` resolve:

```bash
# from the project root
python -m http.server 8000
```

Open <http://localhost:8000/workspace/web/index.html>.

On first load the page prompts for your Neo4j password (stashed in
`sessionStorage` so closing the tab forgets it). The header badge should
flip to **connected**.

### What to try

1. Click **Mon → Tue → Wed** in order. Each click ingests that day's scan
   and the graph grows.
2. Click **Thu**. Server `B` vanishes — Thursday's scan didn't see it, so
   its lifespan closes.
3. Drag the time slider back to **Wed 09:00**. `B` is back, relationships
   restored.
4. Drag to **Mon 14:00**. Only `A` is visible — no other scan had
   happened by then.
5. Click **Fri**, drag to **Fri 09:00**. `B` is visible again. In Neo4j
   Browser, inspect `MATCH (s:Server {id:'B'})-[:HAS_STATE]->(st) RETURN
   st` — you'll see **two** `ServerState` nodes, representing `B`'s two
   distinct lives.

Expand **Show the query being fired** to see the exact `snapshot.cypher`
that runs on every slider move.

The **Reset database** button wipes the `timeslice` DB and re-applies the
schema, so you can replay the week from scratch.

---

## 7. Overriding URI / user / database for the web UI

The web UI's config lives at the top of `workspace/web/app.js`:

```js
const CONFIG = {
  uri: "neo4j://localhost:7687",
  user: "neo4j",
  database: "timeslice",
  ...
};
```

Change these if your Neo4j lives elsewhere, uses a different user, or
(e.g. Aura) requires the default `neo4j` database. The browser doesn't
read `.env`, so this file is the source of truth for the UI.

---

## Troubleshooting

- **`connection failed` in the header.** Check `NEO4J_URI` and that the
  DB is running. For Docker, confirm port `7687` is mapped. For Aura,
  the URI starts with `neo4j+s://`.
- **`database does not exist`.** Either run `CREATE DATABASE timeslice;`
  on the system DB, or change `CONFIG.database` in `workspace/web/app.js`
  (and `NEO4J_DATABASE` in `.env`) to match an existing database.
- **Blank canvas / no updates after clicking a day button.** Open the
  browser console — CSV load, ingest, and snapshot calls all log with
  the `[timeslice]` prefix.
- **Wrong password stuck in the browser.** Open DevTools → Application →
  Session Storage and delete `timeslice.password`, then reload.

---

## What's next

Once the demo runs, read
[workspace/use_case.md](workspace/use_case.md) for the full rationale —
why both `ServerState` and `CONNECTED_TO` carry validity, why we close
at run time rather than last-seen time, why v1 is deliberately this
small, and how the same model extends to lineage, warehouse, and service
topology without structural change.
