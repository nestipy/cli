import os

from granian.constants import Interfaces
from nestipy.common import logger, session
from nestipy.core import NestipyFactory

from src.app_module import AppModule

app = NestipyFactory.create(AppModule)

# minijinja view engine for the Inertia root template (views/index.html)
app.set_base_view_dir(os.path.join(os.path.dirname(__file__), "views"))

# session is required for Inertia flash messages / validation errors
app.use(session())


@app.on_startup
async def startup():
    logger.info("[APP] Starting up ...")


@app.on_shutdown
async def shutdown():
    logger.info("[APP] Shutting down ...")


if __name__ == "__main__":
    app.listen(
        interface=Interfaces.ASGI,
        host="0.0.0.0",
        port=8000,
        reload=True,
    )
