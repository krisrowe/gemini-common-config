import click
from rich import print as rprint
from aicfg.sdk import mcp_setup

@click.command("register-mcp-server")
@click.option("--scope", type=click.Choice(["user", "project"]), default="user", help="Scope for registration (default: user)")
def register(scope):
    """
    Register the aicfg MCP server in Gemini settings.
    
    This enables Gemini to manage configuration via natural language.
    """
    try:
        # Check if aicfg-mcp is available
        import shutil
        if not shutil.which("aicfg-mcp"):
            rprint("[yellow]Warning:[/yellow] 'aicfg-mcp' not found in PATH. Ensure you installed with pipx ensurepath.")
            
        config_path = mcp_setup.register_server("aicfg-mcp", scope=scope)
        rprint(f"[green]Registered[/green] MCP server 'aicfg' in {config_path} ({scope} scope)")
        rprint("[blue]Tip:[/blue] Run [bold]gemini mcp list[/bold] to verify connection.")
        rprint("You may need to restart Gemini if it's running.")
    except Exception as e:
        rprint(f"[red]Error registering server:[/red] {e}")
