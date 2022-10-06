from __future__ import annotations

import importlib
import logging

import aiorun
import click

from aio_services.service import Service

try:
    import uvloop

    uvloop.install()
except ImportError:
    uvloop = None


def _import_service(path: str) -> Service | None:
    module_name, _, service_name = path.partition(":")
    try:
        module = importlib.import_module(module_name)
        service = getattr(module, service_name)
        assert isinstance(service, Service), "Object must be instance of Service"
        return service
    except (AttributeError, ImportError) as e:
        click.echo(f"Service {service_name} not found in module {module_name}")
        click.echo(e)
        return None


@click.group()
def cli() -> None:
    pass


@cli.command(help="Run service")
@click.argument("service")
@click.option("--log-level", default="info")
def run(service: str, log_level: str) -> None:
    click.echo(f"Running service [{service}]...")
    logging.basicConfig(level=log_level.upper())
    service = _import_service(service)
    if service:
        aiorun.run(service.start(), shutdown_callback=service.stop)


@cli.command()
@click.argument("service")
def verify(service: str) -> None:
    click.echo(f"Verifying service [{service}]...")
    _import_service(service)
    click.echo("OK")


if __name__ == "__main__":
    cli()
