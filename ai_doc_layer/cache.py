# cache.py
import json
import hashlib
from pathlib import Path
from typing import Optional

CACHE_PATH = Path(".ai_doc_cache.json")

def _hash(prompt: str, extra: Optional[dict] = None):
    s = prompt + (json.dumps(extra, sort_keys=True) if extra else "")
    return hashlib.sha256(s.encode()).hexdigest()

def load_from_cache(prompt: str, extra=None) -> Optional[str]:
    if not CACHE_PATH.exists():
        return None
    data = json.loads(CACHE_PATH.read_text("utf-8"))
    return data.get(_hash(prompt, extra), None)

def save_to_cache(prompt: str, response: str, extra=None):
    if CACHE_PATH.exists():
        data = json.loads(CACHE_PATH.read_text("utf-8"))
    else:
        data = {}

    data[_hash(prompt, extra)] = response
    CACHE_PATH.write_text(json.dumps(data, indent=2), encoding="utf-8")
