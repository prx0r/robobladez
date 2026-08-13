from pathlib import Path
import json
from .model import MatchResult
from .engine import canonical_json

def save_match(match:MatchResult,path):
    Path(path).write_text(json.dumps(match.to_dict(),indent=2,allow_nan=False),encoding="utf-8")

def save_canonical(match:MatchResult,path):
    Path(path).write_text(canonical_json(match.to_dict()),encoding="utf-8")
