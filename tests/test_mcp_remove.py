import pytest
from aicfg.sdk import mcp_setup
from aicfg.sdk.settings import get_settings_path, load_json, save_json

@pytest.fixture
def setup_server(isolated_env):
    """Helper to register a server for removal tests."""
    user_dir, *others = isolated_env
    server_name = "test-removable-server"
    command_name = "test-cmd-to-remove"
    mcp_setup.register_mcp(command=command_name, name=server_name, scope="user")
    yield server_name, command_name, user_dir

def _get_servers(scope: str) -> dict:
    path = get_settings_path(scope)
    data = load_json(path)
    return data.get("mcpServers", {})

def test_mcp_remove_user_positive(isolated_env, setup_server):
    """Test removing an existing server from user scope."""
    server_name, _, user_dir = setup_server
    
    initial_servers = _get_servers("user")
    assert server_name in initial_servers
    
    mcp_setup.remove_mcp_server(server_name, scope="user")
    
    updated_servers = _get_servers("user")
    assert server_name not in updated_servers

def test_mcp_remove_user_negative(isolated_env):
    """Test attempting to remove a non-existent server from user scope fails gracefully."""
    non_existent_server = "non-existent-server"
    
    initial_servers = _get_servers("user")
    assert non_existent_server not in initial_servers
    
    with pytest.raises(FileNotFoundError, match="not found"):
        mcp_setup.remove_mcp_server(non_existent_server, scope="user")

def test_mcp_remove_project_positive(isolated_env):
    """Test removing an existing server from project scope."""
    user_dir, _, project_dir = isolated_env
    server_name = "proj-removable-server"
    command_name = "proj-cmd-to-remove"
    
    # Register in project scope
    mcp_setup.register_mcp(command=command_name, name=server_name, scope="project")
    
    initial_servers = _get_servers("project")
    assert server_name in initial_servers
    
    mcp_setup.remove_mcp_server(server_name, scope="project")
    
    updated_servers = _get_servers("project")
    assert server_name not in updated_servers

def test_mcp_remove_project_negative(isolated_env):
    """Test attempting to remove a non-existent server from project scope fails gracefully."""
    non_existent_server = "non-existent-proj-server"
    
    initial_servers = _get_servers("project")
    assert non_existent_server not in initial_servers
    
    with pytest.raises(FileNotFoundError, match="not found"):
        mcp_setup.remove_mcp_server(non_existent_server, scope="project")
