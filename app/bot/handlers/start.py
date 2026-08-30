import time
import logging
from aiogram import Router, F
from aiogram.filters import CommandStart, Command, CommandObject
from aiogram.types import Message, CallbackQuery, ChatMemberUpdated
from app.core.config import settings
from app.localization.manager import i18n
from app.bot.keyboards.inline import get_start_keyboard, get_lobby_keyboard
from app.database.session import AsyncSessionLocal
from app.database.repositories import GroupRepository
from app.game.engine import GameEngine
from app.game.enums import GamePhase
from app.bot.handlers.game_orchestrator import GameOrchestrator
from app.services.lock_manager import acquire_lock
from app.services.recovery_service import recovery_service

logger = logging.getLogger(__name__)
router = Router()

@router.message(CommandStart())
async def cmd_start(message: Message, command: CommandObject, user_lang: str = "uz"):
    """
    Handles /start command:
    - In Group: Responds with short welcome and /game prompt.
    - In Private with deep-link args (e.g., /start join_-100123456): Joins the lobby directly!
    - In Private normal: Displays the rich main menu.
    """
    if message.chat.type in ("group", "supergroup"):
        text = i18n.get("group_welcome", user_lang)
        await message.reply(text, parse_mode="Markdown")
        return

    # Deep-link joining handling
    args = command.args
    if args and args.startswith("join_"):
        try:
            group_id_str = args.replace("join_", "", 1)
            group_id = int(group_id_str)

            # Only Telegram users who are actually members of the target group may join.
            try:
                member = await message.bot.get_chat_member(group_id, message.from_user.id)
                allowed_statuses = {"creator", "administrator", "member"}
                if member.status not in allowed_statuses and not getattr(member, "is_member", False):
                    await message.answer("⚠️ Avval o‘yin bo‘layotgan guruhga qo‘shiling, keyin shu tugmani bosing.")
                    return
            except Exception as e:
                logger.warning("Could not verify group membership for %s in %s: %s", message.from_user.id, group_id, e)
                await message.answer("⚠️ Guruhdagi a’zoligingizni tekshirib bo‘lmadi. Iltimos, guruhga qo‘shilganingizni va bot admin ekanini tekshiring.")
                return

            async with acquire_lock(f"join:{group_id}", timeout=5) as lock:
                state = GameOrchestrator.get_game(group_id)
                if not state or state.phase != GamePhase.LOBBY:
                    await message.answer("⚠️ Ushbu guruhdagi o'yin topilmadi yoki qabul muddati tugagan.", parse_mode="Markdown")
                    return
                
                success, reason = GameEngine.add_player(
                    state=state,
                    user_id=message.from_user.id,
                    full_name=message.from_user.full_name,
                    username=message.from_user.username,
                    language_code=user_lang
                )
                
                if not success:
                    if reason == "ALREADY_JOINED":
                        await message.answer("⚠️ Siz allaqachon ushbu o'yindasiz! Guruhga qaytib o'yin boshlanishini kuting.", parse_mode="Markdown")
                    else:
                        await message.answer(f"⚠️ O'yinga qo'shilish imkonsiz: {reason}", parse_mode="Markdown")
                    return

                await recovery_service.save_active_game(state)

            # Successfully joined via deep-link
            joined_confirmation = (
                f"✅ *Tabriklaymiz!*\n\n"
                f"Siz *{state.group_title}* guruhidagi Mafia o'yiniga qo'shildingiz!\n"
                f"🎭 O'yin boshlanganda shaxsiy rolingiz va tungi harakatlar aynan shu bot orqali yuboriladi.\n\n"
                f"Guruhga qaytib qolgan ishtirokchilarni kuting!"
            )
            await message.answer(joined_confirmation, parse_mode="Markdown")

            # Update lobby message in group
            if state.lobby_message_id:
                remaining = max(0, int(state.phase_deadline - time.time()))
                mins = remaining // 60
                secs = remaining % 60
                time_str = f"{mins:02d}:{secs:02d}"
                lobby_text = i18n.get(
                    "lobby_title",
                    state.group_language,
                    current=len(state.players),
                    max=state.max_players,
                    time_left=time_str
                )
                keyboard = get_lobby_keyboard(state.game_id, state.group_language, group_id=state.group_id)
                try:
                    await message.bot.edit_message_text(
                        text=lobby_text,
                        chat_id=state.group_id,
                        message_id=state.lobby_message_id,
                        reply_markup=keyboard,
                        parse_mode="Markdown"
                    )
                except Exception:
                    logger.debug("Could not update lobby message", exc_info=True)

            # IMPORTANT: do not wait for the full lobby timer once the minimum is reached.
            # This fixes the common production symptom where /game exists but the match never starts.
            if len(state.players) >= state.min_players:
                await GameOrchestrator.start_if_ready(message.bot, state)
            return
        except Exception as e:
            logger.error(f"Error handling deep link join: {e}")

    # Standard Private chat welcome menu
    text = i18n.get("welcome_title", user_lang)
    keyboard = get_start_keyboard(user_lang)
    await message.answer(text, reply_markup=keyboard, parse_mode="Markdown")

@router.my_chat_member()
async def bot_added_to_chat(event: ChatMemberUpdated):
    """Detects when bot is added to a group or granted administrator status."""
    chat = event.chat
    if chat.type not in ("group", "supergroup"):
        return

    new_member = event.new_chat_member
    is_admin = new_member.status in ("administrator", "creator")

    async with AsyncSessionLocal() as session:
        await GroupRepository.get_or_create(
            session=session,
            group_id=chat.id,
            title=chat.title or f"Group {chat.id}",
            username=chat.username,
            bot_is_admin=is_admin
        )
        await session.commit()

    bot_username = settings.BOT_USERNAME or "mafiaku_gobot"

    if is_admin:
        try:
            # 1. Send /start@mafiaku_gobot command text as required
            await event.bot.send_message(chat_id=chat.id, text=f"/start@{bot_username}")
            
            # 2. Localized instruction
            welcome_msg = (
                "🎭 *Mafia Ku*\n"
                "O‘yinni boshlash uchun /game yozing."
            )
            await event.bot.send_message(chat_id=chat.id, text=welcome_msg, parse_mode="Markdown")
        except Exception as e:
            logger.warning(f"Could not send auto-welcome to group {chat.id}: {e}")
    else:
        # Prompt group admin to grant admin rights
        warning_msg = (
            "⚠️ *Eslatma:* Bot to'liq ishlashi uchun unga guruh administratori huquqlarini bering.\n"
            "Administrator huquqi berilgach, avtomatik ravishda faollashadi!"
        )
        try:
            await event.bot.send_message(chat_id=chat.id, text=warning_msg, parse_mode="Markdown")
        except Exception as e:
            logger.warning(f"Could not send permission warning to group {chat.id}: {e}")
