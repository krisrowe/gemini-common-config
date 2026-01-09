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
