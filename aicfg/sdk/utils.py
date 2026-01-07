import toml
import hashlib
from pathlib import Path
from datetime import datetime
from typing import Optional

def load_toml(path: Path) -> dict:
    if not path.exists():
        return {}
    with open(path, "r") as f:
        return toml.load(f)

def save_toml(path: Path, data: dict):
    with open(path, "w") as f:
        toml.dump(data, f)

def get_file_info(path: Path) -> dict:
    """Return presence, md5 hash, and modified time for a file."""
    if not path.exists():
        return {"exists": False, "hash": None, "mtime": None}
    
    with open(path, "rb") as f:
        content = f.read()
        md5 = hashlib.md5(content).hexdigest()
    
    mtime = datetime.fromtimestamp(path.stat().st_mtime).isoformat()
    
    return {
        "exists": True,
        "hash": md5,
        "mtime": mtime
    }