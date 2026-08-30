import json
import logging
from typing import List, Optional
from app.game.models import GameState, PlayerState
from app.game.enums import GamePhase, Role, WinnerTeam
from app.services.redis_service import redis_service

logger = logging.getLogger(__name__)


class RecoveryService:
    """Persists active games in Redis and restores them after process restarts."""

    @staticmethod
    def serialize_game(state: GameState) -> str:
        data = {
            "game_id": state.game_id,
            "group_id": state.group_id,
            "group_title": state.group_title,
            "group_language": state.group_language,
            "lobby_message_id": state.lobby_message_id,
            "voting_message_id": state.voting_message_id,
            "discussion_message_id": state.discussion_message_id,
            "phase": state.phase.value,
            "lobby_duration": state.lobby_duration,
            "discussion_duration": state.discussion_duration,
            "voting_duration": state.voting_duration,
            "night_duration": state.night_duration,
            "min_players": state.min_players,
            "max_players": state.max_players,
            "auto_start_delay": state.auto_start_delay,
            "round_number": state.round_number,
            "phase_started_at": state.phase_started_at,
            "phase_deadline": state.phase_deadline,
            "tie_count": state.tie_count,
            "voting_attempt": state.voting_attempt,
            "last_killed_player_id": state.last_killed_player_id,
            "winner": state.winner.value if state.winner else None,
            "mvp_player_id": state.mvp_player_id,
            "mafia_votes": state.mafia_votes,
            "doctor_target_id": state.doctor_target_id,
            "commissar_target_id": state.commissar_target_id,
            "players": {
                str(p.user_id): {
                    "user_id": p.user_id,
                    "full_name": p.full_name,
                    "username": p.username,
                    "language_code": p.language_code,
                    "role": p.role.value if p.role else None,
                    "is_alive": p.is_alive,
                    "joined_at": p.joined_at,
                    "night_action_target": p.night_action_target,
                    "vote_target": p.vote_target,
                    "kills": p.kills,
                    "saves": p.saves,
                    "investigations": p.investigations,
                    "correct_votes": p.correct_votes,
                    "death_round": p.death_round,
                    "death_reason": p.death_reason,
                }
                for p in state.players.values()
            },
        }
        return json.dumps(data, separators=(",", ":"))

    @staticmethod
    def deserialize_game(raw: str) -> Optional[GameState]:
        try:
            data = json.loads(raw)
            state = GameState(
                game_id=data["game_id"],
                group_id=int(data["group_id"]),
                group_title=data["group_title"],
                group_language=data.get("group_language", "uz"),
                lobby_message_id=data.get("lobby_message_id"),
                voting_message_id=data.get("voting_message_id"),
                discussion_message_id=data.get("discussion_message_id"),
                phase=GamePhase(data["phase"]),
                lobby_duration=int(data.get("lobby_duration", 180)),
                discussion_duration=int(data.get("discussion_duration", 120)),
                voting_duration=int(data.get("voting_duration", 45)),
                night_duration=int(data.get("night_duration", 45)),
                min_players=int(data.get("min_players", 4)),
                max_players=int(data.get("max_players", 20)),
                auto_start_delay=int(data.get("auto_start_delay", 5)),
                round_number=int(data.get("round_number", 1)),
                phase_started_at=float(data.get("phase_started_at", 0)),
                phase_deadline=float(data.get("phase_deadline", 0)),
                tie_count=int(data.get("tie_count", 0)),
                voting_attempt=int(data.get("voting_attempt", 1)),
                last_killed_player_id=data.get("last_killed_player_id"),
                winner=WinnerTeam(data["winner"]) if data.get("winner") else None,
                mvp_player_id=data.get("mvp_player_id"),
                mafia_votes={int(k): int(v) for k, v in data.get("mafia_votes", {}).items()},
                doctor_target_id=data.get("doctor_target_id"),
                commissar_target_id=data.get("commissar_target_id"),
            )
            for pdata in data.get("players", {}).values():
                p = PlayerState(
                    user_id=int(pdata["user_id"]),
                    full_name=pdata.get("full_name", ""),
                    username=pdata.get("username"),
                    language_code=pdata.get("language_code", "uz"),
                    role=Role(pdata["role"]) if pdata.get("role") else None,
                    is_alive=pdata.get("is_alive", True),
                    joined_at=float(pdata.get("joined_at", 0)),
                    night_action_target=pdata.get("night_action_target"),
                    vote_target=pdata.get("vote_target"),
                    kills=int(pdata.get("kills", 0)),
                    saves=int(pdata.get("saves", 0)),
                    investigations=int(pdata.get("investigations", 0)),
                    correct_votes=int(pdata.get("correct_votes", 0)),
                    death_round=pdata.get("death_round"),
                    death_reason=pdata.get("death_reason"),
                )
                state.players[p.user_id] = p
            return state
        except Exception:
            logger.exception("Failed to deserialize game state")
            return None

    @classmethod
    async def save_active_game(cls, state: GameState) -> None:
        await redis_service.set(f"active_game:{state.group_id}", cls.serialize_game(state), ex=86400)

    @classmethod
    async def load_active_game(cls, group_id: int) -> Optional[GameState]:
        raw = await redis_service.get(f"active_game:{group_id}")
        return cls.deserialize_game(raw) if raw else None

    @classmethod
    async def get_all_saved_games(cls) -> List[GameState]:
        games: List[GameState] = []
        try:
            keys = await redis_service.keys("active_game:*")
            for key in keys:
                raw = await redis_service.get(key)
                if raw:
                    state = cls.deserialize_game(raw)
                    if state:
                        games.append(state)
        except Exception:
            logger.exception("Could not load all saved games")
        return games

    @classmethod
    async def clear_active_game(cls, group_id: int) -> None:
        await redis_service.delete(f"active_game:{group_id}")


recovery_service = RecoveryService()
