import pytest
import uuid
import shutil
from aicfg.sdk import mcp_setup
from aicfg.sdk.settings import get_settings_path, load_json
from pathlib import Path

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
    mcp_setup.register_mcp(is_self=True, name=random_server_name, scope="user")
    assert random_server_name in _get_servers("user")

def test_mcp_add_from_command(isolated_env, random_server_name, monkeypatch):
    """Test registering from a command name."""
    command_name = "mock-mcp-cmd"
    # Mock shutil.which for the command
    monkeypatch.setattr(shutil, 'which', lambda cmd: "/usr/local/bin/" + cmd)
    
    mcp_setup.register_mcp(command=command_name, name=random_server_name, scope="user")
    servers = _get_servers("user")
    assert random_server_name in servers
    assert servers[random_server_name]["command"] == command_name

def test_mcp_add_from_path(isolated_env, random_server_name):
    """Test registering from a local repository path."""
    _, registry_dir, _ = isolated_env # registry_dir is a mock repo path
    repo_path = registry_dir # For clarity, using as repo_path
    
    # Create a mock setup.py in the mock repo
    (repo_path / "setup.py").write_text("from setuptools import setup; setup(name='mock-repo', console_scripts=['mock-tool-mcp=mock_module:func'])")
    
    mcp_setup.register_mcp(path=str(repo_path), name=random_server_name, scope="user")
    servers = _get_servers("user")
    assert random_server_name in servers
    assert servers[random_server_name]["command"] == "mock-tool-mcp"

def test_mcp_add_from_url(isolated_env, random_server_name):
    """Test registering an HTTP server from a URL (requires --name)."""
    url = "http://localhost:8000/mcp"
    
    mcp_setup.register_mcp(url=url, name=random_server_name, scope="user")
    servers = _get_servers("user")
    assert random_server_name in servers
    assert servers[random_server_name]["url"] == url

def test_mcp_remove_user_negative(isolated_env):
    """Test attempting to remove a non-existent server from user scope fails gracefully."""
    non_existent_server = "non-existent-server"
    with pytest.raises(FileNotFoundError, match="not found"):
        mcp_setup.remove_mcp_server(non_existent_server, scope="user")

def test_mcp_remove_project_positive(isolated_env):
    """Test removing an existing server from project scope."""
    server_name = "proj-removable-server"
    command_name = "proj-cmd-to-remove"
    mcp_setup.register_mcp(command=command_name, name=server_name, scope="project")
    
    mcp_setup.remove_mcp_server(server_name, scope="project")
    assert server_name not in _get_servers("project")

def test_mcp_remove_project_negative(isolated_env):
    """Test attempting to remove a non-existent server from project scope fails gracefully."""
    non_existent_server = "non-existent-proj-server"
    with pytest.raises(FileNotFoundError, match="not found"):
        mcp_setup.remove_mcp_server(non_existent_server, scope="project")

def test_mcp_add_conflict(isolated_env, random_server_name):
    """Test adding a server with a conflicting name fails."""
    mcp_setup.register_mcp(command="first-cmd", name=random_server_name, scope="user")
    with pytest.raises(FileExistsError, match="already registered"):
        mcp_setup.register_mcp(command="second-cmd", name=random_server_name, scope="user")

def test_check_mcp_startup_success(monkeypatch):
    """Test check_mcp_startup with a valid server response."""
    import subprocess
    
    mock_response = b'{"jsonrpc":"2.0","id":1,"result":{"capabilities":{}}}'
    
    class MockCompletedProcess:
        returncode = 0
        stdout = mock_response
        stderr = b""
        
    def mock_run(*args, **kwargs):
        return MockCompletedProcess()
        
    monkeypatch.setattr(subprocess, "run", mock_run)
    
    result = mcp_setup.check_mcp_startup(["mock-server", "--stdio"])
    assert result["success"] is True
    assert result["response"]["result"]["capabilities"] == {}

def test_check_mcp_startup_failure(monkeypatch):
    """Test check_mcp_startup handling a server failure/timeout."""
    import subprocess
    
    def mock_run_timeout(*args, **kwargs):
        raise subprocess.TimeoutExpired(cmd=args[0], timeout=5)
        
    monkeypatch.setattr(subprocess, "run", mock_run_timeout)
    
    result = mcp_setup.check_mcp_startup(["slow-server"])
    assert result["success"] is False
    assert "timed out" in result["error"]
