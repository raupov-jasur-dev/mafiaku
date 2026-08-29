from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message
from sqlalchemy import select, func
from app.core.config import settings
from app.database.session import AsyncSessionLocal
from app.database.models import User, Group, Game, UserStatistics

router = Router()

def is_admin(user_id: int) -> bool:
    return user_id in settings.admin_ids

@router.message(Command("admin"))
async def cmd_admin_panel(message: Message):
    if not is_admin(message.from_user.id):
        return

    async with AsyncSessionLocal() as session:
        user_count = await session.scalar(select(func.count(User.id)))
        group_count = await session.scalar(select(func.count(Group.id)))
        game_count = await session.scalar(select(func.count(Game.id)))

    text = (
        "👑 *MAFIA KU SUPERADMIN PANEL*\n\n"
        f"👤 Jami foydalanuvchilar: *{user_count}*\n"
        f"👥 Jami guruhlar: *{group_count}*\n"
        f"🎮 O'tkazilgan o'yinlar: *{game_count}*\n\n"
        "Buyruqlar:\n"
        "/broadcast [xabar] — Barcha userlarga xabar yuborish\n"
        "/admin_stats — Batafsil analitika"
    )
    await message.reply(text, parse_mode="Markdown")

@router.message(Command("broadcast"))
async def cmd_broadcast(message: Message):
    if not is_admin(message.from_user.id):
        return

    text_to_send = message.text.replace("/broadcast", "", 1).strip()
    if not text_to_send:
        await message.reply("⚠️ Xabar matnini kiriting: `/broadcast Salom hammaga!`", parse_mode="Markdown")
        return

    async with AsyncSessionLocal() as session:
        users = (await session.execute(select(User.id))).scalars().all()

    sent = 0
    failed = 0
    for uid in users:
        try:
            await message.bot.send_message(chat_id=uid, text=text_to_send, parse_mode="Markdown")
            sent += 1
        except Exception:
            failed += 1

    await message.reply(f"📢 Broadcast yakunlandi:\n✅ Yetkazildi: {sent}\n❌ Xatolik: {failed}")
