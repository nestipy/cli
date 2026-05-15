from uuid import uuid4

import edgy
from edgy.core.signals import post_save
from nestipy_db import BaseModel, Model

from nestipy.common import logger


@Model()
class User(BaseModel):
    id = edgy.UUIDField(primary_key=True, default=uuid4, editable=False)
    name = edgy.CharField(max_length=255)
    email = edgy.EmailField(max_length=70, unique=True)
    password = edgy.CharField(max_length=255)
    created_at = edgy.DateTimeField(auto_now_add=True)
    updated_at = edgy.DateTimeField(auto_now=True)


@Model()
class Profile(BaseModel):
    user = edgy.OneToOne(User, on_delete=edgy.CASCADE, related_name="profile")


@post_save.connect_via(User)
async def create_profile(sender, instance, **kwargs):
    logger.info("Creation de profil ...")
    await Profile.query.create(user=kwargs["model_instance"])
