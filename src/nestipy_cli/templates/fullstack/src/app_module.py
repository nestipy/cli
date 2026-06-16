import os
from typing import Annotated

from nestipy_db import AdminConfig, DbConfig, DbModule
from nestipy_inertia import InertiaConfig, InertiaModule
from nestipy_jwt import JwtModule, JwtOption

from nestipy.common import Module
from nestipy.common.config import ConfigModule, ConfigService
from nestipy.core.constant import AppKey
from nestipy.ioc import Inject, ModuleProviderDict

from .app_service import AppService
from .auth.auth_guard import AuthGuard
from .auth.auth_module import AuthModule
from .user.user_module import UserModule
from .web.web_controller import HomeController


def get_jwt_option(env: Annotated[ConfigService, Inject()]) -> JwtOption:
    return JwtOption(secret=env.get("JWT_SECRET", "your_generated_long_secret_here"))


@Module(
    controllers=[HomeController],
    providers=[
        ModuleProviderDict(token=AppKey.APP_GUARD, use_class=AuthGuard),
        AppService,
    ],
    imports=[
        ConfigModule.for_root(),
        DbModule.for_root(
            DbConfig(
                url="sqlite:///db.sqlite",
                models=[],
                admin=AdminConfig(enable=True, url="/admin", panel_title="DB Admin"),
            )
        ),
        JwtModule.for_root_async(
            factory=get_jwt_option,
            inject=[ConfigService],
        ),
        InertiaModule.register(
            InertiaConfig(root_dir=os.path.join(os.getcwd(), "inertia"))
        ),
        AuthModule,
        UserModule,
    ],
)
class AppModule: ...
