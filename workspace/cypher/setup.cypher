// ---------------------------------------------------------------------------
// Time-slice infrastructure graph — schema setup
//
// Idempotent. Safe to run on an existing DB.
// ---------------------------------------------------------------------------

// One canonical identity per physical server.
CREATE CONSTRAINT server_id_unique IF NOT EXISTS
FOR (s:Server) REQUIRE s.id IS UNIQUE;

// ServerState has no natural key — we rely on graph structure. But we do
// want fast filtering by validity boundaries.
CREATE INDEX server_state_valid_from IF NOT EXISTS
FOR (st:ServerState) ON (st.valid_from);

CREATE INDEX server_state_valid_to IF NOT EXISTS
FOR (st:ServerState) ON (st.valid_to);

// Relationship property indexes for the snapshot query's relationship filter.
CREATE INDEX connected_to_valid_from IF NOT EXISTS
FOR ()-[c:CONNECTED_TO]-() ON (c.valid_from);

CREATE INDEX connected_to_valid_to IF NOT EXISTS
FOR ()-[c:CONNECTED_TO]-() ON (c.valid_to);
