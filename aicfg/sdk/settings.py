import json
import yaml
import collections.abc
from pathlib import Path
from typing import Any, List, Optional

from aicfg.sdk.config import get_user_scoped_gemini_dir, get_project_cmds_dir

MAP_PATH = Path(__file__).parent / "settings_map.yaml"

def get_settings_path(scope: Optional[str] = None) -> Path:
    if scope == "user": return get_user_scoped_gemini_dir() / "settings.json"
    project_path = get_project_cmds_dir().parent / "settings.json"
    if scope == "project": return project_path
    return project_path if project_path.exists() else get_user_scoped_gemini_dir() / "settings.json"

def load_json(path: Path) -> dict:
    if not path or not path.exists(): return {}
    try:
        with open(path, "r") as f: return json.load(f)
    except Exception: return {}

def save_json(path: Path, data: dict):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f: json.dump(data, f, indent=2)

def load_map() -> dict:
    if not MAP_PATH.exists(): return {}
    with open(MAP_PATH, "r") as f: return yaml.safe_load(f) or {}

def get_by_path(data: dict, dot_path: str) -> Any:
    parts = dot_path.split(".")
    curr = data
    for part in parts:
        if isinstance(curr, dict) and part in curr: curr = curr[part]
        else: return None
    return curr

def set_by_path(data: dict, dot_path: str, value: Any):
    parts = dot_path.split(".")
    curr = data
    for part in parts[:-1]:
        curr = curr.setdefault(part, {})
    curr[parts[-1]] = value

def _get_path_for_alias(alias: str) -> str:
    aliases = load_map()
    if alias not in aliases:
        # Fallback for core logic if map is broken, but ideally we crash or handle
        raise ValueError(f"Unknown alias: {alias}")
    return aliases[alias]["path"]

# --- SDK API ---

def add_allowed_tool(name: str, scope: Optional[str] = None) -> tuple[Path, bool]:
    return _modify_list(name, scope, _get_path_for_alias("allowed-tools"), "add")

def remove_allowed_tool(name: str, scope: Optional[str] = None) -> tuple[Path, bool]:
    return _modify_list(name, scope, _get_path_for_alias("allowed-tools"), "remove")

def add_include_directory(path: str, scope: Optional[str] = None) -> tuple[Path, bool]:
    return _modify_list(path, scope, _get_path_for_alias("include-directories"), "add")

def _modify_list(item: str, scope: Optional[str], path_str: str, action: str) -> tuple[Path, bool]:
    path = get_settings_path(scope)
    data = load_json(path)
    current_list = get_by_path(data, path_str)
    if current_list is None: current_list = []
    
    changed = False
    if action == "add" and item not in current_list:
        current_list.append(item)
        changed = True
    elif action == "remove" and item in current_list:
        current_list.remove(item)
        changed = True
    
    if changed:
        set_by_path(data, path_str, current_list)
        save_json(path, data)
        
    return path, changed

def get_setting_by_alias(alias: str, scope: Optional[str] = None) -> tuple[Path, Any]:
    # For get, we probably want resolved value? 
    # Current implementation just reads from specific scope file.
    # If we want inheritance, we should use list_settings_by_alias logic or similar.
    # But for "set" verification, we usually check the file. 
    # Let's keep it simple: get from SPECIFIC scope file.
    path = get_settings_path(scope)
    data = load_json(path)
    aliases = load_map()
    if alias not in aliases: raise ValueError(f"Unknown alias: {alias}")
    return path, get_by_path(data, aliases[alias]["path"])

def set_setting_by_alias(alias: str, value: str, scope: Optional[str] = None) -> tuple[Path, Any, bool]:
    path = get_settings_path(scope)
    aliases = load_map()
    if alias not in aliases: raise ValueError(f"Unknown alias: {alias}")
    info = aliases[alias]
    
    typed_val = value
    if info["type"] == "bool":
        if isinstance(value, str): typed_val = value.lower() in ("true", "1", "yes", "on")
    elif info["type"] == "int": typed_val = int(value)
    elif info["type"] == "list":
        typed_val = [v.strip() for v in value.split(",")]

    data = load_json(path)
    set_by_path(data, info["path"], typed_val)
    save_json(path, data)
    return path, typed_val, info.get("restart", False)

def list_settings_by_alias(scope: Optional[str] = None) -> tuple[Path, dict, dict]:
    target_path = get_settings_path(scope)
    
    # Load user data first
    user_path = get_user_scoped_gemini_dir() / "settings.json"
    data = load_json(user_path)
    
    # Merge project data if needed
    if scope == "project":
        project_path = get_project_cmds_dir().parent / "settings.json"
        if project_path.exists():
            project_data = load_json(project_path)
            
            def update(d, u):
                for k, v in u.items():
                    if isinstance(v, collections.abc.Mapping):
                        d[k] = update(d.get(k, {}), v)
                    else:
                        d[k] = v
                return d
            update(data, project_data)

    aliases = load_map()
    values = {}
    for alias, info in aliases.items():
        values[alias] = get_by_path(data, info["path"])
    return target_path, aliases, values
