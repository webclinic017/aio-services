from __future__ import annotations

from typing import TYPE_CHECKING

from aio_services.middlewares.healthcheck import HealthCheckMiddleware

if TYPE_CHECKING:

    from starlette.applications import Starlette
    from starlette.responses import JSONResponse

    from aio_services import Service


def register_service(
    service: Service,
    app: Starlette,
    add_health_endpoint: bool = False,
    endpoint: str = "/healthz",
    response_class=JSONResponse,
) -> None:
    app.on_event("startup")(service.start)
    app.on_event("shutdown")(service.stop)

    if add_health_endpoint:
        for m in service.broker.middlewares:
            if isinstance(m, HealthCheckMiddleware):

                async def _get_health_status():
                    """Return get broker connection status"""
                    status = m.get_health_status()
                    return (
                        response_class({"status": "ok"})
                        if status
                        else response_class(
                            {"status": "Connection error"}, status_code=503
                        )
                    )

                app.add_route(path=endpoint, methods=["GET"], route=_get_health_status)
