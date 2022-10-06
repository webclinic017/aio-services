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
    route=None,
) -> None:
    app.on_event("startup")(service.start)
    app.on_event("shutdown")(service.stop)

    if add_health_endpoint:
        if route:
            get_health_status = route
        else:
            for m in service.broker.middlewares:
                if isinstance(m, HealthCheckMiddleware):

                    async def _get_health_status():
                        """Return get broker connection status"""
                        status = m.get_health_status()
                        return (
                            JSONResponse({"status": "ok"})
                            if status
                            else JSONResponse(
                                {"status": "Connection error"}, status_code=503
                            )
                        )

                    get_health_status = _get_health_status
                    break
            else:
                raise ValueError("HealthCheckMiddleware not found")
        app.add_route(path=endpoint, methods=["GET"], route=get_health_status)
