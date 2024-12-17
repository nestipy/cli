from typing import Annotated

from nestipy.commander import BaseCommand, Command
from nestipy.ioc import Inject

from app_service import AppService


@Command(name='test', desc="Test app command")
class AppCommand(BaseCommand):
    service: Annotated[AppService, Inject()]

    async def run(self):
        print(self.get_opt())
        print("Hello ", await self.service.get())
