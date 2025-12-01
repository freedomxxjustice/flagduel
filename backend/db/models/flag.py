from tortoise import fields
from tortoise.models import Model
from tortoise.contrib.pydantic import pydantic_model_creator


class Flag(Model):
    id = fields.IntField(pk=True)
    name = fields.CharField(255)
    description = fields.CharField(255, null=True)
    difficulty = fields.FloatField(default=0.0)
    image = fields.CharField(255)
    emoji = fields.CharField(10, null=True)
    created_at = fields.DatetimeField(auto_now_add=True)
    total_shown = fields.IntField(default=0)
    total_correct = fields.IntField(default=0)
    category = fields.CharField(128, null=False)

    class Meta:
        table = "flags"


FlagSchema = pydantic_model_creator(Flag)
