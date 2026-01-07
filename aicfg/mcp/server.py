import json
import logging
from typing import Any, Optional
from mcp.server.fastmcp import FastMCP
from aicfg.sdk import commands as cmds_sdk
from aicfg.sdk import settings as settings_sdk

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
async def list_slash_commands(filter_pattern: Optional[str] = None) -> dict[str, Any]:
    """
    List all available slash commands and their status.
    
    Args:
        filter_pattern: Optional shell-style wildcard pattern to filter by name (e.g. "commit*").
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

@mcp.resource("aicfg://commands")
async def commands_resource() -> str:
    """List of all slash commands as a JSON resource."""
    results = cmds_sdk.list_commands()
    return json.dumps(results, indent=2)

def run_server():
    mcp.run()

if __name__ == "__main__":
    run_server()