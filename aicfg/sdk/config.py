import os
import subprocess
from pathlib import Path
import sys
from typing import Optional

# Standard XDG location for active commands (User Scope)
XDG_CMDS_DIR = Path.home() / ".gemini" / "commands"

def get_repo_root() -> Path:
    """
    Locate the repository root relative to this module.
    This works when the package is installed in 'editable' mode (-e).
    """
    # .../gemini-common-config/aicfg/sdk/config.py -> .../gemini-common-config/
    package_dir = Path(__file__).resolve().parent
    repo_root = package_dir.parent.parent
    
    # Validation
    expected_cmds_dir = repo_root / ".gemini" / "commands"
    if not expected_cmds_dir.exists():
        raise FileNotFoundError(
            f"Could not locate repo commands directory at {expected_cmds_dir}.\n"
            "Ensure 'aicfg' is installed in editable mode."
        )
    return repo_root

def get_registry_cmds_dir() -> Path:
    """Returns the 'Registry' commands directory (in gemini-common-config)."""
    return get_repo_root() / ".gemini" / "commands"

def get_git_root() -> Optional[Path]:
    try:
        root = subprocess.check_output(
            ["git", "rev-parse", "--show-toplevel"], 
            stderr=subprocess.DEVNULL
        ).decode().strip()
        return Path(root)
    except subprocess.CalledProcessError:
        return None

def get_project_cmds_dir() -> Path:
    """
    Returns the Project commands directory.
    Prioritizes git root, falls back to CWD.
    """
    root = get_git_root()
    if root:
        return root / ".gemini" / "commands"
    return Path.cwd() / ".gemini" / "commands"

def ensure_dirs():
    """Ensure XDG directory exists."""
    XDG_CMDS_DIR.mkdir(parents=True, exist_ok=True)
