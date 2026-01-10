import json
import logging
from typing import Any, Optional
from mcp.server.fastmcp import FastMCP
from aicfg.sdk import commands as cmds_sdk
from aicfg.sdk import settings as settings_sdk
from aicfg.sdk import mcp_setup as mcp_sdk

logger = logging.getLogger(__name__)
mcp = FastMCP("aicfg")

@mcp.tool()
async def add_slash_command(
    name: str,
    prompt: str,
    description: Optional[str] = None
) -> dict[str, Any]:
    """
    Add a new slash command to the local configuration.
    
    Args:
        name: Command name (e.g. 'fix-bug')
        prompt: The prompt text for the command
        description: Short description
    """
    try:
        path = cmds_sdk.add_command(name, prompt, description)
        return {"success": True, "path": str(path), "status": "PRIVATE"}
    except Exception as e:
        logger.error(f"Error adding command: {e}")
        return {"error": str(e)}

@mcp.tool()
async def publish_slash_command(name: str) -> dict[str, Any]:
    """
    Publish a local slash command to the common configuration registry.
    
    Args:
        name: The name of the command to publish (e.g., 'fix-bug').
    """
    try:
        registry_path = cmds_sdk.publish_command(name)
        return {
            "success": True, 
            "registry_path": str(registry_path), 
            "status": "PUBLISHED",
            "message": f"Command '{name}' published to registry. Remember to commit changes in gemini-common-config."
        }
    except Exception as e:
        logger.error(f"Error publishing command: {e}")
        return {"error": str(e)}

@mcp.tool()
async def get_slash_command(name: str) -> dict[str, Any]:
    """
    Retrieve the full definition of a slash command.
    
    Args:
        name: The name of the command to retrieve.
    """
    try:
        command = cmds_sdk.get_command(name)
        if command:
            return {"name": name, "definition": command}
        return {"error": f"Command '{name}' not found."}
    except Exception as e:
        logger.error(f"Error getting command: {e}")
        return {"error": str(e)}

@mcp.tool()
async def list_mcp_servers(scope: str = "user") -> dict[str, Any]:
    """
    List all registered MCP servers for a given scope.
    
    Args:
        scope: The configuration scope ('user' or 'project').
    """
    try:
        servers = mcp_sdk.list_mcp_servers(scope)
        return {"scope": scope, "servers": servers}
    except Exception as e:
        logger.error(f"Error listing MCP servers: {e}")
        return {"error": str(e)}

@mcp.tool()
async def list_slash_commands(filter_pattern: Optional[str] = None) -> dict[str, Any]:
    """
    List all available slash commands and their status.
    
    Args:
        filter_pattern: Optional shell-style wildcard pattern to filter by name (e.g. "commit*").

    Note: When presenting these to the user, it is recommended to use the following 'Icon [space] Scope Name' format for clarity:
    - 👤 User
    - ☁️ Registry
    - 🏠 Project
    """
    try:
        results = cmds_sdk.list_commands(filter_pattern=filter_pattern)
        return {"commands": results}
    except Exception as e:
        return {"error": str(e)}

@mcp.tool()
async def add_context_path(path: str) -> dict[str, Any]:
    """Add a directory to the Gemini context paths."""
    try:
        config_path = settings_sdk.add_include_directory(path)
        return {
            "success": True,
            "config_file": str(config_path),
            "added_path": path,
            "tip": "Run '/dir add <path>' in Gemini to apply instantly."
        }
    except Exception as e:
        return {"error": str(e)}

@mcp.tool()
async def check_mcp_server_startup(command: str, args: Optional[list[str]] = None) -> dict[str, Any]:
    """
    Smoke test an MCP server command to see if it starts up correctly (STDIO).
    
    This is the best way to verify if an MCP server command is working or not if you've 
    already confirmed that it's registered with the agent (e.g. via 'gemini mcp list') 
    and you are seeing it listed with an unhealthy status (e.g. Disconnected).
    
    If you reference an MCP tool that the agent cannot find, first check the list of 
    registered MCP servers. If one reports unhealth, invoke this tool to diagnose the
    startup issue.
    
    Args:
        command: The command to execute (e.g., 'uv', 'python', 'my-mcp-server').
        args: Optional list of arguments for the command.
    """
    try:
        full_cmd = [command] + (args or [])
        return mcp_sdk.check_mcp_startup(full_cmd)
    except Exception as e:
        return {"error": str(e)}

@mcp.resource("aicfg://commands")
async def commands_resource() -> str:
    """List of all slash commands as a JSON resource."""
    results = cmds_sdk.list_commands()
    return json.dumps(results, indent=2)

def run_server():
    mcp.run()

if __name__ == "__main__":
    run_server()