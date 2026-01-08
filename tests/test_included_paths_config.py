import json
from pathlib import Path
import pytest
from aicfg.sdk import settings as sdk

def test_paths_add_for_project_with_no_settings(isolated_env, monkeypatch):
    """Test adding path to a clean project (creates .gemini/settings.json)."""
    user_dir, _, project_dir = isolated_env
    monkeypatch.chdir(project_dir) # Still need chdir for CWD-based project detection

    sdk.add_include_directory("../some/lib", scope="project")
    
    settings_file = project_dir / ".gemini" / "settings.json"
    assert settings_file.exists()
    with open(settings_file) as f:
        data = json.load(f)
    assert "../some/lib" in data["context"]["includeDirectories"]
