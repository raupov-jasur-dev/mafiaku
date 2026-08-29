import asyncio
import logging
import time
from typing import Dict, Optional, List
from aiogram import Bot
from aiogram.exceptions import TelegramAPIError

from app.game.engine import GameEngine
from app.game.models import GameState, PlayerState
from app.game.enums import GamePhase, Role, WinnerTeam
from app.localization.manager import i18n
from app.bot.keyboards.inline import (
    get_night_action_keyboard,
    get_voting_keyboard,
    get_lobby_keyboard
)
from app.services.recovery_service import recovery_service
from app.services.stats_service import stats_service
from app.services.achievement_service import achievement_service
from app.database.session import AsyncSessionLocal
from app.database.repositories import GameRepository

logger = logging.getLogger(__name__)

# Active in-memory orchestrator states keyed by group_id
active_games: Dict[int, GameState] = {}
active_tasks: Dict[int, asyncio.Task] = {}

class GameOrchestrator:
    """Coordinates Telegram Bot interactions with the pure GameEngine state machine."""

    @classmethod
    def get_game(cls, group_id: int) -> Optional[GameState]:
        return active_games.get(group_id)

    @classmethod
    def set_game(cls, group_id: int, state: GameState) -> None:
        active_games[group_id] = state

    @classmethod
    def remove_game(cls, group_id: int) -> None:
        active_games.pop(group_id, None)
        task = active_tasks.pop(group_id, None)
        if task and not task.done():
            task.cancel()

    @classmethod
    async def restore_active_games(cls, bot: Bot):
        """Restores and resumes active games from Redis on startup."""
        saved_games = await recovery_service.get_all_saved_games()
        for state in saved_games:
            cls.set_game(state.group_id, state)
            logger.info(f"Restored active game {state.game_id} in group {state.group_id} (Phase: {state.phase.value})")
            if state.phase == GamePhase.LOBBY:
                remaining = max(5, int(state.phase_deadline - time.time()))
                task = asyncio.create_task(
                    cls.run_lobby_loop(bot, state.group_id, state.lobby_message_id or 0, duration=remaining)
                )
                active_tasks[state.group_id] = task
            elif state.phase != GamePhase.ENDED:
                task = asyncio.create_task(cls.run_game_loop(bot, state))
                active_tasks[state.group_id] = task

    @classmethod
    async def run_lobby_loop(cls, bot: Bot, group_id: int, lobby_msg_id: int, duration: int = 180):
        """Monitors lobby timer and updates message periodically."""
        start_time = time.time()
        end_time = start_time + duration
        
        while time.time() < end_time:
            await asyncio.sleep(20)
            state = cls.get_game(group_id)
            if not state or state.phase != GamePhase.LOBBY:
                return

            remaining = max(0, int(end_time - time.time()))
            mins = remaining // 60
            secs = remaining % 60
            time_str = f"{mins:02d}:{secs:02d}"

            glang = state.group_language
            text = i18n.get(
                "lobby_title",
                glang,
                current=len(state.players),
                max=20,
                time_left=time_str
            )
            try:
                if lobby_msg_id:
                    await bot.edit_message_text(
                        chat_id=group_id,
                        message_id=lobby_msg_id,
                        text=text,
                        reply_markup=get_lobby_keyboard(state.game_id, glang, group_id=group_id),
                        parse_mode="Markdown"
                    )
            except Exception as e:
                logger.debug(f"Lobby edit skipped: {e}")

        # Lobby expired - check if enough players
        state = cls.get_game(group_id)
        if not state or state.phase != GamePhase.LOBBY:
            return

        glang = state.group_language
        if len(state.players) < 4:
            cancel_text = i18n.get("lobby_not_enough_players", glang, min=4)
            try:
                await bot.send_message(chat_id=group_id, text=cancel_text, parse_mode="Markdown")
            except Exception:
                pass
            cls.remove_game(group_id)
            await recovery_service.clear_active_game(group_id)
            return

        # Start match loop
        await cls.run_game_loop(bot, state)

    @classmethod
    async def run_game_loop(cls, bot: Bot, state: GameState):
        """Full game state lifecycle orchestrator."""
        group_id = state.group_id
        glang = state.group_language
        
        # 1. Assign Roles & Create DB record if not yet started
        if state.phase == GamePhase.LOBBY:
            GameEngine.start_game(state)
            async with AsyncSessionLocal() as session:
                await GameRepository.create_game_record(session, state.game_id, group_id, len(state.players))
                await GameRepository.record_game_event(session, state.game_id, "GAME_STARTED", f"Players: {len(state.players)}")
                await session.commit()

            start_notice = i18n.get("game_starting", glang, count=len(state.players))
            try:
                await bot.send_message(chat_id=group_id, text=start_notice, parse_mode="Markdown")
            except Exception:
                pass

            # Send private role messages to each player in their personal language
            mafia_team_names = [p.display_name for p in state.players.values() if p.role == Role.MAFIA]
            team_str = "\n".join([f"• {name}" for name in mafia_team_names])

            for player in state.players.values():
                plang = player.language_code or glang
                try:
                    if player.role == Role.MAFIA:
                        text = f"{i18n.get('role_mafia_title', plang)}\n\n{i18n.get('role_mafia_desc', plang)}"
                        if len(mafia_team_names) > 1:
                            text += i18n.get('role_mafia_team', plang, team=team_str)
                    elif player.role == Role.DOCTOR:
                        text = f"{i18n.get('role_doctor_title', plang)}\n\n{i18n.get('role_doctor_desc', plang)}"
                    elif player.role == Role.COMMISSAR:
                        text = f"{i18n.get('role_commissar_title', plang)}\n\n{i18n.get('role_commissar_desc', plang)}"
                    else:
                        text = f"{i18n.get('role_citizen_title', plang)}\n\n{i18n.get('role_citizen_desc', plang)}"

                    await bot.send_message(chat_id=player.user_id, text=text, parse_mode="Markdown")
                except Exception as e:
                    logger.warning(f"Could not send private role message to {player.user_id}: {e}")

            await asyncio.sleep(4)

        # Main Round Cycle
        while True:
            # --- NIGHT PHASE ---
            if state.phase != GamePhase.NIGHT:
                GameEngine.begin_night(state, duration=45)
                await recovery_service.save_active_game(state)
                async with AsyncSessionLocal() as session:
                    await GameRepository.record_game_event(session, state.game_id, "NIGHT_STARTED", f"Round {state.round_number}")
                    await session.commit()

            night_intro = f"🌙 *{state.round_number}-TUN*\n\n{i18n.get('night_started_group', glang)}"
            try:
                await bot.send_message(chat_id=group_id, text=night_intro, parse_mode="Markdown")
            except Exception:
                pass

            # Send action buttons in private chat to living active roles
            alive = state.alive_players
            for player in alive:
                plang = player.language_code or glang
                try:
                    if player.role == Role.MAFIA:
                        kb = get_night_action_keyboard(state.game_id, alive, exclude_user_id=None)
                        await bot.send_message(chat_id=player.user_id, text=i18n.get("mafia_action_prompt", plang), reply_markup=kb, parse_mode="Markdown")
                    elif player.role == Role.DOCTOR:
                        kb = get_night_action_keyboard(state.game_id, alive, exclude_user_id=None)
                        await bot.send_message(chat_id=player.user_id, text=i18n.get("doctor_action_prompt", plang), reply_markup=kb, parse_mode="Markdown")
                    elif player.role == Role.COMMISSAR:
                        kb = get_night_action_keyboard(state.game_id, alive, exclude_user_id=player.user_id)
                        await bot.send_message(chat_id=player.user_id, text=i18n.get("commissar_action_prompt", plang), reply_markup=kb, parse_mode="Markdown")
                except Exception as e:
                    logger.debug(f"Action prompt error for {player.user_id}: {e}")

            # Calculate remaining night time if restored
            night_rem = max(0, int(state.phase_deadline - time.time()))
            while night_rem > 0:
                await asyncio.sleep(2)
                night_rem -= 2
                mafia_done = len(state.mafia_votes) == len(state.alive_mafia)
                doc_alive = any(p.role == Role.DOCTOR for p in state.alive_players)
                doc_done = (state.doctor_target_id is not None) if doc_alive else True
                com_alive = any(p.role == Role.COMMISSAR for p in state.alive_players)
                com_done = (state.commissar_target_id is not None) if com_alive else True
                if mafia_done and doc_done and com_done:
                    break

            # --- NIGHT RESOLUTION ---
            killed_id, was_saved = GameEngine.resolve_night(state)
            await recovery_service.save_active_game(state)

            async with AsyncSessionLocal() as session:
                await GameRepository.record_game_event(
                    session, 
                    state.game_id, 
                    "NIGHT_RESOLVED", 
                    f"Killed: {killed_id}, Saved: {was_saved}"
                )
                await session.commit()

            if killed_id:
                victim = state.get_player(killed_id)
                victim_name = victim.display_name if victim else "Player"
                victim_role = victim.role.value if victim and victim.role else "Citizen"
                morning_text = i18n.get("morning_killed", glang, player=victim_name, role=victim_role)
            else:
                morning_text = i18n.get("morning_no_kill", glang)

            try:
                await bot.send_message(chat_id=group_id, text=morning_text, parse_mode="Markdown")
            except Exception:
                pass

            await asyncio.sleep(3)

            # --- CHECK WIN CONDITIONS AFTER NIGHT ---
            winner = GameEngine.check_win_condition(state)
            if winner:
                break

            # --- DISCUSSION PHASE (120 SECONDS) ---
            if state.phase != GamePhase.DISCUSSION:
                GameEngine.begin_discussion(state, duration=120)
                await recovery_service.save_active_game(state)
                async with AsyncSessionLocal() as session:
                    await GameRepository.record_game_event(session, state.game_id, "DISCUSSION_STARTED", f"Round {state.round_number}")
                    await session.commit()

            disc_text = i18n.get("discussion_start", glang, minutes=2)
            try:
                await bot.send_message(chat_id=group_id, text=disc_text, parse_mode="Markdown")
            except Exception:
                pass

            # Precise 120s discussion timer supporting restart recovery
            disc_rem = max(0, int(state.phase_deadline - time.time()))
            while disc_rem > 0:
                step = min(5, disc_rem)
                await asyncio.sleep(step)
                disc_rem -= step
                if cls.get_game(group_id) is None:
                    return

            # --- VOTING PHASE (45 SECONDS) ---
            voting_attempt = 1
            while voting_attempt <= 2:
                GameEngine.begin_voting(state, duration=45)
                await recovery_service.save_active_game(state)

                async with AsyncSessionLocal() as session:
                    await GameRepository.record_game_event(session, state.game_id, "VOTE_STARTED", f"Attempt {voting_attempt}")
                    await session.commit()

                # Group notification
                vote_group_text = (
                    f"🗳 *{state.round_number}-RAUND: OVOZ BERISH BOSHLANDI!*\n\n"
                    f"⏱ Vaqt: 45 soniya\n"
                    f"Shahardan kimni chiqarish kerakligini botning *shaxsiy chatida* tanlang!"
                )
                try:
                    await bot.send_message(chat_id=group_id, text=vote_group_text, parse_mode="Markdown")
                except Exception:
                    pass

                # Send private voting keyboard to each living player
                for player in state.alive_players:
                    plang = player.language_code or glang
                    pkb = get_voting_keyboard(state.game_id, state.alive_players, voter_id=player.user_id)
                    vote_pm_text = (
                        f"🗳 *{state.group_title}*\n\n"
                        f"{i18n.get('voting_title', plang, seconds=45)}\n"
                        f"Kimni shahardan chiqarmoqchisiz?"
                    )
                    try:
                        await bot.send_message(chat_id=player.user_id, text=vote_pm_text, reply_markup=pkb, parse_mode="Markdown")
                    except Exception as e:
                        logger.debug(f"Could not send private vote to {player.user_id}: {e}")

                vote_rem = max(0, int(state.phase_deadline - time.time()))
                while vote_rem > 0:
                    await asyncio.sleep(2)
                    vote_rem -= 2
                    # Early termination if all living players voted
                    voted_count = len([p for p in state.alive_players if p.vote_target is not None])
                    if voted_count == len(state.alive_players):
                        break

                eliminated_id, is_tie, is_double_tie = GameEngine.resolve_voting(state)
                await recovery_service.save_active_game(state)

                if is_tie:
                    try:
                        await bot.send_message(chat_id=group_id, text=i18n.get("vote_tie", glang), parse_mode="Markdown")
                    except Exception:
                        pass
                    voting_attempt += 1
                    await asyncio.sleep(3)
                    continue

                if is_double_tie:
                    try:
                        await bot.send_message(chat_id=group_id, text=i18n.get("vote_double_tie", glang), parse_mode="Markdown")
                    except Exception:
                        pass
                    break

                if eliminated_id:
                    elim_player = state.get_player(eliminated_id)
                    p_name = elim_player.display_name if elim_player else "Player"
                    p_role = elim_player.role.value if elim_player and elim_player.role else "Citizen"
                    elim_text = i18n.get("vote_eliminated", glang, player=p_name, role=p_role)
                    try:
                        await bot.send_message(chat_id=group_id, text=elim_text, parse_mode="Markdown")
                    except Exception:
                        pass
                break

            await asyncio.sleep(3)

            # --- CHECK WIN CONDITIONS AFTER VOTING ---
            winner = GameEngine.check_win_condition(state)
            if winner:
                break

            state.round_number += 1

        # --- GAME OVER & REWARD SUMMARY ---
        await cls.finalize_game(bot, state)

    @classmethod
    async def finalize_game(cls, bot: Bot, state: GameState):
        group_id = state.group_id
        glang = state.group_language
        is_cit_win = (state.winner == WinnerTeam.CITIZENS)
        winner_str = i18n.get("winner_citizens", glang) if is_cit_win else i18n.get("winner_mafia", glang)
        
        # Build roles list
        roles_lines = []
        for p in state.players.values():
            role_icon = "🔴 Mafia" if p.role == Role.MAFIA else ("👨‍⚕️ Doctor" if p.role == Role.DOCTOR else ("🕵️ Commissar" if p.role == Role.COMMISSAR else "👨‍🌾 Citizen"))
            status = " (Tirik)" if p.is_alive else " (☠️ Halok bo'lgan)"
            roles_lines.append(f"• {p.display_name} — {role_icon}{status}")
        roles_text = "\n".join(roles_lines)

        mvp_player = state.get_player(state.mvp_player_id) if state.mvp_player_id else None
        mvp_name = mvp_player.display_name if mvp_player else "—"

        summary_msg = (
            f"{i18n.get('game_over_title', glang)}\n\n"
            f"{winner_str}\n\n"
            f"🎭 *Rollar:*\n{roles_text}\n\n"
            f"⭐ *MVP:* {mvp_name}"
        )

        try:
            await bot.send_message(chat_id=group_id, text=summary_msg, parse_mode="Markdown")
        except Exception as e:
            logger.error(f"Could not send game over message: {e}")

        # Update stats, game players, & DB
        async with AsyncSessionLocal() as session:
            await GameRepository.complete_game_record(
                session=session,
                game_id=state.game_id,
                winner=state.winner.value if state.winner else "DRAW",
                rounds=state.round_number,
                mvp_user_id=state.mvp_player_id
            )
            await GameRepository.record_game_event(
                session=session,
                game_id=state.game_id,
                event_type="GAME_FINISHED",
                payload=f"Winner: {state.winner.value if state.winner else 'DRAW'}, MVP: {mvp_name}"
            )
            for p in state.players.values():
                death_reason = None
                death_round = None
                if not p.is_alive:
                    death_round = state.round_number
                    death_reason = "ELIMINATED"

                await GameRepository.save_game_player(
                    session=session,
                    game_id=state.game_id,
                    user_id=p.user_id,
                    role=p.role.value if p.role else "CITIZEN",
                    is_alive=p.is_alive,
                    death_round=death_round,
                    death_reason=death_reason,
                    kills=p.kills,
                    saves=p.saves,
                    investigations=p.investigations,
                    xp_earned=100 if (is_cit_win and p.role != Role.MAFIA) or (not is_cit_win and p.role == Role.MAFIA) else 30
                )
            await stats_service.process_game_completion(session, state)
            
            # Check achievements for all players
            for p in state.players.values():
                newly_unlocked = await achievement_service.check_and_unlock_achievements(session, p.user_id)
                if newly_unlocked:
                    for ach_id in newly_unlocked:
                        try:
                            await bot.send_message(
                                chat_id=p.user_id,
                                text=f"🎉 *Yangi Yutuq ochildi!* 🏆\nSiz '{ach_id}' yutug'ini qo'lga kiritdingiz!",
                                parse_mode="Markdown"
                            )
                        except Exception:
                            pass
            await session.commit()

        cls.remove_game(group_id)
        await recovery_service.clear_active_game(group_id)
