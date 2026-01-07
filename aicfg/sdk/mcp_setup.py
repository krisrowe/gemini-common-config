from pathlib import Path
from aicfg.sdk.settings import USER_SETTINGS_PATH, PROJECT_SETTINGS_PATH, load_json, save_json

def register_server(command: str = "aicfg-mcp", scope: str = "user"):
    """
    Register aicfg-mcp in the active settings.json.
    """
    if scope == "project":
        if not PROJECT_SETTINGS_PATH:
            # Should generally not happen with current settings.py logic unless CWD fallback removed
            raise ValueError("Could not determine project settings path.")
        path = PROJECT_SETTINGS_PATH
    else:
        path = USER_SETTINGS_PATH

    data = load_json(path)
    
    if "mcpServers" not in data:
        data["mcpServers"] = {}
        
    server_config = {
        "command": command,
        "args": []
    }
    
    data["mcpServers"]["aicfg"] = server_config
    save_json(path, data)
    return path