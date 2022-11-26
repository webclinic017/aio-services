from __future__ import annotations

from typing import TYPE_CHECKING

from asvc.middlewares.healthcheck import HealthCheckMiddleware

if TYPE_CHECKING:

    from fastapi import FastAPI

    from asvc import Service


def include_service(
    app: FastAPI,
    service: Service,
    add_health_endpoint: bool = False,
    path: str = "/healthz",
    response_class=None,
) -> None:
    app.on_event("startup")(service.start)
    app.on_event("shutdown")(service.stop)

    if add_health_endpoint:
        if response_class is None:
            from fastapi.responses import JSONResponse

            response_class = JSONResponse

        for m in service.broker.middlewares:
            if isinstance(m, HealthCheckMiddleware):

                async def _get_health_status():
                    """Return get broker connection status"""
                    status = await m.get_health_status()
                    return (
                        response_class({"status": "ok"})
                        if status
                        else response_class(
                            {"status": "Connection error"}, status_code=503
                        )
                    )

                app.add_api_route(
                    path=path, endpoint=_get_health_status, methods=["GET"]
                )
