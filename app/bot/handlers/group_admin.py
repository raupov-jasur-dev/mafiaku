from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message
from app.game.models import GameState
from app.localization.manager import i18n
from app.bot.handlers.game_orchestrator import GameOrchestrator
from app.services.recovery_service import recovery_service
from app.database.session import AsyncSessionLocal
from app.database.repositories import GroupRepository

router = Router()

@router.message(Command("resetgame"))
async def cmd_reset_game(message: Message, user_lang: str = "uz"):
    """Allows group admins to abort/reset a stuck game."""
    if message.chat.type not in ("group", "supergroup"):
        return

    # Check admin privileges
    member = await message.chat.get_member(message.from_user.id)
    if member.status not in ("creator", "administrator"):
        await message.reply(i18n.get("only_admin_can_action", user_lang))
        return

    group_id = message.chat.id
    GameOrchestrator.remove_game(group_id)
    await recovery_service.clear_active_game(group_id)

    await message.reply(i18n.get("game_reset_success", user_lang))

@router.message(Command("groupstats"))
async def cmd_group_stats(message: Message, user_lang: str = "uz"):
    """Shows top members for this specific group."""
    if message.chat.type not in ("group", "supergroup"):
        return

    group_id = message.chat.id
    group_title = message.chat.title or "Guruh"

    async with AsyncSessionLocal() as session:
        members = await GroupRepository.get_group_members(session, group_id, limit=10)

    if not members:
        await message.reply("🏆 Ushbu guruhda hali o'yinlar o'tkazilmagan.")
        return

    lines = []
    medals = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]
    for idx, mem in enumerate(members):
        medal = medals[idx] if idx < len(medals) else f"{idx+1}."
        user_name = mem.user.username and f"@{mem.user.username}" or mem.user.first_name if mem.user else f"ID:{mem.user_id}"
        lines.append(f"{medal} *{user_name}* — {mem.xp} XP | {mem.wins}/{mem.games_played} g'alaba")

    text = i18n.get("group_top_title", user_lang, group_name=group_title, top_list="\n".join(lines))
    await message.reply(text, parse_mode="Markdown")

@router.message(Command("rules"))
async def cmd_rules(message: Message, user_lang: str = "uz"):
    text = i18n.get("about_roles_text", user_lang)
    await message.reply(text, parse_mode="Markdown")
