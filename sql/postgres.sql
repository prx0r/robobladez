CREATE TABLE agents(
 id TEXT PRIMARY KEY,
 genesis_seed TEXT NOT NULL,
 created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE TABLE agent_versions(
 agent_id TEXT NOT NULL REFERENCES agents(id),
 version INTEGER NOT NULL,
 body JSONB NOT NULL,
 policy_manifest JSONB NOT NULL,
 phenotype JSONB,
 daimon_projection JSONB,
 parent_version INTEGER,
 created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
 PRIMARY KEY(agent_id,version)
);
CREATE TABLE matches(
 match_id TEXT PRIMARY KEY,
 engine_version TEXT NOT NULL,
 seed BIGINT NOT NULL,
 arena JSONB NOT NULL,
 blades JSONB NOT NULL,
 policy_manifests JSONB NOT NULL,
 policy_commitments JSONB NOT NULL,
 wins JSONB NOT NULL,
 winner TEXT,
 replay_digest TEXT NOT NULL UNIQUE,
 replay JSONB NOT NULL,
 created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX matches_winner_idx ON matches(winner);
