from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message
from sqlalchemy import select, desc
from app.database.session import AsyncSessionLocal
from app.database.models import UserRank, User, GroupMember
from app.localization.manager import i18n
from app.bot.keyboards.inline import get_back_to_start_keyboard

router = Router()

@router.callback_query(F.data == "menu:top")
async def show_top_players_menu(callback: CallbackQuery, user_lang: str = "uz"):
    async with AsyncSessionLocal() as session:
        stmt = (
            select(UserRank, User)
            .join(User, UserRank.user_id == User.id)
            .order_by(desc(UserRank.xp))
            .limit(10)
        )
        res = await session.execute(stmt)
        top_list = res.all()

    lines = []
    medals = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]
    for idx, (rank, user) in enumerate(top_list):
        medal = medals[idx] if idx < len(medals) else f"{idx+1}."
        name = user.username and f"@{user.username}" or user.first_name
        lines.append(f"{medal} *{name}* — {rank.xp} XP ({rank.rank_name})")

    if not lines:
        lines_text = "Hozircha o'yinchilar ro'yxati bo'sh. Birinchi bo'lib o'ynang!"
    else:
        lines_text = "\n".join(lines)

    text = f"🏆 *GLOBAL TOP O'YINCHILAR*\n\n{lines_text}"
    keyboard = get_back_to_start_keyboard(user_lang)
    if callback.message:
        await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="Markdown")
    await callback.answer()

@router.message(Command("top"))
async def cmd_top(message: Message, user_lang: str = "uz"):
    """
    Shows top leaderboard:
    - If in Group: Shows top players specific to this group.
    - If in Private: Shows global top players.
    """
    async with AsyncSessionLocal() as session:
        if message.chat.type in ("group", "supergroup"):
            group_id = message.chat.id
            stmt = (
                select(GroupMember, User)
                .join(User, GroupMember.user_id == User.id)
                .where(GroupMember.group_id == group_id)
                .order_by(desc(GroupMember.xp))
                .limit(10)
            )
            res = await session.execute(stmt)
            top_list = res.all()

            lines = []
            medals = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]
            for idx, (member, user) in enumerate(top_list):
                medal = medals[idx] if idx < len(medals) else f"{idx+1}."
                name = user.username and f"@{user.username}" or user.first_name
                lines.append(f"{medal} *{name}* — {member.xp} XP | 🎮 {member.games_played} | 🏆 {member.wins}")

            group_title = message.chat.title or "Guruh"
            if not lines:
                lines_text = "Ushbu guruhda hali o'yin o'tkazilmagan. /game orqali boshlang!"
            else:
                lines_text = "\n".join(lines)

            text = f"🏆 *GURUH LIDERLARI ({group_title})*\n\n{lines_text}"
            await message.reply(text, parse_mode="Markdown")
        else:
            stmt = (
                select(UserRank, User)
                .join(User, UserRank.user_id == User.id)
                .order_by(desc(UserRank.xp))
                .limit(10)
            )
            res = await session.execute(stmt)
            top_list = res.all()

            lines = []
            medals = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]
            for idx, (rank, user) in enumerate(top_list):
                medal = medals[idx] if idx < len(medals) else f"{idx+1}."
                name = user.username and f"@{user.username}" or user.first_name
                lines.append(f"{medal} *{name}* — {rank.xp} XP ({rank.rank_name})")

            if not lines:
                lines_text = "Hozircha o'yinchilar ro'yxati bo'sh."
            else:
                lines_text = "\n".join(lines)

            text = f"🏆 *GLOBAL TOP O'YINCHILAR*\n\n{lines_text}"
            await message.reply(text, parse_mode="Markdown")
