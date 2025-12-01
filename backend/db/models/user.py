from tortoise import fields
from tortoise.models import Model
from tortoise.contrib.pydantic import pydantic_model_creator

class User(Model):
    id = fields.BigIntField(primary_key=True, unique=True)
    name = fields.CharField(max_length=255)
    total_score = fields.IntField(default=0)
    created_at = fields.DatetimeField(auto_now_add=True)
    energy = fields.IntField(default=5)

    class Meta:
        table = "users"

UserSchema = pydantic_model_creator(User)
