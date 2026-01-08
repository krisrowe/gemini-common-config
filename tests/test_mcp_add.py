import pytest
import uuid
from pathlib import Path
from aicfg.sdk import mcp_setup
from aicfg.sdk.settings import get_settings_path, load_json

@pytest.fixture
def random_server_name():
    """Generates a random server name for isolated testing."""
    return f"test-server-{uuid.uuid4().hex[:8]}"

def _get_servers(scope: str) -> dict:
    path = get_settings_path(scope)
    data = load_json(path)
    return data.get("mcpServers", {})

def test_mcp_add_self(isolated_env, random_server_name):
    """Test registering aicfg itself."""
    user_dir, *others = isolated_env
    
    initial_servers = _get_servers("user")
    assert random_server_name not in initial_servers # Ensure clean start
    
    result = mcp_setup.register_mcp(is_self=True, name=random_server_name, scope="user")
    assert result["name"] == random_server_name
    
    updated_servers = _get_servers("user")
    assert random_server_name in updated_servers

def test_mcp_add_from_command_derived_name_same(isolated_env, random_server_name):
    """Test command name without 'mcp' segment is used as-is."""
    # Create a mock command that doesn't have an 'mcp' segment
    command_name = "mytool"
    
    result = mcp_setup.register_mcp(command=command_name, name=random_server_name, scope="user")
    assert result["name"] == random_server_name
    assert _get_servers("user")[random_server_name]["command"] == command_name

def test_mcp_add_from_command_derived_name_simplified_prefix(isolated_env, random_server_name):
    """Test command name with 'mcp-' prefix is simplified."""
    command_name = "mcp-mytool"
    derived_name = "mytool"
    
    result = mcp_setup.register_mcp(command=command_name, name=random_server_name, scope="user")
    assert result["name"] == random_server_name # Name is explicitly set in test, but internal derived name used for config entry
    assert _get_servers("user")[random_server_name]["command"] == command_name
    
    # This specific test will now assert the derivation logic directly.
    assert mcp_setup.derive_mcp_name(command_name) == derived_name

def test_mcp_add_from_command_derived_name_simplified_suffix(isolated_env, random_server_name):
    """Test command name with '-mcp' suffix is simplified."""
    command_name = "mytool-mcp"
    derived_name = "mytool"
    
    result = mcp_setup.register_mcp(command=command_name, name=random_server_name, scope="user")
    assert result["name"] == random_server_name
    assert _get_servers("user")[random_server_name]["command"] == command_name
    assert mcp_setup.derive_mcp_name(command_name) == derived_name

def test_mcp_add_from_command_derived_name_simplified_infix(isolated_env, random_server_name):
    """Test command name with '-mcp-' infix is simplified."""
    command_name = "my-mcp-tool"
    derived_name = "my-tool"
    
    result = mcp_setup.register_mcp(command=command_name, name=random_server_name, scope="user")
    assert result["name"] == random_server_name
    assert _get_servers("user")[random_server_name]["command"] == command_name
    assert mcp_setup.derive_mcp_name(command_name) == derived_name

def test_mcp_add_from_command_derived_name_simplified_multiple(isolated_env, random_server_name):
    """Test command name with multiple 'mcp' segments is simplified."""
    command_name = "mcp-my-mcp-tool-mcp"
    derived_name = "my-tool"
    
    result = mcp_setup.register_mcp(command=command_name, name=random_server_name, scope="user")
    assert result["name"] == random_server_name
    assert _get_servers("user")[random_server_name]["command"] == command_name
    assert mcp_setup.derive_mcp_name(command_name) == derived_name

def test_mcp_add_from_command_with_specified_name(isolated_env):
    """Test explicit --name overrides derivation."""
    command_name = "long-mcp-command"
    specified_name = "custom-tool"
    
    result = mcp_setup.register_mcp(command=command_name, name=specified_name, scope="user")
    assert result["name"] == specified_name
    assert _get_servers("user")[specified_name]["command"] == command_name

def test_mcp_add_from_command_with_specified_name_trimmed(isolated_env):
    """Test explicit --name is trimmed and validated."""
    command_name = "some-cmd"
    specified_name_raw = "  my-trimmed-name  "
    specified_name_trimmed = "my-trimmed-name"
    
    result = mcp_setup.register_mcp(command=command_name, name=specified_name_raw, scope="user")
    assert result["name"] == specified_name_trimmed
    assert _get_servers("user")[specified_name_trimmed]["command"] == command_name

def test_mcp_add_from_command_name_invalid_illegal_chars(isolated_env):
    """Test invalid names (illegal characters) fail."""
    command_name = "some-cmd"
    invalid_name = "invalid!name"
    
    with pytest.raises(ValueError, match="Invalid or empty server name"):
        mcp_setup.register_mcp(command=command_name, name=invalid_name, scope="user")

def test_mcp_add_from_path(isolated_env, random_server_name):
    """Test registering from a local repository path."""
    user_dir, registry_dir, _ = isolated_env
    repo_path = registry_dir # Use registry_dir as a mock repo
    
    # Create a mock setup.py or pyproject.toml in the mock repo
    (repo_path / "setup.py").write_text("console_scripts = ['mock-tool-mcp=mock_module:func']")

    result = mcp_setup.register_mcp(path=str(repo_path), name=random_server_name, scope="user")
    assert result["name"] == random_server_name
    assert _get_servers("user")[random_server_name]["command"] == "mock-tool-mcp"

def test_mcp_add_from_url(isolated_env):
    """Test registering an HTTP server from a URL (requires --name)."""
    url = "http://localhost:8000/mcp"
    server_name = "my-http-server"
    
    result = mcp_setup.register_mcp(url=url, name=server_name, scope="user")
    assert result["name"] == server_name
    assert _get_servers("user")[server_name]["url"] == url

def test_mcp_add_conflict(isolated_env, random_server_name):
    """Test adding a server with a conflicting name fails."""
    mcp_setup.register_mcp(command="first-cmd", name=random_server_name, scope="user")
    
    with pytest.raises(FileExistsError, match="already registered"):
        mcp_setup.register_mcp(command="second-cmd", name=random_server_name, scope="user")
