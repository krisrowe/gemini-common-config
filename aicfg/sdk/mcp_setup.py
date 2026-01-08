import json
import os
import shutil
import subprocess
from pathlib import Path
from typing import Optional

from aicfg.sdk.config import get_aicfg_tool_repo_dir
from aicfg.sdk.settings import get_settings_path, load_json, save_json
from aicfg.sdk.utils import (
    derive_mcp_name,
    find_mcp_command_in_repo,
    is_valid_mcp_name,
    discover_self_mcp_command
)

def register_mcp(
    name: Optional[str] = None,
    path: Optional[str] = None,
    command: Optional[str] = None,
    url: Optional[str] = None,
    is_self: bool = False,
    scope: str = "user",
    args: Optional[str] = None,
) -> dict:
    """The core logic for registering an MCP server."""

    # 1. Determine Source & Command
    mcp_command = None
    repo_path = None

    if is_self:
        mcp_command = discover_self_mcp_command()
        if not mcp_command:
            raise RuntimeError("Could not discover aicfg's own MCP command. Is it installed correctly?")
        # For --self, ensure it's on PATH (pipx handles this)
        if not shutil.which(mcp_command):
            raise FileNotFoundError(f"aicfg's own MCP command '{mcp_command}' not found in PATH.")
    elif path:
        repo_path = Path(path).expanduser().resolve()
        if not repo_path.exists():
            raise FileNotFoundError(f"Path does not exist: {repo_path}")
        
        mcp_command = find_mcp_command_in_repo(repo_path)
        if not mcp_command:
            raise ValueError(f"Could not find an MCP server command (e.g., *-mcp) in {repo_path}")
    elif command:
        if not shutil.which(command):
            raise FileNotFoundError(f"Command not found in PATH: {command}")
        mcp_command = command
    elif url:
        mcp_command = url  # Store URL in command for now
    else:
        raise ValueError("Must provide a PATH, COMMAND, URL, or --self.")

    # 2. Derive and Validate Name
    trimmed_name = ""
    if name:
        trimmed_name = name.strip()
    elif not url: # Only derive if not a URL, URLs require explicit --name
        trimmed_name = derive_mcp_name(mcp_command)
    
    if not is_valid_mcp_name(trimmed_name):
        if url and not name:
             raise ValueError("The --name option is required when registering a URL.")
        raise ValueError(f"Invalid or empty server name: '{trimmed_name}'")

    final_name = trimmed_name
    
    # 3. Check for Conflicts
    settings_path = get_settings_path(scope)
    settings_data = load_json(settings_path)
    if final_name in settings_data.get("mcpServers", {}):
        raise FileExistsError(f"An MCP server with the name '{final_name}' is already registered in {settings_path}.")

    # 4. Validate Server Command (Startup Test for Stdio)
    config = {}
    cli_args = args.split() if args else []
    
    if url:
        config = {"url": url}
        # Optional: Add a HEAD request test here in the future
    else: # Stdio
        try:
            full_command = [mcp_command, "--stdio"] + cli_args
            subprocess.run(
                full_command,
                timeout=2,
                check=True,
                capture_output=True,
                input=b'{"jsonrpc":"2.0","method":"mcp.status","id":1}',
            )
            config = {"command": mcp_command, "args": ["--stdio"] + cli_args}
        except (subprocess.TimeoutExpired, subprocess.CalledProcessError) as e:
            raise ConnectionError(f"Server command '{mcp_command}' failed startup validation. Error: {e.stderr.decode()}")
        except FileNotFoundError:
            raise FileNotFoundError(f"Could not execute command '{mcp_command}'. Is it installed and in your PATH?")

    # 5. Register and Save
    settings_data.setdefault("mcpServers", {})[final_name] = config
    save_json(settings_path, settings_data)
    
    return {"name": final_name, "config": config, "path": str(settings_path)}

def remove_mcp_server(name: str, scope: str) -> tuple[Path, bool]:
    settings_path = get_settings_path(scope)
    settings_data = load_json(settings_path)
    
    if name not in settings_data.get("mcpServers", {}):
        raise FileNotFoundError(f"MCP server '{name}' not found in {settings_path} ({scope} scope).")
        
    del settings_data["mcpServers"][name]
    save_json(settings_path, settings_data)
    return settings_path, True

def list_mcp_servers(scope: str) -> dict:
    settings_path = get_settings_path(scope)
    settings_data = load_json(settings_path)
    return settings_data.get("mcpServers", {})