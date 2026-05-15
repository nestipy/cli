import uuid
from dataclasses import asdict

from nestipy.common import Injectable, logger

from .user_dto import CreateUserDto, UpdateUserDto
from .user_model import User


@Injectable()
class UserService:
    async def list(self):
        users = await User.query.all()
        return [u.model_dump() for u in users]

    async def create(self, data: CreateUserDto):
        return await User.query.create(**data.model_dump(mode="json"))

    async def update(self, id: str, data: UpdateUserDto):
        json_data = data.model_dump(mode="json", exclude_none=True)
        user = await User.query.get(id=uuid.UUID(id))
        await user.update(**json_data)
        return {"status": "Updated"}

    async def delete(self, id: int):
        user = await User.query.get(id=uuid.UUID(id))
        await user.delete()
        return {"status": "Deleted"}

    async def get_by_email(self, email: str):
        return await User.query.where(email == email).first()
