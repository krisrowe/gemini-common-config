import json
import yaml
import subprocess
import os
from pathlib import Path
from typing import Any, List, Optional, Union

# Paths
USER_SETTINGS_PATH = Path.home() / ".gemini" / "settings.json"
MAP_PATH = Path(__file__).parent / "settings_map.yaml"

def get_git_root() -> Optional[Path]:
    try:
        root = subprocess.check_output(
            ["git", "rev-parse", "--show-toplevel"], 
            stderr=subprocess.DEVNULL
        ).decode().strip()
        return Path(root)
    except subprocess.CalledProcessError:
        return None

def get_project_settings_path() -> Path:
    root = get_git_root()
    if root:
        return root / ".gemini" / "settings.json"
    # Fallback to CWD if not in git repo (e.g. testing in temp dir)
    return Path.cwd() / ".gemini" / "settings.json"

def get_active_config_path() -> Path:
    """
    Resolve configuration file.
    Priority: Local Project (if exists) > Global User
    """
    project_path = get_project_settings_path()
    if project_path.exists():
        return project_path
    return USER_SETTINGS_PATH

# PROJECT_SETTINGS_PATH kept for backward compatibility in imports, 
# but get_active_config_path now recalculates.
PROJECT_SETTINGS_PATH = get_project_settings_path()

def load_json(path: Path) -> dict:
    if not path or not path.exists():
        return {}
    try:
        with open(path, "r") as f:
            return json.load(f)
    except Exception:
        return {}

def save_json(path: Path, data: dict):
    if not path:
        raise ValueError("Invalid config path")
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        json.dump(data, f, indent=2)

def load_map() -> dict:
    if not MAP_PATH.exists():
        return {}
    with open(MAP_PATH, "r") as f:
        return yaml.safe_load(f) or {}

def get_by_path(data: dict, dot_path: str) -> Any:
    parts = dot_path.split(".")
    curr = data
    for part in parts:
        if isinstance(curr, dict) and part in curr:
            curr = curr[part]
        else:
            return None
    return curr

def set_by_path(data: dict, dot_path: str, value: Any):
    parts = dot_path.split(".")
    curr = data
    for part in parts[:-1]:
        if part not in curr or not isinstance(curr[part], dict):
            curr[part] = {}
        curr = curr[part]
    curr[parts[-1]] = value

# --- SDK API ---

def get_include_directories() -> tuple[Path, List[str]]:
    """Return (config_path, list_of_paths)."""
    path = get_active_config_path()
    data = load_json(path)
    return path, data.get("context", {}).get("includeDirectories", [])

def add_include_directory(path_to_add: str, scope: Optional[str] = None) -> Path:
    """Add path to config. Returns modified config path."""
    if scope == "project":
        path = get_project_settings_path()
    elif scope == "user":
        path = USER_SETTINGS_PATH
    else:
        path = get_active_config_path()
        
    data = load_json(path)
    if "context" not in data: data["context"] = {}
    if "includeDirectories" not in data["context"]: data["context"]["includeDirectories"] = []
    
    if path_to_add not in data["context"]["includeDirectories"]:
        data["context"]["includeDirectories"].append(path_to_add)
        save_json(path, data)
    return path

def remove_include_directory(path_to_remove: str) -> tuple[Path, bool]:
    """Remove path. Returns (config_path, was_removed)."""
    path = get_active_config_path()
    data = load_json(path)
    dirs = data.get("context", {}).get("includeDirectories", [])
    if path_to_remove in dirs:
        dirs.remove(path_to_remove)
        save_json(path, data)
        return path, True
    return path, False

def get_context_files() -> tuple[Path, List[str]]:
    path = get_active_config_path()
    data = load_json(path)
    val = data.get("context", {}).get("fileName", [])
    return path, [val] if isinstance(val, str) else val

def add_context_file(filename: str) -> Path:
    path = get_active_config_path()
    data = load_json(path)
    if "context" not in data: data["context"] = {}
    val = data["context"].get("fileName", [])
    files = [val] if isinstance(val, str) else val
    
    if filename not in files:
        files.append(filename)
        data["context"]["fileName"] = files if len(files) > 1 else files[0]
        save_json(path, data)
    return path

def remove_context_file(filename: str) -> tuple[Path, bool]:
    path = get_active_config_path()
    data = load_json(path)
    val = data.get("context", {}).get("fileName", [])
    files = [val] if isinstance(val, str) else val
    
    if filename in files:
        files.remove(filename)
        if not files:
            del data["context"]["fileName"]
        else:
            data["context"]["fileName"] = files if len(files) > 1 else files[0]
        save_json(path, data)
        return path, True
    return path, False

def get_setting_alias(alias: str) -> tuple[Path, Any]:
    path = get_active_config_path()
    data = load_json(path)
    aliases = load_map()
    if alias not in aliases:
        raise ValueError(f"Unknown alias: {alias}")
    return path, get_by_path(data, aliases[alias]["path"])

def set_setting_alias(alias: str, value: str) -> tuple[Path, Any, bool]:
    """Returns (path, typed_value, restart_required)."""
    aliases = load_map()
    if alias not in aliases:
        raise ValueError(f"Unknown alias: {alias}")
        
    info = aliases[alias]
    typed_val = value
    if info["type"] == "bool":
        if isinstance(value, str):
            typed_val = value.lower() in ("true", "1", "yes", "on")
    elif info["type"] == "int":
        typed_val = int(value)
        
    path = get_active_config_path()
    data = load_json(path)
    set_by_path(data, info["path"], typed_val)
    save_json(path, data)
    
    return path, typed_val, info.get("restart", False)

def list_settings_aliases() -> tuple[Path, dict, dict]:
    """Returns (path, aliases_map, current_values)."""
    path = get_active_config_path()
    data = load_json(path)
    aliases = load_map()
    values = {}
    for alias, info in aliases.items():
        values[alias] = get_by_path(data, info["path"])
    return path, aliases, values
