from aiogram import Router, F
from aiogram.types import CallbackQuery
from app.game.engine import GameEngine
from app.game.enums import GamePhase, Role
from app.localization.manager import i18n
from app.bot.handlers.game_orchestrator import active_games
from app.services.recovery_service import recovery_service

router = Router()

@router.callback_query(F.data.startswith("night:action:"))
async def handle_night_action(callback: CallbackQuery, user_lang: str = "uz"):
    """
    Handles private night action button clicks (Mafia, Doctor, Commissar).
    """
    parts = callback.data.split(":")
    if len(parts) < 4:
        await callback.answer("Invalid callback data", show_alert=True)
        return

    game_id = parts[2]
    target_id = int(parts[3])
    user_id = callback.from_user.id

    # Find the corresponding active game
    target_state = None
    for state in active_games.values():
        if state.game_id == game_id:
            target_state = state
            break

    if not target_state or target_state.phase != GamePhase.NIGHT:
        await callback.answer("⚠️ Tun allaqachon tugagan yoki o'yin topilmadi.", show_alert=True)
        return

    player = target_state.get_player(user_id)
    if not player or not player.is_alive:
        await callback.answer("⚠️ Siz ushbu o'yinda tirik emassiz!", show_alert=True)
        return

    target_player = target_state.get_player(target_id)
    target_name = target_player.display_name if target_player else f"Player {target_id}"

    if player.role == Role.MAFIA:
        success, msg = GameEngine.record_mafia_target(target_state, user_id, target_id)
        if success:
            await callback.answer(i18n.get("action_recorded", user_lang, target=target_name), show_alert=False)
            if callback.message:
                await callback.message.edit_text(f"🔴 Nishon tanlandi: *{target_name}*", parse_mode="Markdown")
            await recovery_service.save_active_game(target_state)
        else:
            await callback.answer(f"Xatolik: {msg}", show_alert=True)

    elif player.role == Role.DOCTOR:
        success, msg = GameEngine.record_doctor_target(target_state, user_id, target_id)
        if success:
            await callback.answer(i18n.get("action_recorded", user_lang, target=target_name), show_alert=False)
            if callback.message:
                await callback.message.edit_text(f"👨‍⚕️ Davolash tanlandi: *{target_name}*", parse_mode="Markdown")
            await recovery_service.save_active_game(target_state)
        else:
            await callback.answer(f"Xatolik: {msg}", show_alert=True)

    elif player.role == Role.COMMISSAR:
        success, is_mafia, msg = GameEngine.record_commissar_target(target_state, user_id, target_id)
        if success:
            if is_mafia:
                res_text = i18n.get("commissar_result_mafia", user_lang, target=target_name)
            else:
                res_text = i18n.get("commissar_result_citizen", user_lang, target=target_name)

            await callback.answer("Tekshiruv yakunlandi!", show_alert=False)
            if callback.message:
                await callback.message.edit_text(res_text, parse_mode="Markdown")
            await recovery_service.save_active_game(target_state)
        else:
            await callback.answer(f"Xatolik: {msg}", show_alert=True)
    else:
        await callback.answer("⚠️ Sizda tungi harakat qilish roli yo'q.", show_alert=True)
