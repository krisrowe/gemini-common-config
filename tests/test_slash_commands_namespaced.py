import pytest
from pathlib import Path
from aicfg.sdk import commands as sdk
from aicfg.sdk.config import get_user_cmds_dir

def test_slash_commands_list_with_namespace(isolated_env):
    """
    Validates that list_commands properly discovers both root and namespaced commands.
    """
    # 1. Setup: Add a root command and a namespaced command
    sdk.add_command("root_cmd", prompt="Root", scope="user")
    sdk.add_command("nested_cmd", prompt="Nested", namespace="subdir", scope="user")
    
    # 2. Action: List all commands
    results = sdk.list_commands(scopes=["user"])
    
    # 3. Assertions
    names = [r["name"] for r in results]
    
    assert "root_cmd" in names, "Root command should be listed"
    assert "subdir/nested_cmd" in names, "Namespaced command should be listed with 'namespace/name' format"

def test_register_namespaced_command(isolated_env):
    """
    Validates that register_command correctly handles subdirectories.
    """
    # 1. Setup: Add a namespaced command in user scope
    name = "context/test_reg"
    sdk.add_command("test_reg", prompt="Test", namespace="context", scope="user")
    
    # 2. Action: Register to registry
    reg_path = sdk.register_command(name, source_scope="user")
    
    # 3. Assertions
    assert reg_path.exists()
    assert "context/test_reg.toml" in str(reg_path)
    assert reg_path.parent.name == "context"
    
    reg_data = sdk.get_command(name)
    assert reg_data["prompt"] == "Test"
