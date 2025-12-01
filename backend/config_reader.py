from typing import AsyncGenerator
from contextlib import AsyncExitStack, asynccontextmanager
from pathlib import Path
import logging
import asyncio

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

from aiogram import Bot, Dispatcher
from aiogram.exceptions import TelegramRetryAfter
from fastapi import FastAPI
from tortoise import Tortoise

ROOT_DIR = Path(__file__).parent.parent

logging.root.setLevel(logging.NOTSET)
logging.basicConfig(level=logging.INFO)
logging.getLogger("uvicorn.access").setLevel(logging.INFO)
logging.getLogger("uvicorn.error").setLevel(logging.INFO)
logging.getLogger("fastapi").setLevel(logging.INFO)
logger = logging.getLogger(__name__)


class Config(BaseSettings):
    """Gets .env values"""

    BOT_TOKEN: SecretStr
    DB_URL: SecretStr
    WEBHOOK_URL: str
    WEBHOOK_PATH: str
    WEBAPP_URL: str
    APP_HOST: str
    APP_PORT: int
    ADMIN_ID: int
    model_config = SettingsConfigDict(
        env_file=ROOT_DIR / "backend" / ".env", env_file_encoding="utf-8"
    )


config = Config()

bot = Bot(token=config.BOT_TOKEN.get_secret_value())
dp = Dispatcher(bot=bot)

TORTOISE_ORM = {
    "connections": {"default": config.DB_URL.get_secret_value()},
    "apps": {
        "models": {
            "models": [
                "aerich.models",
                "db.models.user",
                "db.models.flag",
                "db.models.match",
            ],
            "default_connection": "default",
        },
    },
}


async def set_webhook_safe(bot: Bot, url: str):
    """Sets webhook"""
    await bot.delete_webhook()
    while True:
        try:
            await bot.set_webhook(
                url=url,
                allowed_updates=dp.resolve_used_update_types(),
                drop_pending_updates=True,
            )
            logger.info("Webhook set successfully at %s", url)
            break
        except TelegramRetryAfter:
            logger.warning("Retry after %s seconds due to Telegram rate limit", 1)
            await asyncio.sleep(2000)
        except Exception:
            logger.exception("Failed to set webhook!")
            raise


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncGenerator[None, None]:
    """Starts lifespan"""
    logger.info("Starting application lifespan...")
    async with AsyncExitStack() as stack:
        await set_webhook_safe(bot, f"{config.WEBHOOK_URL.rstrip('/')}/webhook")

        await Tortoise.init(TORTOISE_ORM)
        stack.push_async_callback(Tortoise.close_connections)
        logger.info("Tortoise ORM initialized.")

        stack.push_async_callback(bot.session.close)
        logger.info("Bot session cleanup registered.")

        yield

    logger.info("Application lifespan finished.")


app = FastAPI(lifespan=lifespan)
