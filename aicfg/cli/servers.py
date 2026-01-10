import click
from rich import print as rprint
from rich.table import Table
from aicfg.sdk import mcp_setup

@click.group(name="mcp")
def mcp_servers():
    """Manage MCP servers."""
    pass

@mcp_servers.command("add")
@click.option("--name", help="Name for the server")
@click.option("--path", help="Local repository path")
@click.option("--command", help="Existing command name")
@click.option("--url", help="Server URL for remote servers")
@click.option("--self", "is_self", is_flag=True, help="Register aicfg itself")
@click.option("--scope", type=click.Choice(["user", "project"]), default="user", help="Where to save")
@click.option("--args", help="CLI arguments for the server")
def add_mcp(name, path, command, url, is_self, scope, args):
    """Register a new MCP server."""
    try:
        result = mcp_setup.register_mcp(
            name=name, path=path, command=command, url=url, 
            is_self=is_self, scope=scope, args=args
        )
        rprint(f"[green]Registered[/green] '{result['name']}' in {result['path']}")
    except Exception as e:
        rprint(f"[red]Error:[/red] {e}")

@mcp_servers.command("remove")
@click.argument("name")
@click.option("--scope", type=click.Choice(["user", "project"]), default="user")
def remove_mcp(name, scope):
    """Remove an MCP server."""
    try:
        path, success = mcp_setup.remove_mcp_server(name, scope)
        rprint(f"[green]Removed[/green] '{name}' from {path}")
    except Exception as e:
        rprint(f"[red]Error:[/red] {e}")

@mcp_servers.command("list")
@click.option("--scope", type=click.Choice(["user", "project"]), default="user")
def list_mcp(scope):
    """List registered MCP servers."""
    servers = mcp_setup.list_mcp_servers(scope)
    table = Table(title=f"MCP Servers ({scope})")
    table.add_column("Name", style="cyan")
    table.add_column("Command/URL", style="green")
    
    for name in sorted(servers.keys()):
        cfg = servers[name]
        cmd_url = cfg.get("url") or cfg.get("command")
        table.add_row(name, cmd_url)
    rprint(table)

@mcp_servers.command("check-startup")
@click.argument("command")
@click.argument("args", nargs=-1)
def check_startup(command, args):
    """
    Check if an MCP server command starts up correctly (STDIO).
    
    Pipes a JSON-RPC initialize request to the command and checks for a valid response.
    Use this to diagnose 'disconnected' or unhealthy servers.
    """
    import json
    import sys
    
    full_cmd = [command] + list(args)
    rprint(f"[dim]Testing command: {' '.join(full_cmd)}[/dim]", file=sys.stderr)
    
    result = mcp_setup.check_mcp_startup(full_cmd)
    
    if result["success"]:
        rprint("[green]Success![/green] Server responded correctly.", file=sys.stderr)
        click.echo(json.dumps(result["response"], indent=2))
    else:
        rprint("[red]Failed![/red] Server did not respond correctly.", file=sys.stderr)
        click.echo(json.dumps(result, indent=2))
        sys.exit(1)
