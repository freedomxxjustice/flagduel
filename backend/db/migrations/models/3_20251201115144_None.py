from tortoise import BaseDBAsyncClient

RUN_IN_TRANSACTION = True


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        CREATE TABLE IF NOT EXISTS "aerich" (
    "id" SERIAL NOT NULL PRIMARY KEY,
    "version" VARCHAR(255) NOT NULL,
    "app" VARCHAR(100) NOT NULL,
    "content" JSONB NOT NULL
);
CREATE TABLE IF NOT EXISTS "users" (
    "id" BIGSERIAL NOT NULL PRIMARY KEY,
    "name" VARCHAR(255) NOT NULL,
    "total_score" INT NOT NULL DEFAULT 0,
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "energy" INT NOT NULL DEFAULT 5
);
CREATE TABLE IF NOT EXISTS "flags" (
    "id" SERIAL NOT NULL PRIMARY KEY,
    "name" VARCHAR(255) NOT NULL,
    "description" VARCHAR(255),
    "difficulty" DOUBLE PRECISION NOT NULL DEFAULT 0,
    "image" VARCHAR(255) NOT NULL,
    "emoji" VARCHAR(10),
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "total_shown" INT NOT NULL DEFAULT 0,
    "total_correct" INT NOT NULL DEFAULT 0,
    "category" VARCHAR(128) NOT NULL
);
CREATE TABLE IF NOT EXISTS "matches" (
    "id" UUID NOT NULL PRIMARY KEY,
    "inline_message_id" VARCHAR(255),
    "host_id" BIGINT NOT NULL,
    "participants" JSONB NOT NULL,
    "ready_players" JSONB NOT NULL,
    "questions" JSONB NOT NULL,
    "current_question_idx" INT NOT NULL DEFAULT 0,
    "scores" JSONB NOT NULL,
    "current_round_answers" JSONB NOT NULL,
    "is_started" BOOL NOT NULL DEFAULT False,
    "is_finished" BOOL NOT NULL DEFAULT False,
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS "idx_matches_inline__402ecf" ON "matches" ("inline_message_id");
CREATE TABLE IF NOT EXISTS "matchanswer" (
    "id" UUID NOT NULL PRIMARY KEY,
    "match_id" UUID NOT NULL REFERENCES "matches" ("id") ON DELETE CASCADE
);"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        """


MODELS_STATE = (
    "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"
)
