from __future__ import annotations

from typing import TYPE_CHECKING

from aio_services.middlewares.healthcheck import HealthCheckMiddleware

if TYPE_CHECKING:
    from aiohttp.web import Application

    from aio_services import Service


def register_service(
    service: Service, app: Application, add_health_endpoint: bool = False
) -> None:
    app.on_startup.append(service.start)
    app.on_shutdown.append(service.stop)
    if add_health_endpoint:
        for m in service.broker.middlewares:
            if isinstance(m, HealthCheckMiddleware):
                # TODO
                break
        else:
            raise TypeError("HealthCheckMiddleware not found")
