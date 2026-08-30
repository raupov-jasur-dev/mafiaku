from aiogram import Router, F
from aiogram.types import CallbackQuery
from app.game.engine import GameEngine
from app.game.enums import GamePhase, Role
from app.localization.manager import i18n
from app.bot.handlers.game_orchestrator import active_games
from app.services.recovery_service import recovery_service
from app.services.lock_manager import acquire_lock
from app.database.session import AsyncSessionLocal
from app.database.repositories import GameRepository

router = Router()


@router.callback_query(F.data.startswith("night:action:"))
async def handle_night_action(callback: CallbackQuery, user_lang: str = "uz"):
    parts = callback.data.split(":")
    if len(parts) != 4:
        await callback.answer("⚠️ Noto‘g‘ri tugma.", show_alert=True)
        return
    game_id = parts[2]
    try:
        target_id = int(parts[3])
    except ValueError:
        await callback.answer("⚠️ Noto‘g‘ri o‘yinchi.", show_alert=True)
        return

    user_id = callback.from_user.id
    target_state = next((s for s in active_games.values() if s.game_id == game_id), None)
    if not target_state or target_state.phase != GamePhase.NIGHT:
        await callback.answer("⚠️ Tun allaqachon tugagan yoki o‘yin topilmadi.", show_alert=True)
        return

    async with acquire_lock(f"night:{game_id}:{user_id}", timeout=3) as lock:
        if not lock.acquired:
            await callback.answer("⚠️ So‘rov qayta ishlanmoqda.", show_alert=True)
            return
        player = target_state.get_player(user_id)
        if not player or not player.is_alive:
            await callback.answer("⚠️ Siz ushbu o‘yinda tirik emassiz!", show_alert=True)
            return
        target_player = target_state.get_player(target_id)
        if not target_player:
            await callback.answer("⚠️ O‘yinchi topilmadi.", show_alert=True)
            return
        target_name = target_player.display_name

        action_type = None
        if player.role == Role.MAFIA:
            success, msg = GameEngine.record_mafia_target(target_state, user_id, target_id)
            action_type = "MAFIA_KILL"
        elif player.role == Role.DOCTOR:
            success, msg = GameEngine.record_doctor_target(target_state, user_id, target_id)
            action_type = "DOCTOR_SAVE"
        elif player.role == Role.COMMISSAR:
            success, is_mafia, msg = GameEngine.record_commissar_target(target_state, user_id, target_id)
            action_type = "COMMISSAR_CHECK"
        else:
            await callback.answer("⚠️ Sizda tungi harakat qilish roli yo‘q.", show_alert=True)
            return

        if not success:
            await callback.answer(f"⚠️ Xatolik: {msg}", show_alert=True)
            return

        async with AsyncSessionLocal() as session:
            await GameRepository.save_game_action(
                session, target_state.game_id, target_state.round_number,
                user_id, action_type, target_id, True,
            )
            await session.commit()

        await recovery_service.save_active_game(target_state)
        if player.role == Role.COMMISSAR:
            result = i18n.get(
                "commissar_result_mafia" if is_mafia else "commissar_result_citizen",
                user_lang, target=target_name,
            )
            if callback.message:
                await callback.message.edit_text(result, parse_mode="Markdown")
            await callback.answer("Tekshiruv yakunlandi!")
        else:
            text = (f"🔴 Nishon tanlandi: *{target_name}*" if player.role == Role.MAFIA
                    else f"👨‍⚕️ Davolash tanlandi: *{target_name}*")
            if callback.message:
                await callback.message.edit_text(text, parse_mode="Markdown")
            await callback.answer(i18n.get("action_recorded", user_lang, target=target_name))
