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
    else: # Stdio
        full_command = [mcp_command, "--stdio"] + cli_args
        result = check_mcp_startup(full_command)
        
        if not result["success"]:
             raise ConnectionError(f"Server command '{mcp_command}' failed startup validation. Error: {result.get('error')}")
        
        config = {"command": mcp_command, "args": ["--stdio"] + cli_args}

    # 5. Register and Save
    settings_data.setdefault("mcpServers", {})[final_name] = config
    save_json(settings_path, settings_data)
    
    return {"name": final_name, "config": config, "path": str(settings_path)}

def check_mcp_startup(command_list: list) -> dict:
    """
    Checks if an MCP server starts up correctly by sending an initialize request.
    Returns a dict with 'success', 'response' (JSON), or 'error'.
    """
    init_payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {"name": "aicfg-check", "version": "1.0"}
        }
    }
    
    try:
        process = subprocess.run(
            command_list,
            input=json.dumps(init_payload).encode(),
            capture_output=True,
            timeout=5,
            check=False 
        )
        
        if process.returncode != 0 and not process.stdout:
             return {"success": False, "error": f"Process exited with code {process.returncode}. Stderr: {process.stderr.decode()}"}

        # Try to parse the first line of stdout
        output_lines = process.stdout.decode().strip().split('\n')
        if not output_lines:
             return {"success": False, "error": "No output received from server."}
             
        try:
            response = json.loads(output_lines[0])
            # Basic validation of JSON-RPC response
            if "result" in response or "error" in response:
                 return {"success": True, "response": response}
            else:
                 return {"success": False, "error": f"Invalid JSON-RPC response: {output_lines[0]}"}
        except json.JSONDecodeError:
             return {"success": False, "error": f"Non-JSON output received: {output_lines[0]}"}

    except subprocess.TimeoutExpired:
        return {"success": False, "error": "Connection timed out (server took too long to respond)."}
    except FileNotFoundError:
        return {"success": False, "error": f"Command not found: {command_list[0]}"}
    except Exception as e:
        return {"success": False, "error": str(e)}

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