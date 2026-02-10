from nestipy.core import NestipyFactory

from app_module import AppModule

app = NestipyFactory.create(AppModule)

if __name__ == "__main__":
    app.listen(
        "main:app",
        interface="asgi",
        host="[IP_ADDRESS]",
        port=8000,
        reload=True,
        log_level="critical",
        access_log=False,
    ).serve()
