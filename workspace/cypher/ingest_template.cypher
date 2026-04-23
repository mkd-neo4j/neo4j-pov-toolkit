// ---------------------------------------------------------------------------
// Time-slice infrastructure graph — ingest template
//
// One canonical per-run ingest. Called once per scan, parameterised by the
// observations CSV for that run.
//
// Parameters:
//   $run_time          :: datetime  -- when this scan ran
//   $servers           :: list of {id, name}
//   $relationships     :: list of {from_id, to_id}
//   $offline_threshold :: string ISO-8601 duration (e.g. 'PT0S', 'PT24H')
//                         PT0S means "close on first miss"
//
// Invariants preserved:
//   - Each Server has at most one open ServerState at any time.
//   - Each (a,b) Server pair has at most one open CONNECTED_TO relationship.
//   - Ingest must be called in chronological order of $run_time.
// ---------------------------------------------------------------------------

// Step 1 -- Upsert server identity. Stable node per physical server.
CALL () {
  UNWIND $servers AS observed
  MERGE (s:Server {id: observed.id})
    ON CREATE SET s.name = observed.name, s.first_observed_at = $run_time
  RETURN count(*) AS upserted
}

// Step 2 -- For each observed server, extend its open state
// (bump last_seen_alive) or open a new one if none is open.
CALL () {
  UNWIND $servers AS observed
  MATCH (s:Server {id: observed.id})
  OPTIONAL MATCH (s)-[:HAS_STATE]->(st:ServerState) WHERE st.valid_to IS NULL
  FOREACH (_ IN CASE WHEN st IS NULL THEN [1] ELSE [] END |
    CREATE (s)-[:HAS_STATE]->(:ServerState {
      valid_from: $run_time, valid_to: null, last_seen_alive: $run_time
    })
  )
  FOREACH (existing IN CASE WHEN st IS NOT NULL THEN [st] ELSE [] END |
    SET existing.last_seen_alive = $run_time
  )
  RETURN count(*) AS states_touched
}

// Step 3 -- For each observed relationship, extend the open one between
// the pair or create a new CONNECTED_TO.
CALL () {
  UNWIND $relationships AS observed_rel
  MATCH (a:Server {id: observed_rel.from_id})
  MATCH (b:Server {id: observed_rel.to_id})
  OPTIONAL MATCH (a)-[c:CONNECTED_TO]->(b) WHERE c.valid_to IS NULL
  FOREACH (_ IN CASE WHEN c IS NULL THEN [1] ELSE [] END |
    CREATE (a)-[:CONNECTED_TO {
      valid_from: $run_time, valid_to: null, last_seen_alive: $run_time
    }]->(b)
  )
  FOREACH (existing IN CASE WHEN c IS NOT NULL THEN [c] ELSE [] END |
    SET existing.last_seen_alive = $run_time
  )
  RETURN count(*) AS rels_touched
}

// Step 4 -- Close any open ServerState whose server was not observed in
// this run, once it has been absent for >= offline_threshold.
CALL () {
  WITH [x IN $servers | x.id] AS observed_ids
  MATCH (s:Server)-[:HAS_STATE]->(st:ServerState)
  WHERE st.valid_to IS NULL
    AND NOT s.id IN observed_ids
    AND $run_time >= st.last_seen_alive + duration($offline_threshold)
  SET st.valid_to = $run_time
  RETURN count(*) AS states_closed
}

// Step 5 -- Close any open CONNECTED_TO relationship not observed in this
// run, subject to the same threshold rule.
CALL () {
  MATCH (a:Server)-[c:CONNECTED_TO]->(b:Server)
  WHERE c.valid_to IS NULL
    AND NONE(r IN $relationships WHERE r.from_id = a.id AND r.to_id = b.id)
    AND $run_time >= c.last_seen_alive + duration($offline_threshold)
  SET c.valid_to = $run_time
  RETURN count(*) AS rels_closed
}

RETURN upserted, states_touched, rels_touched, states_closed, rels_closed;
