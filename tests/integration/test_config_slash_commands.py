import pytest
import uuid
from pathlib import Path
from aicfg.sdk import commands as sdk
from aicfg.sdk.config import XDG_CMDS_DIR, get_registry_cmds_dir, get_project_cmds_dir

@pytest.fixture
def random_command_name():
    """Generates a random command name and ensures cleanup."""
    name = f"test_{uuid.uuid4().hex[:8]}"
    yield name
    # Cleanup
    for scope in ["user", "project", "registry"]:
        sdk.delete_command(name, scope=scope)

def test_add_user_scoped(random_command_name):
    path = sdk.add_command(random_command_name, prompt="User", scope="user")
    assert path.exists()
    assert path.parent == XDG_CMDS_DIR
    
    data = sdk.get_command(random_command_name)
    assert data["prompt"] == "User"

def test_add_project_scoped(random_command_name):
    path = sdk.add_command(random_command_name, prompt="Project", scope="project")
    assert path.exists()
    assert path.parent == get_project_cmds_dir()
    
    data = sdk.get_command(random_command_name)
    assert data["prompt"] == "Project"

def test_publish_to_registry(random_command_name):
    sdk.add_command(random_command_name, prompt="Shared", scope="user")
    reg_path = sdk.publish_command(random_command_name)
    assert reg_path.exists()
    assert reg_path.parent == get_registry_cmds_dir()

def test_list_all_scopes(random_command_name):
    # Setup across all 3
    sdk.add_command(random_command_name, prompt="Base", scope="user")
    sdk.publish_command(random_command_name)
    sdk.add_command(random_command_name, prompt="Base", scope="project")
    
    results = sdk.list_commands()
    match = next(r for r in results if r["name"] == random_command_name)
    
    assert match["user"]["exists"] is True
    assert match["registry"]["exists"] is True
    assert match["project"]["exists"] is True
    assert match["synced"] is True

def test_diff_detection(random_command_name):
    # Create different content
    sdk.add_command(random_command_name, prompt="Version A", scope="user")
    sdk.add_command(random_command_name, prompt="Version B", scope="registry")
    
    results = sdk.list_commands()
    match = next(r for r in results if r["name"] == random_command_name)
    
    assert match["synced"] is False
    assert match["user"]["hash"] != match["registry"]["hash"]