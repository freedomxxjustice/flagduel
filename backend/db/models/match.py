from tortoise import fields
from tortoise.models import Model


class Match(Model):
    id = fields.UUIDField(pk=True)
    inline_message_id = fields.CharField(max_length=255, null=True, index=True) 
    host_id = fields.BigIntField() 
    participants = fields.JSONField(default=list)
    ready_players = fields.JSONField(default=list)
    questions = fields.JSONField(default=list) 
    current_question_idx = fields.IntField(default=0)
    scores = fields.JSONField(default={}) 
    current_round_answers = fields.JSONField(default={}) 
    is_started = fields.BooleanField(default=False)
    is_finished = fields.BooleanField(default=False)
    created_at = fields.DatetimeField(auto_now_add=True)

    class Meta:
        table = "matches"

class MatchAnswer(Model):
    id = fields.UUIDField(pk=True)
    match = fields.ForeignKeyField("models.Match", related_name="answers")

