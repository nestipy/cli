from nestipy.commander import BaseCommand, Command
from nestipy.ioc import Inject


@Command(name='test', desc="TEST command")
class TestCommand(BaseCommand):
    async def run(self):
        print(self.get_opt())
        print(self.get_arg())
        print("Hello from test")
