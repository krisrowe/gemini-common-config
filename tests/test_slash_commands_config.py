import pytest
from pathlib import Path
from aicfg.sdk import commands as sdk
from aicfg.sdk.config import get_user_cmds_dir, get_registry_cmds_dir

# The 'isolated_env' fixture is auto-discovered from conftest.py

def test_add_user_scoped(isolated_env):
    path = sdk.add_command("test-cmd", prompt="User", scope="user")
    assert path.exists()
    assert path.parent == get_user_cmds_dir()
    data = sdk.get_command("test-cmd")
    assert data["prompt"] == "User"

def test_publish_to_registry(isolated_env):
    sdk.add_command("test-cmd", prompt="Shared", scope="user")
    reg_path = sdk.publish_command("test-cmd")
    assert reg_path.exists()
    assert reg_path.parent == get_registry_cmds_dir()

def test_list_all_scopes(isolated_env):
    sdk.add_command("test-cmd", prompt="Base", scope="user")
    sdk.publish_command("test-cmd")
    
    results = sdk.list_commands()
    match = next((r for r in results if r["name"] == "test-cmd"), None)
    
    assert match is not None
    assert match["user"]["exists"] is True
    assert match["registry"]["exists"] is True
    assert match["synced"] is True

def test_diff_detection(isolated_env):
    sdk.add_command("test-cmd", prompt="Version A", scope="user")
    sdk.add_command("test-cmd", prompt="Version B", scope="registry")
    
    results = sdk.list_commands()
    match = next(r for r in results if r["name"] == "test-cmd")
    
    assert match["synced"] is False
    assert match["user"]["hash"] != match["registry"]["hash"]
