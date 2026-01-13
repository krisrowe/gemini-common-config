import pytest
import uuid
from aicfg.sdk import mcp_setup


@pytest.fixture
def random_server_name():
    """Generates a random server name for isolated testing."""
    return f"test-server-{uuid.uuid4().hex[:8]}"


def test_mcp_list(isolated_env, random_server_name):
    """Test listing registered servers."""
    # Register a server first
    mcp_setup.register_mcp(is_self=True, name=random_server_name, scope="user")

    result = mcp_setup.list_mcp_servers("user")
    server_names = [s["name"] for s in result["servers"]]
    assert random_server_name in server_names
