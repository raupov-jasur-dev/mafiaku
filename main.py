import asyncio
import logging
import sys
import os
import uvicorn
from aiogram import Bot
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties

from app.core.config import settings
from app.core.constants import BOT_NAME
from app.database.session import init_db
from app.services.redis_service import redis_service
from app.bot.dispatcher import create_dispatcher
from app.bot.handlers.game_orchestrator import GameOrchestrator
from app.admin.api import app as fastapi_app, set_bot

# Configure logging
logging.basicConfig(
    level=logging.INFO if not settings.DEBUG else logging.DEBUG,
    format="%(asctime)s - [%(levelname)s] - %(name)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

async def run_bot_polling(bot: Bot):
    """Run polling with automatic recovery if Telegram/network errors stop the polling task."""
    dp = create_dispatcher()
    await GameOrchestrator.restore_active_games(bot)
    await bot.delete_webhook(drop_pending_updates=True)

    while True:
        try:
            logger.info("🤵🏻 %s (@%s) is now online and polling Telegram updates...", BOT_NAME, settings.BOT_USERNAME)
            await dp.start_polling(bot)
            # start_polling normally blocks until shutdown. If it returns, do not spin aggressively.
            await asyncio.sleep(1)
        except asyncio.CancelledError:
            raise
        except Exception:
            logger.exception("Telegram polling stopped unexpectedly; retrying in 5 seconds")
            await asyncio.sleep(5)


async def start_services():
    """Starts backend services: Database, Redis, Telegram Bot, and FastAPI Admin/Health server."""
    logger.info(f"Starting {BOT_NAME} backend services (Env: {settings.ENVIRONMENT})...")
    settings.validate_for_production()
    
    # 1. Initialize Database
    try:
        await init_db()
        logger.info("Database schemas verified.")
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        if settings.ENVIRONMENT == "production":
            raise e

    # 2. Connect Redis
    await redis_service.connect()

    # 3. Setup Bot if token configured
    bot_task = None
    bot = None
    if settings.BOT_TOKEN:
        bot = Bot(
            token=settings.BOT_TOKEN,
            default=DefaultBotProperties(parse_mode=ParseMode.MARKDOWN)
        )
        set_bot(bot)
        bot_task = asyncio.create_task(run_bot_polling(bot))
    else:
        if settings.ENVIRONMENT == "production":
            raise RuntimeError("BOT_TOKEN is required in production.")
        logger.warning("BOT_TOKEN is not configured. Bot polling is disabled for local development; FastAPI /health remains active.")

    # 4. Start FastAPI server for Railway Healthcheck and Admin endpoints
    port = int(os.getenv("PORT", "3000"))
    config = uvicorn.Config(
        app=fastapi_app,
        host="0.0.0.0",
        port=port,
        log_level="info" if not settings.DEBUG else "debug"
    )
    server = uvicorn.Server(config)

    try:
        logger.info(f"FastAPI server listening on http://0.0.0.0:{port} (Healthcheck at /health)")
        if bot_task:
            await asyncio.gather(server.serve(), bot_task)
        else:
            await server.serve()
    finally:
        if bot and not bot.session.closed:
            await bot.session.close()
        await redis_service.close()

def main():
    try:
        asyncio.run(start_services())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Services stopped gracefully.")

if __name__ == "__main__":
    main()
