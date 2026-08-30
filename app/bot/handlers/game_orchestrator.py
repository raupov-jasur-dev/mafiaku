import asyncio
import logging
import time
from typing import Dict, Optional

from aiogram import Bot

from app.game.engine import GameEngine
from app.game.models import GameState
from app.game.enums import GamePhase, Role, WinnerTeam
from app.localization.manager import i18n
from app.bot.keyboards.inline import get_night_action_keyboard, get_voting_keyboard, get_lobby_keyboard
from app.services.recovery_service import recovery_service
from app.services.stats_service import stats_service
from app.services.achievement_service import achievement_service
from app.database.session import AsyncSessionLocal
from app.database.repositories import GameRepository

logger = logging.getLogger(__name__)

active_games: Dict[int, GameState] = {}
active_tasks: Dict[int, asyncio.Task] = {}


class GameOrchestrator:
    """Telegram-facing game lifecycle manager with restart-safe phase handling."""

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
        if task and not task.done() and task is not asyncio.current_task():
            task.cancel()

    @classmethod
    def _spawn_task(cls, bot: Bot, state: GameState) -> asyncio.Task:
        old = active_tasks.get(state.group_id)
        current = asyncio.current_task()
        if old and not old.done() and old is not current:
            old.cancel()
        task = asyncio.create_task(cls.run_game_loop(bot, state), name=f"mafia-game-{state.group_id}")
        active_tasks[state.group_id] = task
        return task

    @classmethod
    async def start_if_ready(cls, bot: Bot, state: GameState) -> bool:
        """Start once the minimum is reached, with a short grace period for extra players."""
        if state.phase != GamePhase.LOBBY or len(state.players) < state.min_players:
            return False
        # A short grace period prevents a 20-player game from locking at exactly 4 players.
        if state.auto_start_delay > 0:
            await asyncio.sleep(state.auto_start_delay)
        if state.group_id not in active_games or state.phase != GamePhase.LOBBY:
            return False
        cls._spawn_task(bot, state)
        return True

    @classmethod
    async def restore_active_games(cls, bot: Bot) -> None:
        """Restore every Redis-persisted game without resetting its current phase."""
        saved_games = await recovery_service.get_all_saved_games()
        for state in saved_games:
            if state.phase == GamePhase.GAME_OVER:
                # A completed game can safely be removed from recovery storage.
                await recovery_service.clear_active_game(state.group_id)
                continue
            cls.set_game(state.group_id, state)
            if state.phase == GamePhase.LOBBY:
                if len(state.players) >= state.min_players:
                    cls._spawn_task(bot, state)
                else:
                    task = asyncio.create_task(cls.run_lobby_loop(bot, state.group_id, state.lobby_message_id or 0))
                    active_tasks[state.group_id] = task
            else:
                cls._spawn_task(bot, state)
            logger.info("Restored game %s in group %s at phase %s", state.game_id, state.group_id, state.phase.value)

    @classmethod
    async def run_lobby_loop(cls, bot: Bot, group_id: int, lobby_msg_id: int = 0, duration: Optional[int] = None) -> None:
        state = cls.get_game(group_id)
        if not state or state.phase != GamePhase.LOBBY:
            return
        if duration is not None and state.phase_deadline <= time.time():
            state.phase_deadline = time.time() + max(1, duration)

        try:
            while True:
                state = cls.get_game(group_id)
                if not state or state.phase != GamePhase.LOBBY:
                    return

                if len(state.players) >= state.min_players:
                    await cls.start_if_ready(bot, state)
                    return

                remaining = max(0, int(state.phase_deadline - time.time()))
                if remaining <= 0:
                    break

                mins, secs = divmod(remaining, 60)
                text = i18n.get(
                    "lobby_title", state.group_language,
                    current=len(state.players), max=state.max_players,
                    time_left=f"{mins:02d}:{secs:02d}"
                )
                try:
                    if lobby_msg_id:
                        await bot.edit_message_text(
                            chat_id=group_id,
                            message_id=lobby_msg_id,
                            text=text,
                            reply_markup=get_lobby_keyboard(state.game_id, state.group_language, group_id=group_id),
                            parse_mode="Markdown",
                        )
                except Exception as exc:
                    logger.debug("Lobby edit skipped: %s", exc)
                await recovery_service.save_active_game(state)
                await asyncio.sleep(min(5, remaining))

            state = cls.get_game(group_id)
            if not state or state.phase != GamePhase.LOBBY:
                return
            if len(state.players) < state.min_players:
                try:
                    await bot.send_message(
                        chat_id=group_id,
                        text=i18n.get("lobby_not_enough_players", state.group_language, min=state.min_players),
                        parse_mode="Markdown",
                    )
                except Exception:
                    logger.debug("Could not send lobby cancellation message", exc_info=True)
                cls.remove_game(group_id)
                await recovery_service.clear_active_game(group_id)
                return
            await cls.run_game_loop(bot, state)
        except asyncio.CancelledError:
            raise
        except Exception:
            logger.exception("Lobby task crashed for group %s", group_id)
            cls.remove_game(group_id)
            await recovery_service.clear_active_game(group_id)

    @staticmethod
    async def _wait_until_deadline(state: GameState, group_id: int, interval: float = 1.0) -> bool:
        """Wait until the persisted phase deadline. Returns False if the game was removed."""
        while True:
            if state.group_id not in active_games:
                return False
            remaining = state.phase_deadline - time.time()
            if remaining <= 0:
                return True
            await asyncio.sleep(min(interval, remaining))

    @classmethod
    async def _create_game_record(cls, state: GameState) -> None:
        async with AsyncSessionLocal() as session:
            await GameRepository.create_game_record(session, state.game_id, state.group_id, len(state.players))
            await GameRepository.record_game_event(
                session, state.game_id, "GAME_STARTED", f"Players: {len(state.players)}"
            )
            await session.commit()

    @classmethod
    async def _send_role_messages(cls, bot: Bot, state: GameState) -> None:
        glang = state.group_language
        mafia_names = [p.display_name for p in state.players.values() if p.role == Role.MAFIA]
        team_str = "\n".join(f"• {name}" for name in mafia_names)
        try:
            await bot.send_message(
                chat_id=state.group_id,
                text=i18n.get("game_starting", glang, count=len(state.players)),
                parse_mode="Markdown",
            )
        except Exception:
            logger.debug("Could not send game-start announcement", exc_info=True)

        for player in state.players.values():
            plang = player.language_code or glang
            try:
                if player.role == Role.MAFIA:
                    text = f"{i18n.get('role_mafia_title', plang)}\n\n{i18n.get('role_mafia_desc', plang)}"
                    if len(mafia_names) > 1:
                        text += i18n.get("role_mafia_team", plang, team=team_str)
                elif player.role == Role.DOCTOR:
                    text = f"{i18n.get('role_doctor_title', plang)}\n\n{i18n.get('role_doctor_desc', plang)}"
                elif player.role == Role.COMMISSAR:
                    text = f"{i18n.get('role_commissar_title', plang)}\n\n{i18n.get('role_commissar_desc', plang)}"
                else:
                    text = f"{i18n.get('role_citizen_title', plang)}\n\n{i18n.get('role_citizen_desc', plang)}"
                await bot.send_message(chat_id=player.user_id, text=text, parse_mode="Markdown")
            except Exception:
                logger.warning("Could not send role message to %s", player.user_id, exc_info=True)

    @classmethod
    async def _announce_night(cls, bot: Bot, state: GameState) -> None:
        try:
            await bot.send_message(
                chat_id=state.group_id,
                text=f"🌙 *{state.round_number}-TUN*\n\n{i18n.get('night_started_group', state.group_language)}",
                parse_mode="Markdown",
            )
        except Exception:
            logger.debug("Could not announce night", exc_info=True)

        alive = state.alive_players
        for player in alive:
            plang = player.language_code or state.group_language
            try:
                if player.role == Role.MAFIA:
                    prompt = i18n.get("mafia_action_prompt", plang)
                    keyboard = get_night_action_keyboard(state.game_id, alive)
                elif player.role == Role.DOCTOR:
                    prompt = i18n.get("doctor_action_prompt", plang)
                    keyboard = get_night_action_keyboard(state.game_id, alive)
                elif player.role == Role.COMMISSAR:
                    prompt = i18n.get("commissar_action_prompt", plang)
                    keyboard = get_night_action_keyboard(state.game_id, alive, exclude_user_id=player.user_id)
                else:
                    continue
                await bot.send_message(chat_id=player.user_id, text=prompt, reply_markup=keyboard, parse_mode="Markdown")
            except Exception:
                logger.debug("Could not send night action to %s", player.user_id, exc_info=True)

    @classmethod
    async def _resolve_night_and_announce_morning(cls, bot: Bot, state: GameState) -> None:
        # If restored after NIGHT_RESOLUTION, do not resolve twice.
        if state.phase == GamePhase.NIGHT:
            killed_id, was_saved = GameEngine.resolve_night(state)
            await recovery_service.save_active_game(state)
            async with AsyncSessionLocal() as session:
                await GameRepository.record_game_event(
                    session, state.game_id, "NIGHT_RESOLVED", f"Killed: {killed_id}, Saved: {was_saved}"
                )
                await session.commit()

        killed_id = state.last_killed_player_id
        if killed_id:
            victim = state.get_player(killed_id)
            morning_text = i18n.get(
                "morning_killed", state.group_language,
                player=victim.display_name if victim else "Player",
                role=victim.role.value if victim and victim.role else "Citizen",
            )
        else:
            morning_text = i18n.get("morning_no_kill", state.group_language)
        try:
            await bot.send_message(chat_id=state.group_id, text=morning_text, parse_mode="Markdown")
        except Exception:
            logger.debug("Could not announce morning", exc_info=True)

    @classmethod
    async def _run_discussion(cls, bot: Bot, state: GameState) -> None:
        if state.phase != GamePhase.DISCUSSION:
            GameEngine.begin_discussion(state)
            await recovery_service.save_active_game(state)
            async with AsyncSessionLocal() as session:
                await GameRepository.record_game_event(session, state.game_id, "DISCUSSION_STARTED", f"Round {state.round_number}")
                await session.commit()
        try:
            await bot.send_message(
                chat_id=state.group_id,
                text=i18n.get("discussion_start", state.group_language, minutes=max(1, state.discussion_duration // 60)),
                parse_mode="Markdown",
            )
        except Exception:
            logger.debug("Could not announce discussion", exc_info=True)
        await cls._wait_until_deadline(state, state.group_id)

    @classmethod
    async def _send_voting_prompts(cls, bot: Bot, state: GameState) -> None:
        vote_group_text = (
            f"🗳 *{state.round_number}-RAUND: OVOZ BERISH BOSHLANDI!*\n\n"
            f"⏱ Vaqt: {state.voting_duration} soniya\n"
            "Kimni shahardan chiqarish kerakligini botning *shaxsiy chatida* tanlang!"
        )
        try:
            await bot.send_message(chat_id=state.group_id, text=vote_group_text, parse_mode="Markdown")
        except Exception:
            logger.debug("Could not announce voting", exc_info=True)
        for player in state.alive_players:
            try:
                plang = player.language_code or state.group_language
                await bot.send_message(
                    chat_id=player.user_id,
                    text=(
                        f"🗳 *{state.group_title}*\n\n"
                        f"{i18n.get('voting_title', plang, seconds=state.voting_duration)}\n"
                        "Kimni shahardan chiqarmoqchisiz?"
                    ),
                    reply_markup=get_voting_keyboard(state.game_id, state.alive_players, player.user_id),
                    parse_mode="Markdown",
                )
            except Exception:
                logger.debug("Could not send vote to %s", player.user_id, exc_info=True)

    @classmethod
    async def _run_voting(cls, bot: Bot, state: GameState, force_new: bool = False) -> tuple[Optional[int], bool, bool]:
        if force_new or state.phase != GamePhase.VOTING:
            GameEngine.begin_voting(state, attempt=state.voting_attempt or 1)
            await recovery_service.save_active_game(state)
            async with AsyncSessionLocal() as session:
                await GameRepository.record_game_event(
                    session, state.game_id, "VOTE_STARTED", f"Attempt {state.voting_attempt}"
                )
                await session.commit()
            await cls._send_voting_prompts(bot, state)

        if not await cls._wait_until_deadline(state, state.group_id):
            return None, False, False

        eliminated_id, is_tie, is_double_tie = GameEngine.resolve_voting(state)
        await recovery_service.save_active_game(state)
        async with AsyncSessionLocal() as session:
            await GameRepository.record_game_event(
                session, state.game_id, "VOTE_RESOLVED",
                f"Attempt: {state.voting_attempt}, eliminated: {eliminated_id}, tie: {is_tie}, double_tie: {is_double_tie}",
            )
            await session.commit()

        if is_tie:
            try:
                await bot.send_message(chat_id=state.group_id, text=i18n.get("vote_tie", state.group_language), parse_mode="Markdown")
            except Exception:
                pass
        elif is_double_tie:
            try:
                await bot.send_message(chat_id=state.group_id, text=i18n.get("vote_double_tie", state.group_language), parse_mode="Markdown")
            except Exception:
                pass
        elif eliminated_id:
            p = state.get_player(eliminated_id)
            try:
                await bot.send_message(
                    chat_id=state.group_id,
                    text=i18n.get(
                        "vote_eliminated", state.group_language,
                        player=p.display_name if p else "Player",
                        role=p.role.value if p and p.role else "Citizen",
                    ),
                    parse_mode="Markdown",
                )
            except Exception:
                pass
        return eliminated_id, is_tie, is_double_tie

    @classmethod
    async def run_game_loop(cls, bot: Bot, state: GameState) -> None:
        group_id = state.group_id
        try:
            # Lobby -> role assignment is only performed once.
            if state.phase == GamePhase.LOBBY:
                ok, reason = GameEngine.start_game(state)
                if not ok:
                    raise RuntimeError(f"Could not start game: {reason}")
                await cls._create_game_record(state)
                await cls._send_role_messages(bot, state)
                await recovery_service.save_active_game(state)
                await asyncio.sleep(2)

            elif state.phase == GamePhase.ROLE_ASSIGNMENT:
                # Recovery can happen after role assignment but before the first NIGHT save.
                if any(p.role is None for p in state.players.values()):
                    RoleError = RuntimeError("Recovered game has missing roles")
                    raise RoleError
                await cls._create_game_record(state)
                await cls._send_role_messages(bot, state)

            # Stable phases are resumed as-is. Transitional phases are completed exactly once.
            while True:
                if state.phase == GamePhase.GAME_OVER:
                    break

                if state.phase in (GamePhase.ROLE_ASSIGNMENT, GamePhase.GAME_START):
                    GameEngine.begin_night(state)
                    await recovery_service.save_active_game(state)
                    continue

                if state.phase == GamePhase.NIGHT:
                    await cls._announce_night(bot, state)
                    await cls._wait_until_deadline(state, group_id)
                    await cls._resolve_night_and_announce_morning(bot, state)
                    await asyncio.sleep(1)
                    winner = GameEngine.check_win_condition(state)
                    if winner:
                        await recovery_service.save_active_game(state)
                        break
                    continue

                if state.phase == GamePhase.NIGHT_RESOLUTION:
                    await cls._resolve_night_and_announce_morning(bot, state)
                    await asyncio.sleep(1)
                    winner = GameEngine.check_win_condition(state)
                    if winner:
                        await recovery_service.save_active_game(state)
                        break
                    continue

                if state.phase in (GamePhase.MORNING, GamePhase.WIN_CHECK):
                    winner = GameEngine.check_win_condition(state)
                    if winner:
                        await recovery_service.save_active_game(state)
                        break
                    await cls._run_discussion(bot, state)
                    continue

                if state.phase == GamePhase.DISCUSSION:
                    await cls._run_discussion(bot, state)
                    state.voting_attempt = 1
                    await cls._run_voting(bot, state, force_new=True)
                    continue

                if state.phase == GamePhase.VOTING:
                    await cls._run_voting(bot, state)
                    continue

                if state.phase == GamePhase.VOTE_RESOLUTION:
                    # First tie: start the second voting attempt immediately.
                    if state.tie_count > 0 and state.voting_attempt < 2:
                        state.voting_attempt = 2
                        await recovery_service.save_active_game(state)
                        await cls._run_voting(bot, state, force_new=True)
                        continue

                    winner = GameEngine.check_win_condition(state)
                    if winner:
                        await recovery_service.save_active_game(state)
                        break
                    state.round_number += 1
                    state.voting_attempt = 1
                    GameEngine.begin_night(state)
                    await recovery_service.save_active_game(state)
                    continue

                # Unknown phase: fail safely rather than silently creating a wrong new round.
                raise RuntimeError(f"Unsupported recovered game phase: {state.phase}")

            await cls.finalize_game(bot, state)
        except asyncio.CancelledError:
            raise
        except Exception:
            logger.exception("Game task crashed for group %s", group_id)
            try:
                await bot.send_message(
                    chat_id=group_id,
                    text="⚠️ O‘yin texnik xatolik sabab to‘xtadi. /resetgame buyrug‘i bilan lobby qayta ochiladi.",
                )
            except Exception:
                pass
            cls.remove_game(group_id)
            await recovery_service.clear_active_game(group_id)

    @classmethod
    async def finalize_game(cls, bot: Bot, state: GameState) -> None:
        group_id = state.group_id
        glang = state.group_language
        is_cit_win = state.winner == WinnerTeam.CITIZENS
        winner_str = i18n.get("winner_citizens", glang) if is_cit_win else i18n.get("winner_mafia", glang)

        # Idempotency: if DB already says COMPLETED, the previous attempt committed successfully.
        async with AsyncSessionLocal() as session:
            existing = await GameRepository.get_game(session, state.game_id)
            if existing and existing.status == "COMPLETED":
                cls.remove_game(group_id)
                await recovery_service.clear_active_game(group_id)
                return

        roles_lines = []
        for p in state.players.values():
            if p.role == Role.MAFIA:
                role_icon = "🔴 Mafia"
            elif p.role == Role.DOCTOR:
                role_icon = "👨‍⚕️ Doctor"
            elif p.role == Role.COMMISSAR:
                role_icon = "🕵️ Commissar"
            else:
                role_icon = "👨‍🌾 Citizen"
            status = " (Tirik)" if p.is_alive else " (☠️ Halok bo'lgan)"
            roles_lines.append(f"• {p.display_name} — {role_icon}{status}")

        mvp = state.get_player(state.mvp_player_id) if state.mvp_player_id else None
        summary = (
            f"{i18n.get('game_over_title', glang)}\n\n{winner_str}\n\n"
            f"🎭 *Rollar:*\n{chr(10).join(roles_lines)}\n\n⭐ *MVP:* {mvp.display_name if mvp else '—'}"
        )
        try:
            await bot.send_message(chat_id=group_id, text=summary, parse_mode="Markdown")
        except Exception:
            logger.error("Could not send game-over message", exc_info=True)

        async with AsyncSessionLocal() as session:
            await GameRepository.complete_game_record(
                session, state.game_id, state.winner.value if state.winner else "DRAW",
                state.round_number, state.mvp_player_id,
            )
            await GameRepository.record_game_event(
                session, state.game_id, "GAME_FINISHED",
                f"Winner: {state.winner.value if state.winner else 'DRAW'}, MVP: {mvp.display_name if mvp else '—'}",
            )
            for p in state.players.values():
                player_won = (is_cit_win and p.role != Role.MAFIA) or ((not is_cit_win) and p.role == Role.MAFIA)
                xp_earned = 20 + (50 if player_won else 0) + (50 if state.mvp_player_id == p.user_id else 0)
                xp_earned += p.saves * 25 + p.investigations * 20 + p.kills * 15 + p.correct_votes * 10
                await GameRepository.save_game_player(
                    session, state.game_id, p.user_id, p.role.value if p.role else "CITIZEN",
                    p.is_alive, p.death_round, p.death_reason, p.kills, p.saves, p.investigations, xp_earned,
                )
            await stats_service.process_game_completion(session, state)
            for p in state.players.values():
                unlocked = await achievement_service.check_and_unlock_achievements(session, p.user_id)
                for ach_id in unlocked:
                    try:
                        await bot.send_message(
                            chat_id=p.user_id,
                            text=f"🎉 *Yangi Yutuq ochildi!* 🏆\nSiz '{ach_id}' yutug'ini qo'lga kiritdingiz!",
                            parse_mode="Markdown",
                        )
                    except Exception:
                        logger.debug("Could not send achievement notification", exc_info=True)
            await session.commit()

        cls.remove_game(group_id)
        await recovery_service.clear_active_game(group_id)
