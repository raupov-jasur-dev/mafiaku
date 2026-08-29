import logging
from aiogram import Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

from app.bot.middlewares.throttling import ThrottlingMiddleware
from app.bot.middlewares.auth import AuthMiddleware
from app.bot.handlers import (
    start,
    game,
    lobby,
    night,
    vote,
    profile,
    roles,
    settings as settings_handler,
    top,
    group_admin,
    admin
)

logger = logging.getLogger(__name__)

def create_dispatcher() -> Dispatcher:
    """Configures aiogram 3.x dispatcher with all routers and middlewares."""
    dp = Dispatcher(storage=MemoryStorage())

    # Middlewares
    dp.message.middleware(ThrottlingMiddleware())
    dp.callback_query.middleware(ThrottlingMiddleware())
    dp.message.middleware(AuthMiddleware())
    dp.callback_query.middleware(AuthMiddleware())

    # Register Handler Routers
    dp.include_router(start.router)
    dp.include_router(game.router)
    dp.include_router(lobby.router)
    dp.include_router(night.router)
    dp.include_router(vote.router)
    dp.include_router(profile.router)
    dp.include_router(roles.router)
    dp.include_router(settings_handler.router)
    dp.include_router(top.router)
    dp.include_router(group_admin.router)
    dp.include_router(admin.router)

    logger.info("Aiogram dispatcher created with all handlers successfully.")
    return dp
