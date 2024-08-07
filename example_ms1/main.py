import uvicorn

from app_module import AppModule
from nestipy.core import NestipyFactory
from nestipy.microservice import MicroserviceOption, Transport, MicroserviceClientOption

app = NestipyFactory.create_microservice(
    AppModule, [
        MicroserviceOption(
            transport=Transport.REDIS,
            option=MicroserviceClientOption(
                host="localhost",
                port=6379
            )
        )
    ]
)
# app.start_all_microservices()
if __name__ == '__main__':
    uvicorn.run('main:app', host="0.0.0.0", port=8000, reload=True, lifespan="on", log_level="critical", access_log=False)
    # print("Starting microservice server ")
    # asyncio.run(app.start())
