from nestipy.core import NestipyFactory
from nestipy.microservice import MicroserviceOption, Transport

from app_module import AppModule

app = NestipyFactory.create_microservice(
    AppModule,
    [
        MicroserviceOption(
            transport=Transport.TCP,
        )
    ],
)
# app.start_all_microservices()
if __name__ == "__main__":
    app.listen(
        interface="asgi",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="critical",
        access_log=False,
    ).serve()
    # print("Starting microservice server ")
    # asyncio.run(app.start())
