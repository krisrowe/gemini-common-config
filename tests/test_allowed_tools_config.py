import json
import pytest
from pathlib import Path
from aicfg.sdk import settings as sdk

def test_allowed_tools_add_remove(isolated_env):
    """Test managing allowed tools in user scope via isolated env."""
    user_dir, _ = isolated_env
    user_settings = user_dir / "settings.json"
    
    # Add
    sdk.add_allowed_tool("test-tool", scope="user")
    assert user_settings.exists()
    
    with open(user_settings) as f:
        data = json.load(f)
    assert "test-tool" in data["tools"]["allowed"]
    
    # Remove
    path, success = sdk.remove_allowed_tool("test-tool", scope="user")
    assert success
    
    with open(user_settings) as f:
        data = json.load(f)
    assert "test-tool" not in data["tools"]["allowed"]
