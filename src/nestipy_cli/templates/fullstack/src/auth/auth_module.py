from nestipy.common import Module
from src.user.user_module import UserModule

from .auth_controller import AuthController
from .auth_service import AuthService


@Module(providers=[AuthService], controllers=[AuthController], imports=[UserModule])
class AuthModule: ...
