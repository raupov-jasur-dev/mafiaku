from dataclasses import dataclass, field
from typing import Dict, List, Optional
import time
from app.game.enums import GamePhase, Role, WinnerTeam


@dataclass
class PlayerState:
    user_id: int
    full_name: str
    username: Optional[str] = None
    role: Optional[Role] = None
    is_alive: bool = True
    joined_at: float = field(default_factory=time.time)
    language_code: str = "uz"

    # Stats within match
    night_action_target: Optional[int] = None
    vote_target: Optional[int] = None
    kills: int = 0
    saves: int = 0
    investigations: int = 0
    correct_votes: int = 0

    # Persistent game-result metadata kept in Redis until finalization.
    death_round: Optional[int] = None
    death_reason: Optional[str] = None

    @property
    def display_name(self) -> str:
        if self.username:
            return f"@{self.username}"
        return self.full_name or f"Player {self.user_id}"


@dataclass
class GameState:
    game_id: str
    group_id: int
    group_title: str
    group_language: str = "uz"
    lobby_message_id: Optional[int] = None
    phase: GamePhase = GamePhase.LOBBY
    players: Dict[int, PlayerState] = field(default_factory=dict)

    # Per-game configuration is persisted in Redis so recovery uses the same rules.
    lobby_duration: int = 180
    discussion_duration: int = 120
    voting_duration: int = 45
    night_duration: int = 45
    min_players: int = 4
    max_players: int = 20
    auto_start_delay: int = 5

    # Round tracking
    round_number: int = 1
    phase_started_at: float = field(default_factory=time.time)
    phase_deadline: float = field(default_factory=time.time)

    # Voting & tie status
    tie_count: int = 0
    voting_attempt: int = 1
    last_killed_player_id: Optional[int] = None
    winner: Optional[WinnerTeam] = None
    mvp_player_id: Optional[int] = None

    # Night actions cache for current night
    mafia_votes: Dict[int, int] = field(default_factory=dict)
    doctor_target_id: Optional[int] = None
    commissar_target_id: Optional[int] = None

    # Discussion & voting messages
    discussion_message_id: Optional[int] = None
    voting_message_id: Optional[int] = None

    @property
    def alive_players(self) -> List[PlayerState]:
        return [p for p in self.players.values() if p.is_alive]

    @property
    def dead_players(self) -> List[PlayerState]:
        return [p for p in self.players.values() if not p.is_alive]

    @property
    def alive_mafia(self) -> List[PlayerState]:
        return [p for p in self.alive_players if p.role == Role.MAFIA]

    @property
    def alive_citizens(self) -> List[PlayerState]:
        return [p for p in self.alive_players if p.role != Role.MAFIA]

    def get_player(self, user_id: int) -> Optional[PlayerState]:
        return self.players.get(user_id)
