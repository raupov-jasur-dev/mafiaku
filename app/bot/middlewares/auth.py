from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Message, CallbackQuery
from app.database.session import AsyncSessionLocal
from app.database.repositories import UserRepository, GroupRepository

class AuthMiddleware(BaseMiddleware):
    """Ensures Telegram users and groups are automatically registered/updated in PostgreSQL."""
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        user = None
        chat = None
        if isinstance(event, Message):
            user = event.from_user
            chat = event.chat
        elif isinstance(event, CallbackQuery):
            user = event.from_user
            chat = event.message.chat if event.message else None

        lang = "uz"
        async with AsyncSessionLocal() as session:
            if user and not user.is_bot:
                db_user = await UserRepository.get_or_create(
                    session=session,
                    user_id=user.id,
                    first_name=user.first_name or "",
                    last_name=user.last_name,
                    username=user.username,
                    language_code=user.language_code or "uz"
                )
                user_settings = await UserRepository.get_user_settings(session, user.id)
                if user_settings and user_settings.language:
                    lang = user_settings.language
                if db_user.is_banned:
                    if isinstance(event, CallbackQuery):
                        await event.answer("⛔ Siz botdan foydalanish uchun bloklangansiz.", show_alert=True)
                    elif isinstance(event, Message):
                        await event.reply("⛔ Siz botdan foydalanish uchun bloklangansiz.")
                    await session.commit()
                    return

            if chat and chat.type in ("group", "supergroup"):
                group = await GroupRepository.get_group(session, chat.id)
                if not group:
                    group = await GroupRepository.get_or_create(
                        session=session,
                        group_id=chat.id,
                        title=chat.title or f"Group {chat.id}",
                        username=chat.username,
                        bot_is_admin=False
                    )
                if group.is_banned:
                    if isinstance(event, CallbackQuery):
                        await event.answer("⛔ Bu guruh uchun bot o‘chirib qo‘yilgan.", show_alert=True)
                    elif isinstance(event, Message):
                        await event.reply("⛔ Bu guruh uchun Mafia Ku o‘chirib qo‘yilgan.")
                    await session.commit()
                    return
            await session.commit()

        data["user_lang"] = lang
        return await handler(event, data)
