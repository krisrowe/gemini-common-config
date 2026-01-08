import click
from aicfg.cli.commands import cmds
from aicfg.cli.settings import settings
from aicfg.cli.servers import mcp_servers

@click.group()
def cli():
    """AI Config Manager (aicfg)"""
    pass

cli.add_command(cmds)
cli.add_command(settings)
cli.add_command(mcp_servers)

if __name__ == "__main__":
    cli()