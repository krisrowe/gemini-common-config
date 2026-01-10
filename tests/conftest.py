import pytest
from pathlib import Path
import uuid
import shutil
import subprocess

@pytest.fixture
def isolated_env(tmp_path_factory, monkeypatch):
    """
    Creates isolated user and registry directories for testing
    and sets environment variables to point to them.
    Mocks shutil.which and subprocess.run for isolated testing.
    """
    # Create temp directories
    user_dir = tmp_path_factory.mktemp("user_home")
    registry_dir = tmp_path_factory.mktemp("registry_repo")
    project_dir = tmp_path_factory.mktemp("project_root")
    
    # Set environment variables
    monkeypatch.setenv("AICFG_USER_DIR", str(user_dir))
    monkeypatch.setenv("AICFG_REPO_DIR", str(registry_dir))
    monkeypatch.setenv("AICFG_PROJECT_DIR", str(project_dir))
    monkeypatch.setenv("AICFG_SKIP_GIT_CHECK_FOR_TESTS", "1") # Skip .git check
    
    # Ensure mock directories exist
    (registry_dir / ".gemini" / "commands").mkdir(parents=True)
    (project_dir / ".gemini" / "commands").mkdir(parents=True)
    
    # Mock shutil.which for test commands
    mock_which_commands = set()
    mock_which_commands.add("aicfg-mcp") # For --self test

    def mock_which(cmd):
        return f"/mock/path/to/{cmd}"

    monkeypatch.setattr(shutil, "which", mock_which)
    
    # Mock subprocess.run for command startup validation
    original_run = subprocess.run
    def mock_subprocess_run(cmd_args, **kwargs):
        cmd_str = " ".join(cmd_args) if isinstance(cmd_args, list) else str(cmd_args)
        
        # Simulate success for mcp server startup check (supports both mcp.status and initialize)
        input_str = str(kwargs.get("input", ""))
        if "--stdio" in cmd_str and ("mcp.status" in input_str or "initialize" in input_str):
            # Return a valid JSON-RPC initialize response
            return subprocess.CompletedProcess(
                args=cmd_args, 
                returncode=0, 
                stdout=b'{"jsonrpc":"2.0","id":1,"result":{"protocolVersion":"2024-11-05","capabilities":{},"serverInfo":{"name":"mock","version":"1.0"}}}', 
                stderr=b""
            )
            
        # For other calls (like git rev-parse), use the original run
        return original_run(cmd_args, **kwargs)

    monkeypatch.setattr(subprocess, "run", mock_subprocess_run)
    
    yield user_dir, registry_dir, project_dir

@pytest.fixture
def random_command_name():
    """Generates a random command name and ensures cleanup."""
    name = f"test_{uuid.uuid4().hex[:8]}"
    yield name
    # Cleanup
    for scope in ["user", "project", "registry"]:
        try:
            sdk.delete_command(name, scope=scope)
        except Exception:
            pass
