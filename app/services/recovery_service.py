import json
import logging
from typing import Dict, Optional, List
from app.game.models import GameState, PlayerState
from app.game.enums import GamePhase, Role, WinnerTeam
from app.services.redis_service import redis_service

logger = logging.getLogger(__name__)

class RecoveryService:
    """Saves and restores active game state to withstand server reboots."""
    
    @staticmethod
    def serialize_game(state: GameState) -> str:
        data = {
            "game_id": state.game_id,
            "group_id": state.group_id,
            "group_title": state.group_title,
            "group_language": state.group_language,
            "lobby_message_id": state.lobby_message_id,
            "voting_message_id": state.voting_message_id,
            "phase": state.phase.value,
            "round_number": state.round_number,
            "phase_started_at": state.phase_started_at,
            "phase_deadline": state.phase_deadline,
            "tie_count": state.tie_count,
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
                }
                for p in state.players.values()
            }
        }
        return json.dumps(data)

    @staticmethod
    def deserialize_game(raw: str) -> Optional[GameState]:
        try:
            data = json.loads(raw)
            state = GameState(
                game_id=data["game_id"],
                group_id=data["group_id"],
                group_title=data["group_title"],
                group_language=data.get("group_language", "uz"),
                lobby_message_id=data.get("lobby_message_id"),
                voting_message_id=data.get("voting_message_id"),
                phase=GamePhase(data["phase"]),
                round_number=data.get("round_number", 1),
                phase_started_at=data.get("phase_started_at", 0),
                phase_deadline=data.get("phase_deadline", 0),
                tie_count=data.get("tie_count", 0),
                last_killed_player_id=data.get("last_killed_player_id"),
                winner=WinnerTeam(data["winner"]) if data.get("winner") else None,
                mvp_player_id=data.get("mvp_player_id"),
                mafia_votes={int(k): v for k, v in data.get("mafia_votes", {}).items()},
                doctor_target_id=data.get("doctor_target_id"),
                commissar_target_id=data.get("commissar_target_id"),
            )
            for uid_str, pdata in data.get("players", {}).items():
                p = PlayerState(
                    user_id=pdata["user_id"],
                    full_name=pdata["full_name"],
                    username=pdata.get("username"),
                    language_code=pdata.get("language_code", "uz"),
                    role=Role(pdata["role"]) if pdata.get("role") else None,
                    is_alive=pdata.get("is_alive", True),
                    joined_at=pdata.get("joined_at", 0),
                    night_action_target=pdata.get("night_action_target"),
                    vote_target=pdata.get("vote_target"),
                    kills=pdata.get("kills", 0),
                    saves=pdata.get("saves", 0),
                    investigations=pdata.get("investigations", 0),
                    correct_votes=pdata.get("correct_votes", 0),
                )
                state.players[p.user_id] = p
            return state
        except Exception as e:
            logger.error(f"Failed to deserialize game state: {e}")
            return None

    @classmethod
    async def save_active_game(cls, state: GameState) -> None:
        key = f"active_game:{state.group_id}"
        serialized = cls.serialize_game(state)
        await redis_service.set(key, serialized, ex=86400) # 24h retention

    @classmethod
    async def load_active_game(cls, group_id: int) -> Optional[GameState]:
        key = f"active_game:{group_id}"
        raw = await redis_service.get(key)
        if raw:
            return cls.deserialize_game(raw)
        return None

    @classmethod
    async def get_all_saved_games(cls) -> List[GameState]:
        """Scans Redis for active_game:* and deserializes all existing games."""
        games = []
        try:
            if hasattr(redis_service._client, "keys"):
                keys = await redis_service._client.keys("active_game:*")
                for key in keys:
                    raw = await redis_service._client.get(key)
                    if raw:
                        state = cls.deserialize_game(raw)
                        if state:
                            games.append(state)
        except Exception as e:
            logger.error(f"Could not load all saved games: {e}")
        return games

    @classmethod
    async def clear_active_game(cls, group_id: int) -> None:
        key = f"active_game:{group_id}"
        await redis_service.delete(key)

recovery_service = RecoveryService()
