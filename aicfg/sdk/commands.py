from pathlib import Path
import shutil
import fnmatch
from typing import List, Dict, Optional
from aicfg.sdk.config import (
    XDG_CMDS_DIR, 
    get_registry_cmds_dir, 
    get_project_cmds_dir, 
    ensure_dirs
)
from aicfg.sdk.utils import save_toml, load_toml, get_file_info

def add_command(name: str, prompt: Optional[str] = None, desc: Optional[str] = None, scope: str = "user") -> Path:
    """Add a new command to specified scope."""
    ensure_dirs()
    filename = f"{name}.toml"
    
    if scope == "project":
        target_dir = get_project_cmds_dir()
        target_dir.mkdir(parents=True, exist_ok=True)
        path = target_dir / filename
    elif scope == "registry":
        path = get_registry_cmds_dir() / filename
    else:
        path = XDG_CMDS_DIR / filename
    
    data = {
        "description": desc or f"Command for {name}",
        "prompt": prompt or "Write your prompt here..."
    }
    save_toml(path, data)
    return path

def list_commands(filter_pattern: Optional[str] = None, scopes: Optional[List[str]] = None) -> List[Dict]:
    """
    List all commands.
    
    Args:
        filter_pattern: Shell-style wildcard for name.
        scopes: List of scopes to include ["user", "registry", "project"]. 
                If None, checks all. Sync status is calculated only among included scopes.
    """
    ensure_dirs()
    registry_dir = get_registry_cmds_dir()
    project_dir = get_project_cmds_dir()
    
    valid_scopes = {"user", "registry", "project"}
    active_scopes = set(scopes) if scopes else valid_scopes
    
    # Gather paths only from active scopes
    all_paths = []
    if "user" in active_scopes:
        all_paths.extend(list(XDG_CMDS_DIR.glob("*.toml")))
    if "registry" in active_scopes:
        all_paths.extend(list(registry_dir.glob("*.toml")))
    if "project" in active_scopes:
        if project_dir.exists():
            all_paths.extend(list(project_dir.glob("*.toml")))
    
    all_names = sorted({f.stem for f in all_paths})
    
    if filter_pattern:
        all_names = [n for n in all_names if fnmatch.fnmatch(n, filter_pattern)]
    
    results = []
    for name in all_names:
        # Check files based on active scopes
        # For inactive scopes, we return empty info (exists=False) effectively
        user_info = get_file_info(XDG_CMDS_DIR / f"{name}.toml") if "user" in active_scopes else {"exists": False, "hash": None}
        reg_info = get_file_info(registry_dir / f"{name}.toml") if "registry" in active_scopes else {"exists": False, "hash": None}
        proj_info = get_file_info(project_dir / f"{name}.toml") if "project" in active_scopes else {"exists": False, "hash": None}
        
        # Calculate sync status only for active scopes where file exists
        relevant_infos = []
        if "user" in active_scopes: relevant_infos.append(user_info)
        if "registry" in active_scopes: relevant_infos.append(reg_info)
        if "project" in active_scopes: relevant_infos.append(proj_info)
        
        present_hashes = [info["hash"] for info in relevant_infos if info["exists"]]
        
        if not present_hashes:
            synced = False # Or True? If it doesn't exist anywhere in scope? 
            # If we found the name, it must exist in at least one scope.
        elif len(present_hashes) == 1:
            synced = True # Exists in only one of the requested scopes -> inherently synced
        else:
            synced = len(set(present_hashes)) == 1
            
        results.append({
            "name": name,
            "synced": synced,
            "user": user_info,
            "registry": reg_info,
            "project": proj_info
        })
    return results

def get_command(name: str) -> Optional[Dict]:
    """Get command details. Priority: Project > User > Registry."""
    ensure_dirs()
    proj_path = get_project_cmds_dir() / f"{name}.toml"
    xdg_path = XDG_CMDS_DIR / f"{name}.toml"
    reg_path = get_registry_cmds_dir() / f"{name}.toml"
    
    if proj_path.exists(): return load_toml(proj_path)
    if xdg_path.exists(): return load_toml(xdg_path)
    if reg_path.exists(): return load_toml(reg_path)
    return None

def delete_command(name: str, scope: str = "user") -> bool:
    """Delete command from specified scope."""
    ensure_dirs()
    if scope == "user":
        path = XDG_CMDS_DIR / f"{name}.toml"
    elif scope == "project":
        path = get_project_cmds_dir() / f"{name}.toml"
    elif scope == "registry":
        path = get_registry_cmds_dir() / f"{name}.toml"
    else:
        raise ValueError("Invalid scope")
        
    if path.exists():
        path.unlink()
        return True
    return False

def publish_command(name: str) -> Optional[Path]:
    """Copy User (XDG) -> Registry."""
    ensure_dirs()
    registry_dir = get_registry_cmds_dir()
    xdg_path = XDG_CMDS_DIR / f"{name}.toml"
    reg_path = registry_dir / f"{name}.toml"
    if not xdg_path.exists(): raise FileNotFoundError(f"Command '{name}' not found in User scope.")
    shutil.copy2(xdg_path, reg_path)
    return reg_path

def install_command(name: str) -> Optional[Path]:
    """Copy Registry -> User (XDG)."""
    ensure_dirs()
    registry_dir = get_registry_cmds_dir()
    xdg_path = XDG_CMDS_DIR / f"{name}.toml"
    reg_path = registry_dir / f"{name}.toml"
    if not reg_path.exists(): raise FileNotFoundError(f"Command '{name}' not found in Registry.")
    shutil.copy2(reg_path, xdg_path)
    return xdg_path

def get_diff(name: str) -> Optional[tuple[List[str], List[str]]]:
    """Get lines for diffing (Registry vs User)."""
    ensure_dirs()
    xdg_path = XDG_CMDS_DIR / f"{name}.toml"
    reg_path = get_registry_cmds_dir() / f"{name}.toml"
    if not xdg_path.exists() or not reg_path.exists(): return None
    with open(reg_path) as f: reg_lines = f.readlines()
    with open(xdg_path) as f: xdg_lines = f.readlines()
    return (reg_lines, xdg_lines)
