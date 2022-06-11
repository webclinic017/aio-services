# import aiorun
import click


try:
    import uvloop

    uvloop.install()
except ImportError:
    pass


@click.group()
def cli():
    pass


@cli.command()
@click.argument("app")
def run(app):
    click.echo(f"Running service [{app}]...")


@cli.command()
@click.argument("app")
def verify(app):
    click.echo(f"Veryfying service [{app}]...")
