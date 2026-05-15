from typing import Annotated, Awaitable, Union

from nestipy_db.db_module import uuid
from nestipy_jwt import JwtService

from nestipy.common import CanActivate, Injectable
from nestipy.common.logger import logger
from nestipy.core import ExecutionContext
from nestipy.ioc import Inject
from nestipy.metadata import Reflector
from src.user.user_model import User

from .auth_util import PUBLIC


@Injectable()
class AuthGuard(CanActivate):
    jwt_service: Annotated[JwtService, Inject()]

    async def can_activate(
        self, context: "ExecutionContext"
    ) -> Union[Awaitable[bool], bool]:
        is_public = self.is_public_route(context)
        if is_public:
            return True

        # extract user and put inside request
        token = self.extract_token(context)
        if not token:
            logger.info("[AuthGuard] Unauthorized: no token found")
            return False
        result = self.jwt_service.verify(token)
        if not result:
            logger.info("[AuthGuard] Unauthorized: invalid token")
            return False
        user = await User.query.filter(id=uuid.UUID(result["id"])).first()
        if not user:
            logger.info("[AuthGuard] Unauthorized: user not found")
            return False

        self.set_user(context, user)
        return True

    def is_public_route(self, context: "ExecutionContext") -> bool:
        http_context = context.switch_to_http()
        return Reflector.get_metadata(
            http_context.get_class(), PUBLIC, False
        ) or Reflector.get_metadata(http_context.get_handler(), PUBLIC, False)

    def extract_token(self, context: "ExecutionContext") -> str | None:
        http_context = context.switch_to_http()
        request = http_context.get_request()
        return request.headers.get("authorization", "").replace("Bearer ", "")

    def set_user(self, context: "ExecutionContext", user: User) -> None:
        http_context = context.switch_to_http()
        request = http_context.get_request()
        request.user = user
