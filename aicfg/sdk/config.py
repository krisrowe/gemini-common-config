import os
import subprocess
from pathlib import Path
from typing import Optional

# --- Central Path Functions with Environment Variable Overrides ---

def get_user_scoped_gemini_dir() -> Path:
    """
    Returns the user's Gemini config directory.
    Priority: AICFG_USER_DIR env var > ~/.gemini
    """
    path_str = os.environ.get("AICFG_USER_DIR")
    if path_str:
        return Path(path_str)
    return Path.home() / ".gemini"

def get_aicfg_tool_repo_dir() -> Path:
    """
    Returns the root directory of the aicfg tool repository.
    Priority: AICFG_REPO_DIR env var > discovered git root.
    """
    path_str = os.environ.get("AICFG_REPO_DIR")
    if path_str:
        return Path(path_str)
    
    # Discover relative to this file
    package_dir = Path(__file__).resolve().parent
    repo_root = package_dir.parent.parent
    
    # Validation
    if not (repo_root / ".git").exists() and not os.environ.get("AICFG_SKIP_GIT_CHECK_FOR_TESTS"):
        raise FileNotFoundError(
            f"Could not locate .git directory in discovered repo root: {repo_root}.\n"
            "Ensure 'aicfg' is installed in editable mode from a git repository."
        )
    return repo_root

# --- Derived Paths ---

def get_user_cmds_dir() -> Path:
    """User-scoped commands directory (~/.gemini/commands)."""
    return get_user_scoped_gemini_dir() / "commands"

def get_registry_cmds_dir() -> Path:
    """Registry commands directory (in gemini-common-config)."""
    return get_aicfg_tool_repo_dir() / ".gemini" / "commands"

def get_project_cmds_dir() -> Path:
    """Project-scoped commands directory (./.gemini/commands)."""
    # Allow override for testing
    path_str = os.environ.get("AICFG_PROJECT_DIR")
    if path_str:
        return Path(path_str) / ".gemini" / "commands"

    try:
        root = subprocess.check_output(["git", "rev-parse", "--show-toplevel"], stderr=subprocess.DEVNULL).decode().strip()
        return Path(root) / ".gemini" / "commands"
    except subprocess.CalledProcessError:
        return Path.cwd() / ".gemini" / "commands"

def ensure_dirs():
    """Ensure user command directory exists."""
    get_user_cmds_dir().mkdir(parents=True, exist_ok=True)