from nestipy_db import DbModule

from nestipy.common import Module

from .user_controller import UserController
from .user_model import Profile, User
from .user_service import UserService


@Module(
    providers=[UserService],
    controllers=[UserController],
    imports=[DbModule.for_feature(User, Profile)],
    exports=[UserService],
)
class UserModule: ...
