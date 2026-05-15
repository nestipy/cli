from dataclasses import asdict
from typing import Annotated, cast

from nestipy.common import HttpException, Injectable
from nestipy.ioc import Inject
from nestipy_jwt import JwtService

from src.user.user_dto import CreateUserDto
from src.user.user_model import User
from src.user.user_service import UserService

from .auth_dto import AuthResponseDto, LoginDto, RegisterDto


@Injectable()
class AuthService:
    user_service: Annotated[UserService, Inject()]
    jwt_service: Annotated[JwtService, Inject()]

    async def login(self, data: LoginDto) -> AuthResponseDto:
        user = await self.user_service.get_by_email(data.email)
        if not user:
            raise HttpException(404, "User not found")
        if user.password != data.password:
            raise HttpException(403, "Invalid password")
        user_json = cast(User, user).model_dump(mode="json")
        token = self.jwt_service.generate_token(user_json)
        return AuthResponseDto(user=user_json, token=token)

    async def register(self, data: RegisterDto) -> AuthResponseDto:
        if data.password != data.confirm_password:
            raise HttpException(400, "Passwords do not match")
        user = await self.user_service.create(CreateUserDto(**asdict(data)))
        user_json = cast(User, user).model_dump(mode="json")
        token = self.jwt_service.generate_token(user_json)
        return AuthResponseDto(user=user_json, token=token)
