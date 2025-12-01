import logging
from fastapi import Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn
from aiogram.types import (
    Update,
)
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from bot.handlers import setup_routers as setup_bot_routers
from api import setup_routers as setup_api_routers

from config_reader import config, dp, bot, app


limiter = Limiter(key_func=get_remote_address)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


@app.get("/ping")
async def ping():
    return {"msg": "pong"}


app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://devapp.guessflags.space"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


dp.include_router(setup_bot_routers())
app.include_router(setup_api_routers())


@app.post(config.WEBHOOK_PATH)
async def webhook(request: Request) -> None:
    """Set web"""
    data = await request.json()
    update = Update.model_validate(data, context={"bot": bot})
    await dp.feed_update(bot, update)


@app.exception_handler(Exception)
async def global_exception_handler(_: Request, exc: Exception):
    """Handle exceptions"""
    logging.error("Unhandled error: %s", exc)
    return JSONResponse(status_code=500, content={"detail": "Internal Server Error"})


if __name__ == "__main__":
    uvicorn.run(app, host=config.APP_HOST, port=config.APP_PORT)
