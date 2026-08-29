from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message
from app.database.session import AsyncSessionLocal
from app.database.repositories import UserRepository
from app.localization.manager import i18n
from app.bot.keyboards.inline import get_back_to_start_keyboard

router = Router()

@router.callback_query(F.data == "menu:profile")
async def show_profile_callback(callback: CallbackQuery, user_lang: str = "uz"):
    user = callback.from_user
    async with AsyncSessionLocal() as session:
        stats = await UserRepository.get_user_stats(session, user.id)
        rank = await UserRepository.get_user_rank(session, user.id)

    games = stats.games_played if stats else 0
    wins = stats.wins if stats else 0
    losses = stats.losses if stats else 0
    win_rate = int((wins / games * 100)) if games > 0 else 0
    rank_name = rank.rank_name if rank else "Newbie"
    xp = rank.xp if rank else 0

    title = i18n.get("profile_title", user_lang, name=user.full_name)
    content = i18n.get(
        "profile_stats", 
        user_lang,
        games=games,
        wins=wins,
        losses=losses,
        win_rate=win_rate,
        rank=rank_name,
        xp=xp
    )

    text = f"{title}\n\n{content}"
    keyboard = get_back_to_start_keyboard(user_lang)
    
    if callback.message:
        await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="Markdown")
    await callback.answer()

@router.message(Command("profile", "me", "stats"))
async def show_profile_command(message: Message, user_lang: str = "uz"):
    user = message.from_user
    async with AsyncSessionLocal() as session:
        stats = await UserRepository.get_user_stats(session, user.id)
        rank = await UserRepository.get_user_rank(session, user.id)

    games = stats.games_played if stats else 0
    wins = stats.wins if stats else 0
    losses = stats.losses if stats else 0
    win_rate = int((wins / games * 100)) if games > 0 else 0
    rank_name = rank.rank_name if rank else "Newbie"
    xp = rank.xp if rank else 0

    title = i18n.get("profile_title", user_lang, name=user.full_name)
    content = i18n.get(
        "profile_stats", 
        user_lang,
        games=games,
        wins=wins,
        losses=losses,
        win_rate=win_rate,
        rank=rank_name,
        xp=xp
    )

    text = f"{title}\n\n{content}"
    await message.reply(text, parse_mode="Markdown")
