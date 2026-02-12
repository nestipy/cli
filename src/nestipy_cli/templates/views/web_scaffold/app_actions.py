from nestipy.common import Injectable
from nestipy.web import action


@Injectable()
class AppActions:
    @action()
    async def hello(self, name: str = "Nestipy") -> str:
        return f"Hello, {name}!"
