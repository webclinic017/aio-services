from __future__ import annotations

import logging

import click
from typing_extensions import Literal

from .runner import ServiceRunner
from .service import Service
from .utils.imports import import_from_string


@click.group()
def cli() -> None:
    pass


@cli.command(help="Run service")
@click.argument("service_or_runner")
@click.option("--log-level", default="info")
@click.option("--use-uvloop", default="false")
def run(service_or_runner: str, log_level: str, use_uvloop: str) -> None:
    click.echo(f"Running [{service_or_runner}]...")
    logging.basicConfig(level=log_level.upper())
    obj = import_from_string(service_or_runner)
    if isinstance(obj, Service):
        obj = ServiceRunner([obj])
    obj.run(use_uvloop=(use_uvloop == "true"))


@cli.command(help="Watch and reload on files change")
@click.argument("service_or_runner")
@click.option("--log-level", default="info")
@click.option("--use-uvloop", default="false")
@click.option("--directory", default=".")
def watch(service_or_runner: str, log_level: str, use_uvloop: str, directory: str):
    from watchfiles import run_process

    click.echo(f"Watching [{service_or_runner}]...")
    logging.basicConfig(level=log_level.upper())
    obj = import_from_string(service_or_runner)
    if isinstance(obj, Service):
        obj = ServiceRunner([obj])

    def _callback(changes):
        click.secho(f"Changes detected: {changes}")

    run_process(
        directory,
        target=obj.run,
        kwargs={"use_uvloop": (use_uvloop == "true")},
        callback=_callback,
    )


@cli.command()
@click.argument("service")
def verify(service: str) -> None:
    click.echo(f"Verifying service [{service}]...")
    s = import_from_string(service)
    assert isinstance(s, Service)
    click.echo("OK")


@cli.command()
@click.argument("service")
@click.option("--out", default="./asyncapi.json")
@click.option("--format", default="json")
def generate_docs(
    service: str, out: str = "./asyncapi.json", format: Literal["json", "yaml"] = "json"
):
    from .asyncapi.generator import get_async_api_spec, save_async_api_to_file

    svc = import_from_string(service)
    assert isinstance(svc, Service), f"Service instance expected, got {type(svc)}"
    spec = get_async_api_spec(svc)
    save_async_api_to_file(spec, out, format)


if __name__ == "__main__":
    cli()
