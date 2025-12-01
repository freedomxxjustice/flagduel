from aiogram import Router
from . import game, common, payment

def setup_routers() -> Router:
    router = Router()
    router.include_router(game.router)
    router.include_router(common.router)
    router.include_router(payment.router)
    return router
