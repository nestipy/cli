from pydantic import BaseModel


class LoginDto(BaseModel):
    email: str
    password: str


class RegisterDto(LoginDto):
    confirm_password: str
    name: str


class AuthResponseDto(BaseModel):
    user: dict
    token: str
