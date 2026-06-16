import os

from nestipy.common import Module
from nestipy_inertia import InertiaModule, InertiaConfig

from .app_controller import AppController
from .app_service import AppService


@Module(
    imports=[
        InertiaModule.register(
            InertiaConfig(root_dir=os.path.join(os.getcwd(), "inertia"))
        )
    ],
    controllers=[AppController],
    providers=[AppService],
)
class AppModule: ...
