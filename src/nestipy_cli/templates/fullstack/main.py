import os

from granian.constants import Interfaces

from nestipy.common import logger
from nestipy.core import NestipyConfig, NestipyFactory
from nestipy.openapi import DocumentBuilder, SwaggerModule
from src.app_module import AppModule

document = (
    DocumentBuilder()
    .set_title("Nestipy API")
    .set_description(
        "Nestipy is a Python framework inspired by NestJS and built on top of FastAPI or Blacksheep"
    )
    .set_version("1.0")
    .add_bearer_auth()
    # .add_basic_auth()
    .build()
)

app = NestipyFactory.create(AppModule, config=NestipyConfig(profile=True))
SwaggerModule.setup("docs", app, document)
app.use_static_assets(os.path.join(os.path.dirname(__file__), "public"))


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
