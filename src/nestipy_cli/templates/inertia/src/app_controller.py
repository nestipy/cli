from typing import Annotated

from nestipy.common import Controller, Get, Response
from nestipy.ioc import Inject, Res
from nestipy_inertia import InertiaResponse, defer, optional

from .app_service import AppService


@Controller()
class AppController:
    service: Annotated[AppService, Inject()]

    @Get()
    async def index(self, res: Annotated[InertiaResponse, Res()]) -> Response:
        return await res.inertia.render(
            "Index",
            {
                "message": self.service.greeting(),
                # only sent on a partial reload that requests it
                "details": optional(lambda: "Loaded on partial reload"),
                # excluded from first render, fetched right after load
                "stats": defer(self.service.stats),
            },
        )

    @Get("/about")
    async def about(self, res: Annotated[InertiaResponse, Res()]) -> Response:
        return await res.inertia.render("About", {"framework": "Nestipy + Inertia.js"})
