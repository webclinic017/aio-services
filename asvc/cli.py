from __future__ import annotations

import logging
from typing import Literal

import click

from .runner import ServiceRunner
from .utils.imports import import_from_string


@click.group()
def cli() -> None:
    pass


@cli.command(help="Run service")
@click.argument("runner")
@click.option("--log-level", default="info")
@click.option("--use-uvloop", default="false")
def run(runner: str, log_level: str, use_uvloop: str) -> None:
    click.echo(f"Running [{runner}]...")
    logging.basicConfig(level=log_level.upper())
    r: ServiceRunner = import_from_string(runner)
    r.run(use_uvloop=(use_uvloop == "true"))


@cli.command()
@click.argument("runner")
def verify(runner: str) -> None:
    click.echo(f"Verifying runner [{runner}]...")
    r = import_from_string(runner)
    assert isinstance(r, ServiceRunner)
    click.echo("OK")


@cli.command()
@click.argument("service")
@click.option("--out", default="./asyncapi.json")
@click.option("--format", default="json")
def generate_docs(
    service: str, out: str = "./asyncapi.json", format: Literal["json", "yaml"] = "json"
):
    from .asyncapi.utils import get_async_api_spec, save_async_api_to_file

    svc = import_from_string(service)
    spec = get_async_api_spec(svc)
    save_async_api_to_file(spec, out, format)


if __name__ == "__main__":
    cli()
