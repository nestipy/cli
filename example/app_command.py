from typing import Annotated

from nestipy.commander import BaseCommand, Command
from nestipy.ioc import Inject

from app_service import AppService


@Command(name='app', desc="Test app command")
class AppCommand(BaseCommand):
    service: Annotated[AppService, Inject()]

    async def run(self, context: dict):
        print("Hello ", await self.service.get())
