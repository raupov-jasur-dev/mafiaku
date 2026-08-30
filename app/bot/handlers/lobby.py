import time
from aiogram import Router, F
from aiogram.types import CallbackQuery
from app.core.config import settings
from app.game.engine import GameEngine
from app.game.enums import GamePhase
from app.localization.manager import i18n
from app.bot.handlers.game_orchestrator import GameOrchestrator
from app.services.lock_manager import acquire_lock
from app.services.recovery_service import recovery_service
from app.bot.keyboards.inline import get_lobby_keyboard

router = Router()

@router.callback_query(F.data.startswith("game:join:"))
async def handle_join_game(callback: CallbackQuery, user_lang: str = "uz"):
    """Backward-compatible handler for stale lobby buttons.

    Players must establish a private chat with the bot before becoming participants.
    New keyboards use a URL deep link, but this handler safely redirects any old callback.
    """
    chat = callback.message.chat if callback.message else None
    if not chat or chat.type not in ("group", "supergroup"):
        await callback.answer("⚠️ Guruh topilmadi.", show_alert=True)
        return

    pm_join_url = f"https://t.me/{settings.BOT_USERNAME}?start=join_{chat.id}"
    await callback.answer(
        "🎭 O‘yinga qo‘shilish uchun botning shaxsiy chatini oching.",
        url=pm_join_url
    )
