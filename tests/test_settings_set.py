import json
import pytest
from pathlib import Path
from aicfg.sdk import settings as sdk
from aicfg.sdk.settings import get_settings_path, load_json, get_by_path

# NOTE: 'isolated_env' is defined in conftest.py

def test_set_bool_value_user_scope(isolated_env):
    """Test setting a boolean value in user scope."""
    user_dir, *others = isolated_env
    path = get_settings_path("user")
    
    sdk.set_setting_by_alias("preview-features", "true", scope="user")
    
    settings_data = load_json(path)
    assert get_by_path(settings_data, "general.previewFeatures") is True

def test_set_string_value_project_scope(isolated_env, monkeypatch):
    """Test setting a string value in project scope."""
    _, _, project_dir = isolated_env
    monkeypatch.chdir(project_dir)
    path = get_settings_path("project")
    
    sdk.set_setting_by_alias("log-level", "DEBUG", scope="project")
    
    settings_data = load_json(path)
    assert get_by_path(settings_data, "general.logLevel") == "DEBUG"

def test_set_list_value_user_scope(isolated_env):
    """Test setting a list value from a comma-separated string."""
    user_dir, *others = isolated_env
    path = get_settings_path("user")
    
    sdk.set_setting_by_alias("test-list", "item1, item2, item3", scope="user")
    
    settings_data = load_json(path)
    assert get_by_path(settings_data, "internal.testList") == ["item1", "item2", "item3"]

def test_set_int_value_user_scope(isolated_env):
    """Test setting an integer value."""
    user_dir, *others = isolated_env
    path = get_settings_path("user")
    
    sdk.set_setting_by_alias("max-line-length", "120", scope="user")
    
    settings_data = load_json(path)
    assert get_by_path(settings_data, "terminal.maxLineLength") == 120

def test_set_value_handles_restart_flag(isolated_env):
    """Test that the function correctly returns the restart flag."""
    user_dir, *others = isolated_env
    _, _, restart_flag = sdk.set_setting_by_alias("preview-features", "true", scope="user")
    assert restart_flag is True # 'previewFeatures' has restart: true in settings_map.yaml
    
    _, _, restart_flag = sdk.set_setting_by_alias("log-level", "INFO", scope="user")
    assert restart_flag is False # 'logLevel' has restart: false in settings_map.yaml

def test_set_value_with_unknown_name_raises_error(isolated_env):
    """Test that using an unknown alias raises a ValueError."""
    user_dir, *others = isolated_env
    with pytest.raises(ValueError, match="Unknown alias"):
        sdk.set_setting_by_alias("unknown-alias", "some-value", scope="user")
