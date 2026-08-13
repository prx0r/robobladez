import json,sqlite3
from pathlib import Path
from .model import MatchResult
from .engine import verify_replay_digest

SCHEMA="""
PRAGMA journal_mode=WAL;
CREATE TABLE IF NOT EXISTS matches(
 match_id TEXT PRIMARY KEY,
 engine_version TEXT NOT NULL,
 seed INTEGER NOT NULL,
 winner TEXT,
 replay_digest TEXT NOT NULL UNIQUE,
 payload_json TEXT NOT NULL,
 created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS agent_versions(
 agent_id TEXT NOT NULL,
 version INTEGER NOT NULL,
 snapshot_json TEXT NOT NULL,
 created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
 PRIMARY KEY(agent_id,version)
);
"""

class CanonStore:
    def __init__(self,path:str|Path):
        self.db=sqlite3.connect(str(path))
        self.db.executescript(SCHEMA); self.db.commit()
    def save_match(self,m:MatchResult):
        if not verify_replay_digest(m):
            raise ValueError("refusing to persist match with invalid replay digest")
        self.db.execute(
            "INSERT OR IGNORE INTO matches(match_id,engine_version,seed,winner,replay_digest,payload_json) VALUES(?,?,?,?,?,?)",
            (m.match_id,m.engine_version,m.seed,m.winner,m.replay_digest,json.dumps(m.to_dict(),allow_nan=False)))
        self.db.commit()
    def count(self):
        return self.db.execute("SELECT COUNT(*) FROM matches").fetchone()[0]

    def save_agent_version(self, agent_id: str, version: int, snapshot: dict) -> None:
        self.db.execute(
            "INSERT OR REPLACE INTO agent_versions(agent_id,version,snapshot_json) VALUES(?,?,?)",
            (agent_id, version, json.dumps(snapshot, default=str)))
        self.db.commit()

    def agent_version_count(self, agent_id: str) -> int:
        return self.db.execute(
            "SELECT COUNT(*) FROM agent_versions WHERE agent_id=?", (agent_id,)
        ).fetchone()[0]
