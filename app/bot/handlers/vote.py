from aiogram import Router, F
from aiogram.types import CallbackQuery
from app.game.engine import GameEngine
from app.game.enums import GamePhase
from app.localization.manager import i18n
from app.bot.handlers.game_orchestrator import active_games
from app.services.lock_manager import acquire_lock
from app.services.recovery_service import recovery_service

router = Router()

@router.callback_query(F.data.startswith("vote:cast:"))
async def handle_cast_vote(callback: CallbackQuery, user_lang: str = "uz"):
    """
    Handles daytime town voting callback clicks.
    Guaranteed single vote per alive player, no self-voting.
    """
    parts = callback.data.split(":")
    if len(parts) < 4:
        await callback.answer("Invalid vote data", show_alert=True)
        return

    game_id = parts[2]
    target_id = int(parts[3])
    user_id = callback.from_user.id

    target_state = None
    for state in active_games.values():
        if state.game_id == game_id:
            target_state = state
            break

    if not target_state or target_state.phase != GamePhase.VOTING:
        await callback.answer("⚠️ Ovoz berish bosqichi tugagan yoki o'yin topilmadi.", show_alert=True)
        return

    async with acquire_lock(f"vote:{game_id}:{user_id}", timeout=3) as lock:
        success, reason = GameEngine.record_vote(target_state, user_id, target_id)
        if not success:
            if reason == "CANNOT_VOTE_SELF":
                await callback.answer(i18n.get("cannot_vote_self", user_lang), show_alert=True)
            elif reason == "ALREADY_VOTED":
                await callback.answer(i18n.get("already_voted", user_lang), show_alert=True)
            elif reason == "DEAD_CANNOT_VOTE":
                await callback.answer("⚠️ Halok bo'lgan o'yinchilar ovoz bera olmaydi!", show_alert=True)
            else:
                await callback.answer(f"⚠️ Ovoz qabul qilinmadi: {reason}", show_alert=True)
            return

        target_player = target_state.get_player(target_id)
        target_name = target_player.display_name if target_player else f"Player {target_id}"
        await callback.answer(i18n.get("vote_recorded_toast", user_lang, target=target_name), show_alert=False)
        await recovery_service.save_active_game(target_state)
