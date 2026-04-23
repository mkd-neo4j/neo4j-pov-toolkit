# Scan observations

Two CSVs describe everything each scan saw across the demo week. The
ingest pipeline reads them, groups by `run_time`, and calls the ingest
template once per scan in chronological order.

This is deliberately the simplest possible representation — a real
discovery tool would dump something like this directly. The whole
"time-travel graph" story happens downstream of these two files.

## `scans_servers.csv`

One row per (scan, observed server).

| column   | meaning                                 |
|----------|-----------------------------------------|
| run_time | ISO-8601 UTC timestamp of the scan run  |
| id       | stable server identifier (primary key)  |
| name     | human-readable name                     |

## `scans_relationships.csv`

One row per (scan, observed directional relationship).

| column   | meaning                                 |
|----------|-----------------------------------------|
| run_time | ISO-8601 UTC timestamp of the scan run  |
| from_id  | source server id                        |
| to_id    | target server id                        |

## The demo week at a glance

- **Mon 09:00** — A alone.
- **Tue 09:00** — A and B; A→B.
- **Wed 09:00** — A, B, C; A→B and B→C.
- **Thu 09:00** — A and C (B is offline; scans report only what they see).
- **Fri 09:00** — A, B, C; A→B and B→C (B back, with a *new* lifespan).
