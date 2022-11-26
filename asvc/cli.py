from __future__ import annotations

import importlib
import logging

import aiorun
import click

from asvc.service import Service, ServiceGroup


def _import_service(path: str) -> Service | ServiceGroup:
    module_name, _, service_name = path.partition(":")
    try:
        module = importlib.import_module(module_name)
        service = getattr(module, service_name)
        assert isinstance(
            service, (Service, ServiceGroup)
        ), "Object must be instance of Service(Group)"
        return service
    except (AttributeError, ImportError) as e:
        click.echo(f"Service {service_name} not found in module {module_name}")
        click.echo(e)
        raise SystemExit(1)


@click.group()
def cli() -> None:
    pass


@cli.command(help="Run service")
@click.argument("service")
@click.option("--log-level", default="info")
@click.option("--use-uvloop", default="false")
def run(service: str, log_level: str, use_uvloop: str) -> None:
    click.echo(f"Running service [{service}]...")
    logging.basicConfig(level=log_level.upper())
    svc = _import_service(service)
    if svc:
        aiorun.run(
            svc.start(), shutdown_callback=svc.stop, use_uvloop=(use_uvloop == "true")
        )


@cli.command()
@click.argument("service")
def verify(service: str) -> None:
    click.echo(f"Verifying service [{service}]...")
    _import_service(service)
    click.echo("OK")


if __name__ == "__main__":
    cli()
