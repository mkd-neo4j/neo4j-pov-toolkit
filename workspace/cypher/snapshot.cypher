// ---------------------------------------------------------------------------
// Time-slice infrastructure graph -- point-in-time snapshot query
//
// Parameters:
//   $at :: datetime -- the instant to reconstruct the estate for
//
// Returns:
//   nodes :: list of Server nodes online at $at
//   rels  :: list of CONNECTED_TO relationships valid at $at
//            (only between nodes that are themselves online at $at)
//
// Validity predicate (applied to ServerState and CONNECTED_TO):
//   valid_from <= $at AND (valid_to IS NULL OR valid_to > $at)
//
// A server is "online at $at" iff it has a HAS_STATE relationship to a
// currently-valid ServerState. "Both endpoints online" is therefore a
// traversal, not a list-membership test -- so the whole query is one pattern.
// ---------------------------------------------------------------------------

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
