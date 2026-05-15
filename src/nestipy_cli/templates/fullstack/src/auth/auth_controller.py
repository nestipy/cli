from typing import Annotated

from nestipy.common import Controller, Post
from nestipy.ioc import Body, Inject
from nestipy.openapi import ApiBody, ApiOkResponse

from .auth_dto import AuthResponseDto, LoginDto, RegisterDto
from .auth_service import AuthService
from .auth_util import IsPublic


@ApiOkResponse(schema=AuthResponseDto)
@IsPublic()
@Controller("auth")
class AuthController:
    auth_service: Annotated[AuthService, Inject()]

    @ApiBody(body=LoginDto)
    @Post("/login")
    async def login(self, data: Annotated[LoginDto, Body()]) -> str:
        return await self.auth_service.login(data)

    @ApiBody(body=RegisterDto)
    @Post("/register")
    async def register(self, data: Annotated[RegisterDto, Body()]) -> str:
        return await self.auth_service.register(data)
