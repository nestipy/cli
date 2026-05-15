from typing import Optional

from pydantic import BaseModel, Field


class CreateUserDto(BaseModel):
    name: str
    email: str
    password: str


class UpdateUserDto(BaseModel):
    name: Optional[str] = Field(default=None)
    email: Optional[str] = Field(default=None)
    password: Optional[str] = Field(default=None)
