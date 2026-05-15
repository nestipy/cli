from typing import Annotated

from nestipy.common import Controller, Delete, Get, Post, Put, logger
from nestipy.ioc import Body, Inject, Param
from nestipy.openapi import ApiBearerAuth, ApiBody, ApiOkResponse
from src.auth.auth_util import AuthUser
from src.user.user_model import User

from .user_dto import CreateUserDto, UpdateUserDto
from .user_service import UserService


@ApiBearerAuth()
@ApiOkResponse()
@Controller("users")
class UserController:
    def __init__(self, user_service: Annotated[UserService, Inject()]) -> None:
        self.user_service = user_service

    @Get()
    async def list(self, user: Annotated[User, AuthUser()]) -> str:
        logger.info(user)
        return await self.user_service.list()

    @Post()
    @ApiBody(body=CreateUserDto)
    async def create(self, data: Annotated[CreateUserDto, Body()]) -> str:
        logger.info(data)
        return await self.user_service.create(data)

    @Put("/{id}")
    @ApiBody(body=UpdateUserDto)
    async def update(
        self,
        user_id: Annotated[int, Param("id")],
        data: Annotated[UpdateUserDto, Body()],
    ) -> str:
        return await self.user_service.update(user_id, data)

    @Delete("/{id}")
    async def delete(self, user_id: Annotated[int, Param("id")]) -> None:
        return await self.user_service.delete(user_id)
