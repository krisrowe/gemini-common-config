import json
import pytest
from pathlib import Path
from aicfg.sdk import settings as sdk
from aicfg.sdk.settings import get_settings_path, load_json, save_json, set_by_path, load_map

# NOTE: 'isolated_env' is defined in conftest.py

@pytest.fixture
def pre_populated_settings(isolated_env):
    user_dir, project_dir = isolated_env
    user_path = get_settings_path("user")
    project_path = get_settings_path("project")
    
    # Populate user settings
    user_data = {
        "general": {
            "previewFeatures": True,
            "logLevel": "INFO"
        },
        "tools": {
            "allowed": ["toolA", "toolB"]
        }
    }
    save_json(user_path, user_data)

    # Populate project settings (will override user for logLevel, add a new one)
    project_data = {
        "general": {
            "logLevel": "DEBUG"
        },
        "terminal": {
            "maxLineLength": 100
        }
    }
    save_json(project_path, project_data)

    return user_path, project_path

def test_get_value_user_scope(pre_populated_settings):
    """Test getting a setting from user scope."""
    user_path, _ = pre_populated_settings
    
    path, value = sdk.get_setting_by_alias("preview-features", scope="user")
    assert path == user_path
    assert value is True

def test_get_value_project_scope_override(pre_populated_settings, monkeypatch):
    """Test getting a setting from project scope that overrides user scope."""
    _, project_path = pre_populated_settings
    monkeypatch.chdir(project_path.parent.parent) # Change to mock project root

    path, value = sdk.get_setting_by_alias("log-level", scope="project")
    assert path == project_path
    assert value == "DEBUG"

def test_get_value_project_scope_only(pre_populated_settings, monkeypatch):
    """Test getting a setting only present in project scope."""
    _, project_path = pre_populated_settings
    monkeypatch.chdir(project_path.parent.parent)

    path, value = sdk.get_setting_by_alias("max-line-length", scope="project")
    assert path == project_path
    assert value == 100

def test_get_value_not_set_returns_none(isolated_env):
    """Test getting a setting that is not set returns None."""
    user_path = get_settings_path("user")
    # Ensure settings file is empty or non-existent
    if user_path.exists(): user_path.unlink()
    
    # Use an alias that's valid in the map but not set in the file
    path, value = sdk.get_setting_by_alias("log-level", scope="user")
    assert path == user_path
    assert value is None

def test_get_value_unknown_name_raises_error(isolated_env):
    """Test getting an unknown alias raises a ValueError."""
    with pytest.raises(ValueError, match="Unknown alias"):
        sdk.get_setting_by_alias("non-existent-alias", scope="user")

def test_list_values_user_scope(pre_populated_settings):
    """Test listing all settings for user scope."""
    user_path, _ = pre_populated_settings
    path, aliases_map, values = sdk.list_settings_by_alias(scope="user")
    
    assert path == user_path
    assert "preview-features" in values
    assert values["preview-features"] is True
    assert values["log-level"] == "INFO"
    assert values["allowed-tools"] == ["toolA", "toolB"]
    assert values["max-line-length"] is None # Not set in user scope

def test_list_values_project_scope_with_overrides(pre_populated_settings, monkeypatch):
    """Test listing all settings for project scope, with overrides."""
    _, project_path = pre_populated_settings
    monkeypatch.chdir(project_path.parent.parent)

    path, aliases_map, values = sdk.list_settings_by_alias(scope="project")
    
    assert path == project_path
    assert "preview-features" in values
    assert values["preview-features"] is True # Inherited from user
    assert values["log-level"] == "DEBUG" # Overridden by project
    assert values["allowed-tools"] == ["toolA", "toolB"] # Inherited from user
    assert values["max-line-length"] == 100 # Only in project
