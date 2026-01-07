import json
import os
from pathlib import Path
import pytest
from aicfg.sdk import settings as sdk

def load_settings(project_root):
    path = project_root / ".gemini" / "settings.json"
    if not path.exists():
        return {}
    with open(path) as f:
        return json.load(f)

def test_paths_add_for_project_with_no_settings(tmp_path, monkeypatch):
    """Test adding path to a clean project (creates .gemini/settings.json)."""
    monkeypatch.chdir(tmp_path)
    
    # Run action - explicitly set project scope to ensure it targets the tmp_path
    new_path = "../some/lib"
    sdk.add_include_directory(new_path, scope="project")
    
    # Verify post-state
    settings_file = tmp_path / ".gemini" / "settings.json"
    assert settings_file.exists()
    
    data = load_settings(tmp_path)
    assert "context" in data
    assert "includeDirectories" in data["context"]
    assert new_path in data["context"]["includeDirectories"]

def test_paths_add_for_project_with_existing_settings(tmp_path, monkeypatch):
    """Test adding path when settings.json exists but has no context/paths."""
    monkeypatch.chdir(tmp_path)
    
    # Setup existing settings
    gemini_dir = tmp_path / ".gemini"
    gemini_dir.mkdir()
    initial_data = {"tools": {"allowed": ["test-tool"]}}
    with open(gemini_dir / "settings.json", "w") as f:
        json.dump(initial_data, f)
        
    # Run action
    new_path = "libs/utils"
    sdk.add_include_directory(new_path, scope="project")
    
    # Verify
    data = load_settings(tmp_path)
    assert "tools" in data
    assert data["tools"]["allowed"] == ["test-tool"]  # Preserved
    assert new_path in data["context"]["includeDirectories"]

def test_paths_add_project_with_existing_paths(tmp_path, monkeypatch):
    """Test appending path to existing list."""
    monkeypatch.chdir(tmp_path)
    
    # Setup existing settings
    gemini_dir = tmp_path / ".gemini"
    gemini_dir.mkdir()
    initial_data = {
        "context": {
            "includeDirectories": ["existing/path"]
        }
    }
    with open(gemini_dir / "settings.json", "w") as f:
        json.dump(initial_data, f)
        
    # Run action
    new_path = "new/path"
    sdk.add_include_directory(new_path, scope="project")
    
    # Verify
    data = load_settings(tmp_path)
    dirs = data["context"]["includeDirectories"]
    assert len(dirs) == 2
    assert "existing/path" in dirs
    assert "new/path" in dirs