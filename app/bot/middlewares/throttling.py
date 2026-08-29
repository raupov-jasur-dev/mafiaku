from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, CallbackQuery, Message
from app.services.rate_limiter import rate_limiter

class ThrottlingMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        user_id = None
        if isinstance(event, Message) and event.from_user:
            user_id = event.from_user.id
        elif isinstance(event, CallbackQuery) and event.from_user:
            user_id = event.from_user.id

        if user_id:
            is_limited = await rate_limiter.is_rate_limited(user_id=user_id, max_requests=8, window_seconds=2)
            if is_limited:
                if isinstance(event, CallbackQuery):
                    await event.answer("⚠️ Iltimos, biroz kuting (Anti-spam)!", show_alert=True)
                return

        return await handler(event, data)
