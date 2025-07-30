import uvicorn
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
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        lifespan="on",
        log_level="critical",
        access_log=False,
    )
    # print("Starting microservice server ")
    # asyncio.run(app.start())
