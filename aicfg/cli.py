import click
from aicfg.cli_cmds import cmds
from aicfg.cli_settings import paths, context_files, settings
from aicfg.cli_mcp import register

@click.group()
def cli():
    """
    AI Config Manager (aicfg)
    
    Manage your Gemini configuration and slash commands repository.
    """
    pass

cli.add_command(cmds)
cli.add_command(paths)
cli.add_command(context_files)
cli.add_command(settings)
cli.add_command(register)

if __name__ == "__main__":
    cli()
