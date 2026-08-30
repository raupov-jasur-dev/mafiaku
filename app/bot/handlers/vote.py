from aiogram import Router, F
from aiogram.types import CallbackQuery
from app.game.engine import GameEngine
from app.game.enums import GamePhase
from app.localization.manager import i18n
from app.bot.handlers.game_orchestrator import active_games
from app.services.lock_manager import acquire_lock
from app.services.recovery_service import recovery_service
from app.database.session import AsyncSessionLocal
from app.database.repositories import GameRepository

router = Router()


@router.callback_query(F.data.startswith("vote:cast:"))
async def handle_cast_vote(callback: CallbackQuery, user_lang: str = "uz"):
    parts = callback.data.split(":")
    if len(parts) != 4:
        await callback.answer("⚠️ Noto‘g‘ri ovoz tugmasi.", show_alert=True)
        return
    game_id = parts[2]
    try:
        target_id = int(parts[3])
    except ValueError:
        await callback.answer("⚠️ Noto‘g‘ri o‘yinchi.", show_alert=True)
        return
    user_id = callback.from_user.id

    target_state = next((s for s in active_games.values() if s.game_id == game_id), None)
    if not target_state or target_state.phase != GamePhase.VOTING:
        await callback.answer("⚠️ Ovoz berish bosqichi tugagan yoki o‘yin topilmadi.", show_alert=True)
        return

    async with acquire_lock(f"vote:{game_id}:{user_id}", timeout=3) as lock:
        if not lock.acquired:
            await callback.answer("⚠️ So‘rov qayta ishlanmoqda.", show_alert=True)
            return
        success, reason = GameEngine.record_vote(target_state, user_id, target_id)
        if not success:
            messages = {
                "CANNOT_VOTE_SELF": i18n.get("cannot_vote_self", user_lang),
                "ALREADY_VOTED": i18n.get("already_voted", user_lang),
                "DEAD_CANNOT_VOTE": "⚠️ Halok bo‘lgan o‘yinchilar ovoz bera olmaydi!",
            }
            await callback.answer(messages.get(reason, f"⚠️ Ovoz qabul qilinmadi: {reason}"), show_alert=True)
            return

        target_player = target_state.get_player(target_id)
        target_name = target_player.display_name if target_player else f"Player {target_id}"
        async with AsyncSessionLocal() as session:
            await GameRepository.save_game_vote(
                session, target_state.game_id, target_state.round_number,
                target_state.voting_attempt, user_id, target_id,
            )
            await session.commit()
        await recovery_service.save_active_game(target_state)
        await callback.answer(i18n.get("vote_recorded_toast", user_lang, target=target_name))
