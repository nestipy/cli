from nestipy.common import Module
from nestipy.web import ActionsModule, ActionsOption

from app_controller import AppController
from app_service import AppService
from app_actions import AppActions


@Module(
    imports=[ActionsModule.for_root(ActionsOption(path="/_actions"))],
    controllers=[AppController],
    providers=[AppService, AppActions],
)
class AppModule: ...
