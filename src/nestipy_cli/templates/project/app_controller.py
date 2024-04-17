from nestipy.common import Controller, Get, Post, Put, Delete
from nestipy.types_ import Inject, Body, Params

from app_service import AppService


@Controller()
class AppController:
    service: Inject[AppService]

    @Get()
    async def get(self) -> str:
        return await self.service.get()

    @Post()
    async def post(self, data: Body[dict]) -> str:
        return await self.service.post(data=data)

    @Put('/{user_id}')
    async def put(self, user_id: Params[int], data: Body[dict]) -> str:
        return await self.service.put(id_=user_id, data=data)

    @Delete('/{user_id}')
    async def delete(self, user_id: Params[int]) -> None:
        await self.service.delete(id_=user_id)
