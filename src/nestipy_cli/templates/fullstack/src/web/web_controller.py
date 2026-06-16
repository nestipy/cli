from typing import Annotated

from nestipy.common import Controller, Get, Response
from nestipy.ioc import Res
from nestipy_inertia import InertiaResponse, defer, optional

from src.auth.auth_util import IsPublic


@IsPublic()
@Controller()
class HomeController:
    @Get()
    async def index(self, res: Annotated[InertiaResponse, Res()]) -> Response:
        return await res.inertia.render(
            "Index",
            {
                "message": "Welcome to Nestipy + Inertia.js",
                "details": optional(lambda: "Loaded on partial reload"),
                "stats": defer(lambda: {"users": 42, "online": 7}),
            },
        )

    @Get("/about")
    async def about(self, res: Annotated[InertiaResponse, Res()]) -> Response:
        return await res.inertia.render("About", {"framework": "Nestipy + Inertia.js"})
