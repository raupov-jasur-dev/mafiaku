import asyncio
import logging
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message
from app.core.config import settings
from app.game.engine import GameEngine
from app.game.enums import GamePhase
from app.localization.manager import i18n
from app.bot.keyboards.inline import get_lobby_keyboard
from app.bot.handlers.game_orchestrator import GameOrchestrator, active_tasks
from app.services.lock_manager import acquire_lock
from app.services.recovery_service import recovery_service
from app.database.session import AsyncSessionLocal
from app.database.repositories import GroupRepository

logger = logging.getLogger(__name__)
router = Router()

@router.message(Command("game"))
async def cmd_create_game(message: Message, user_lang: str = "uz"):
    """
    Handles /game in group chats.
    - Validates chat is group/supergroup.
    - Checks bot is admin with necessary rights.
    - Creates a 3-minute lobby and prevents double-game creation via atomic distributed lock.
    """
    if message.chat.type not in ("group", "supergroup"):
        await message.reply("⚠️ O'yinni faqat guruhlarda boshlash mumkin!\n\nBotni guruhingizga qo'shing va /game buyrug'ini bering.")
        return

    group_id = message.chat.id
    group_title = message.chat.title or f"Group {group_id}"

    # Verify bot admin status in group
    is_admin = False
    try:
        bot_member = await message.bot.get_chat_member(message.chat.id, message.bot.id)
        is_admin = bot_member.status in ("administrator", "creator")
        if not is_admin:
            text = (
                "⚠️ *Botga administrator huquqlari zarur!*\n\n"
                "O'yinni to'g'ri boshqarish, xabarlarni tartibga solish va ovozlarni hisoblash uchun "
                "botni guruhga *Admin* qiling."
            )
            await message.reply(text, parse_mode="Markdown")
            return
    except Exception as e:
        logger.warning(f"Could not check bot member status in group {group_id}: {e}")

    async with acquire_lock(f"create_game:{group_id}", timeout=5) as lock:
        if not lock.acquired:
            await message.reply("⚠️ So'rov qayta ishlanmoqda, kuting...")
            return

        existing = GameOrchestrator.get_game(group_id)
        if existing:
            await message.reply(i18n.get("game_already_running", user_lang))
            return

        # Record or update group in database
        async with AsyncSessionLocal() as session:
            await GroupRepository.get_or_create(
                session=session,
                group_id=group_id,
                title=group_title,
                username=message.chat.username,
                bot_is_admin=is_admin
            )
            await session.commit()

        # Create new authoritative GameState
        state = GameEngine.create_game(
            group_id=group_id, 
            group_title=group_title, 
            lobby_duration=settings.LOBBY_DURATION,
            group_language=user_lang
        )
        GameOrchestrator.set_game(group_id, state)
        await recovery_service.save_active_game(state)

        # Initial Lobby Message
        text = i18n.get(
            "lobby_title",
            user_lang,
            current=0,
            max=settings.MAX_PLAYERS,
            time_left="03:00"
        )
        keyboard = get_lobby_keyboard(state.game_id, user_lang, group_id=group_id)

        lobby_msg = await message.answer(text, reply_markup=keyboard, parse_mode="Markdown")
        state.lobby_message_id = lobby_msg.message_id
        await recovery_service.save_active_game(state)

        # Spawn non-blocking background lobby timer task
        task = asyncio.create_task(
            GameOrchestrator.run_lobby_loop(
                bot=message.bot,
                group_id=group_id,
                lobby_msg_id=lobby_msg.message_id,
                duration=settings.LOBBY_DURATION
            )
        )
        active_tasks[group_id] = task
