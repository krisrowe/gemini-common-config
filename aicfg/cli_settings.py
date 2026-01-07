import click
from rich import print as rprint
from rich.table import Table
from aicfg.sdk import settings as sdk

@click.group()
def paths():
    """Manage context.includeDirectories."""
    pass

@paths.command("list")
def list_paths():
    path, dirs = sdk.get_include_directories()
    rprint(f"[bold]Active Config:[/bold] {path}")
    if not dirs:
        rprint("[yellow]No paths configured.[/yellow]")
        return
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Path")
    for d in dirs: table.add_row(d)
    rprint(table)

@paths.command("add")
@click.argument("path_to_add")
def add_path(path_to_add):
    config_path = sdk.add_include_directory(path_to_add)
    rprint(f"[green]Added[/green] '{path_to_add}' to {config_path}")
    rprint(f"[blue]Tip:[/blue] Run [bold]/dir add {path_to_add}[/bold] in Gemini to apply instantly.")

@paths.command("remove")
@click.argument("path_to_remove")
def remove_path(path_to_remove):
    config_path, removed = sdk.remove_include_directory(path_to_remove)
    if removed:
        rprint(f"[green]Removed[/green] '{path_to_remove}' from {config_path}")
        rprint(f"[blue]Tip:[/blue] Run [bold]/dir remove {path_to_remove}[/bold] in Gemini to apply instantly.")
    else:
        rprint(f"[red]Path '{path_to_remove}' not found in {config_path}[/red]")

@click.group(name="context-file-names")
def context_files():
    """Manage context.fileName."""
    pass

@context_files.command("list")
def list_context_files():
    path, files = sdk.get_context_files()
    rprint(f"[bold]Config:[/bold] {path}")
    if not files:
        rprint("[yellow]No context files configured.[/yellow]")
        return
    table = Table(show_header=True, header_style="bold cyan")
    table.add_column("File Name")
    for f in files: table.add_row(f)
    rprint(table)

@context_files.command("add")
@click.argument("filename")
def add_context_file(filename):
    path = sdk.add_context_file(filename)
    rprint(f"[green]Added[/green] '{filename}' to {path}")

@context_files.command("remove")
@click.argument("filename")
def remove_context_file(filename):
    path, removed = sdk.remove_context_file(filename)
    if removed:
        rprint(f"[green]Removed[/green] '{filename}' from {path}")
    else:
        rprint(f"[red]File '{filename}' not found in {path}[/red]")

@click.group()
def settings():
    """
    Manage aliased Gemini settings.
    
    This tool manages a curated subset of configuration options.
    For a full list of settings and their effects, see:
    https://geminicli.com/docs/get-started/configuration/
    """
    pass

@settings.command("list")
def list_settings():
    path, aliases, values = sdk.list_settings_aliases()
    rprint(f"[bold]Active Config:[/bold] {path}")
    table = Table(title="Setting Aliases")
    table.add_column("Alias", style="cyan")
    table.add_column("Path", style="dim")
    table.add_column("Value", style="green")
    for alias, info in aliases.items():
        val = values.get(alias)
        table.add_row(alias, info["path"], str(val) if val is not None else "[dim]not set[/dim]")
    rprint(table)

@settings.command("set")
@click.argument("alias")
@click.argument("value")
def set_setting(alias, value):
    try:
        path, typed_val, restart = sdk.set_setting_alias(alias, value)
        rprint(f"[green]Set[/green] {alias} = {typed_val}")
        if restart:
            rprint("[yellow]Note: You must [bold]/quit[/bold] and run [bold]gemini -r[/bold] to apply this change.[/yellow]")
    except ValueError as e:
        rprint(f"[red]Error:[/red] {e}")

@settings.command("get")
@click.argument("alias")
def get_setting(alias):
    try:
        path, val = sdk.get_setting_alias(alias)
        rprint(val)
    except ValueError as e:
        rprint(f"[red]Error:[/red] {e}")
