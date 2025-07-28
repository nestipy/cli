import asyncio
import code
import inspect
from types import CodeType
from typing import Type, Optional, TYPE_CHECKING

from .style import CliStyle

echo = CliStyle()
if TYPE_CHECKING:
    from nestipy.core import NestipyApplication


class REPL(code.InteractiveConsole):
    def __init__(self, app: "NestipyApplication"):
        self.app = app
        self.context = {
            'app': self.app,
            'debug': self.debug,
            'methods': self.methods,
            'get': self.get,
            '__builtins__': __builtins__,
            '__name__': __name__,
            '__doc__': None
        }
        self.loop = asyncio.get_event_loop()
        self.loop.run_until_complete(self._load_context())
        super().__init__(locals=self.context)

    def get(self, t: Type):
        return self.loop.run_until_complete(self.app.get(t))

    @classmethod
    def methods(cls, c: Type):
        if inspect.isclass(c):
            echo.info(f'{c.__name__}:')
            for name, func in inspect.getmembers(c, predicate=lambda a: inspect.isfunction(a) or inspect.ismethod(a)):
                if not name.startswith('_'):
                    echo.info("  ◻ {}".format(name))

    def debug(self, module: Type = None, level: str = "  ") -> None:
        from nestipy.dynamic_module import DynamicModule
        if module is None:
            module = getattr(self.app, "_root_module", None)
            if module is None:
                raise Exception("Module not defined")
        metadata: Optional[dict] = getattr(module, '__reflect__metadata__')
        echo.info(f"{level}{module.__name__}:")
        if metadata and metadata.get('_is_module_'):
            imports = metadata['imports']
            if imports:
                echo.info("  - Imports:")
                for imp in imports:
                    if isinstance(imp, DynamicModule):
                        echo.info(f"  {level}  ◻ {imp.module.__name__}")
                        # self.debug(imp.module, level=f"  {level}")
                    elif inspect.isclass(imp):
                        echo.info(f"  {level}  ◻ {imp.__name__}")
                        # self.debug(imp, level=f"  {level}")
            controllers = metadata['controllers']
            if controllers:
                echo.info("  - Controllers:")
                for controller in controllers:
                    echo.info("    ◻ {}".format(controller.__name__))
            providers = metadata['providers']
            if providers:
                echo.info("  - Providers:")
                for p in providers:
                    if inspect.isclass(p):
                        echo.info("    ◻ {}".format(p.__name__))
                    else:
                        token = p.token
                        if inspect.isclass(token):
                            echo.info("    ◻ {}".format(token.__name__))
                        else:
                            echo.info("    ◻ {}".format(token))

    async def _load_context(self):
        from nestipy.core import DiscoverService
        await self.app.ready()
        discover: DiscoverService = await self.app.get(DiscoverService)
        all_modules: list[object] = discover.get_all_module()
        all_controllers: list[object] = discover.get_all_controller()
        all_providers: list[object] = discover.get_all_provider()
        for m in all_modules:
            self.context[m.__class__.__name__] = m.__class__
        for c in all_controllers:
            self.context[c.__class__.__name__] = c.__class__
        for p in all_providers:
            self.context[p.__class__.__name__] = p.__class__

    def runsource(self, source, filename="<input>", symbol="single"):
        await_key = "await "
        if await_key in source.strip():
            wrapped_code = source.replace(await_key, "")
            if source.strip().startswith(await_key):
                try:
                    result = self.loop.run_until_complete(eval(wrapped_code, self.context))
                    self.context["_"] = result
                    super().runsource("_", filename, symbol)
                except Exception as e:
                    echo.error(f"Error: {e}")
            else:
                super().runsource(wrapped_code, filename, symbol)
        else:
            super().runsource(source, filename, symbol)

    def runcode(self, src: CodeType):
        super().runcode(src)
        values = list(self.context.values())
        keys = list(self.context.keys())
        last_value = values[-1]
        last_key = keys[-1]
        if inspect.iscoroutine(last_value):
            try:
                self.context[last_key] = self.loop.run_until_complete(last_value)
            except Exception as e:
                echo.error(f"Error: {e}")
