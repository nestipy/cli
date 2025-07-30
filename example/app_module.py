from nestipy.common import Module

from app_controller import AppController
from app_service import AppService
from app_command import AppCommand


@Module(controllers=[AppController], providers=[AppService, AppCommand])
class AppModule: ...
