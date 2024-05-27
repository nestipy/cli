from typing import Annotated

from nestipy.common import Controller, Get, Post, Put, Delete
from nestipy.ioc import Inject, Body, Param

from app_service import AppService


@Controller()
class AppController:
    service: Annotated[AppService, Inject()]

    @Get()
    async def get(self) -> str:
        return await self.service.get()

    @Post()
    async def post(self, data: Annotated[dict, Body()]) -> str:
        return await self.service.post(data=data)

    @Put('/{app_id}')
    async def put(self, app_id: Annotated[int, Param('app_id')], data: Annotated[dict, Body()]) -> str:
        return await self.service.put(id_=app_id, data=data)

    @Delete('/{app_id}')
    async def delete(self, app_id: Annotated[int, Param('app_id')]) -> None:
        await self.service.delete(id_=app_id)
