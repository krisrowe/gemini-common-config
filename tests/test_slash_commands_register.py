import pytest
from pathlib import Path
from aicfg.sdk import commands as sdk

def test_register_from_user(isolated_env, random_command_name):
    sdk.add_command(random_command_name, prompt="User version", scope="user")
    reg_path = sdk.register_command(random_command_name, source_scope="user")
    assert reg_path.exists()
    reg_data = sdk.get_command(random_command_name)
    assert reg_data["prompt"] == "User version"

def test_register_conflict_with_update(isolated_env, random_command_name):
    sdk.add_command(random_command_name, prompt="Original", scope="user")
    sdk.register_command(random_command_name, source_scope="user")
    sdk.add_command(random_command_name, prompt="Modified", scope="user")
    sdk.register_command(random_command_name, update=True, source_scope="user")
    reg_data = sdk.get_command(random_command_name)
    assert reg_data["prompt"] == "Modified"

def test_register_ambiguity_error(isolated_env, random_command_name):
    sdk.add_command(random_command_name, prompt="User version", scope="user")
    sdk.add_command(random_command_name, prompt="Project version", scope="project")
    with pytest.raises(ValueError, match="Ambiguous source"):
        sdk.register_command(random_command_name)
