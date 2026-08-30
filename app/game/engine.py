import time
import uuid
from typing import Dict, List, Optional, Tuple
from collections import Counter

from app.game.enums import GamePhase, Role, WinnerTeam
from app.game.models import GameState, PlayerState
from app.game.role_distributor import RoleDistributor


class GameEngine:
    """Authoritative, Telegram-independent Mafia rules engine."""

    @staticmethod
    def create_game(
        group_id: int,
        group_title: str,
        lobby_duration: int = 180,
        group_language: str = "uz",
        discussion_duration: int = 120,
        voting_duration: int = 45,
        night_duration: int = 45,
        min_players: int = 4,
        max_players: int = 20,
        auto_start_delay: int = 5,
    ) -> GameState:
        if min_players < 4:
            raise ValueError("Minimum players cannot be below 4.")
        if max_players < min_players:
            raise ValueError("Maximum players must be >= minimum players.")
        now = time.time()
        return GameState(
            game_id=str(uuid.uuid4()),
            group_id=group_id,
            group_title=group_title,
            group_language=group_language,
            phase=GamePhase.LOBBY,
            phase_started_at=now,
            phase_deadline=now + max(1, lobby_duration),
            lobby_duration=max(1, lobby_duration),
            discussion_duration=max(1, discussion_duration),
            voting_duration=max(1, voting_duration),
            night_duration=max(1, night_duration),
            min_players=min_players,
            max_players=max_players,
            auto_start_delay=max(0, auto_start_delay),
        )

    @staticmethod
    def add_player(
        state: GameState,
        user_id: int,
        full_name: str,
        username: Optional[str] = None,
        language_code: str = "uz",
    ) -> Tuple[bool, str]:
        if state.phase != GamePhase.LOBBY:
            return False, "LOBBY_CLOSED"
        if user_id in state.players:
            return False, "ALREADY_JOINED"
        if len(state.players) >= state.max_players:
            return False, "LOBBY_FULL"

        state.players[user_id] = PlayerState(
            user_id=user_id,
            full_name=full_name,
            username=username,
            language_code=language_code or "uz",
            joined_at=time.time(),
        )
        return True, "JOINED"

    @staticmethod
    def remove_player(state: GameState, user_id: int) -> Tuple[bool, str]:
        player = state.get_player(user_id)
        if not player:
            return False, "PLAYER_NOT_FOUND"

        if state.phase == GamePhase.LOBBY:
            del state.players[user_id]
            return True, "REMOVED_FROM_LOBBY"

        if player.is_alive:
            player.is_alive = False
            player.death_round = state.round_number
            player.death_reason = "DISCONNECTED"
            return True, "PLAYER_KILLED_ON_LEAVE"
        return True, "ALREADY_DEAD"

    @staticmethod
    def start_game(state: GameState, seed: Optional[int] = None) -> Tuple[bool, str]:
        if state.phase != GamePhase.LOBBY:
            return False, "INVALID_PHASE"
        if len(state.players) < state.min_players:
            return False, "NOT_ENOUGH_PLAYERS"

        state.phase = GamePhase.ROLE_ASSIGNMENT
        RoleDistributor.assign_roles(list(state.players.values()), seed=seed)
        return True, "ROLES_ASSIGNED"

    @staticmethod
    def begin_night(state: GameState, duration: Optional[int] = None) -> GamePhase:
        duration = state.night_duration if duration is None else duration
        now = time.time()
        state.phase = GamePhase.NIGHT
        state.phase_started_at = now
        state.phase_deadline = now + max(1, duration)
        state.mafia_votes.clear()
        state.doctor_target_id = None
        state.commissar_target_id = None
        state.last_killed_player_id = None
        for p in state.players.values():
            p.night_action_target = None
        return state.phase

    @staticmethod
    def record_mafia_target(state: GameState, actor_id: int, target_id: int) -> Tuple[bool, str]:
        if state.phase != GamePhase.NIGHT:
            return False, "NOT_NIGHT"
        actor = state.get_player(actor_id)
        if not actor or not actor.is_alive or actor.role != Role.MAFIA:
            return False, "UNAUTHORIZED"
        target = state.get_player(target_id)
        if not target or not target.is_alive:
            return False, "INVALID_TARGET"
        if target.role == Role.MAFIA:
            return False, "CANNOT_TARGET_TEAMMATE"

        actor.night_action_target = target_id
        state.mafia_votes[actor_id] = target_id
        return True, "TARGET_RECORDED"

    @staticmethod
    def record_doctor_target(state: GameState, actor_id: int, target_id: int) -> Tuple[bool, str]:
        if state.phase != GamePhase.NIGHT:
            return False, "NOT_NIGHT"
        actor = state.get_player(actor_id)
        if not actor or not actor.is_alive or actor.role != Role.DOCTOR:
            return False, "UNAUTHORIZED"
        target = state.get_player(target_id)
        if not target or not target.is_alive:
            return False, "INVALID_TARGET"

        actor.night_action_target = target_id
        state.doctor_target_id = target_id
        return True, "TARGET_RECORDED"

    @staticmethod
    def record_commissar_target(
        state: GameState, actor_id: int, target_id: int
    ) -> Tuple[bool, Optional[bool], str]:
        if state.phase != GamePhase.NIGHT:
            return False, None, "NOT_NIGHT"
        actor = state.get_player(actor_id)
        if not actor or not actor.is_alive or actor.role != Role.COMMISSAR:
            return False, None, "UNAUTHORIZED"
        if actor.night_action_target is not None:
            return False, None, "ALREADY_INVESTIGATED"
        target = state.get_player(target_id)
        if not target or not target.is_alive:
            return False, None, "INVALID_TARGET"
        if target_id == actor_id:
            return False, None, "INVALID_TARGET"

        actor.night_action_target = target_id
        actor.investigations += 1
        state.commissar_target_id = target_id
        return True, target.role == Role.MAFIA, "INVESTIGATED"

    @classmethod
    def resolve_night(cls, state: GameState) -> Tuple[Optional[int], bool]:
        state.phase = GamePhase.NIGHT_RESOLUTION
        mafia_target_id: Optional[int] = None
        if state.mafia_votes:
            counts = Counter(state.mafia_votes.values())
            max_votes = max(counts.values())
            # Explicit deterministic tie-break: lowest user ID wins.
            candidates = [uid for uid, count in counts.items() if count == max_votes]
            mafia_target_id = min(candidates)

        was_saved = False
        killed_id: Optional[int] = None
        if mafia_target_id:
            if state.doctor_target_id == mafia_target_id:
                was_saved = True
                for p in state.players.values():
                    if p.role == Role.DOCTOR and p.is_alive:
                        p.saves += 1
            else:
                target_player = state.get_player(mafia_target_id)
                if target_player and target_player.is_alive:
                    target_player.is_alive = False
                    target_player.death_round = state.round_number
                    target_player.death_reason = "NIGHT_KILL"
                    killed_id = mafia_target_id
                    for m_id in state.mafia_votes:
                        m_player = state.get_player(m_id)
                        if m_player and m_player.is_alive:
                            m_player.kills += 1

        state.last_killed_player_id = killed_id
        return killed_id, was_saved

    @staticmethod
    def begin_discussion(state: GameState, duration: Optional[int] = None) -> GamePhase:
        duration = state.discussion_duration if duration is None else duration
        now = time.time()
        state.phase = GamePhase.DISCUSSION
        state.phase_started_at = now
        state.phase_deadline = now + max(1, duration)
        return state.phase

    @staticmethod
    def begin_voting(state: GameState, duration: Optional[int] = None, attempt: int = 1) -> GamePhase:
        duration = state.voting_duration if duration is None else duration
        now = time.time()
        state.phase = GamePhase.VOTING
        state.phase_started_at = now
        state.phase_deadline = now + max(1, duration)
        state.voting_attempt = attempt
        for p in state.players.values():
            p.vote_target = None
        return state.phase

    @staticmethod
    def record_vote(state: GameState, voter_id: int, target_id: int) -> Tuple[bool, str]:
        if state.phase != GamePhase.VOTING:
            return False, "NOT_VOTING_PHASE"
        voter = state.get_player(voter_id)
        if not voter or not voter.is_alive:
            return False, "DEAD_CANNOT_VOTE"
        if voter_id == target_id:
            return False, "CANNOT_VOTE_SELF"
        target = state.get_player(target_id)
        if not target or not target.is_alive:
            return False, "INVALID_TARGET"
        if voter.vote_target is not None:
            return False, "ALREADY_VOTED"
        voter.vote_target = target_id
        return True, "VOTE_RECORDED"

    @classmethod
    def resolve_voting(cls, state: GameState) -> Tuple[Optional[int], bool, bool]:
        state.phase = GamePhase.VOTE_RESOLUTION
        votes = [p.vote_target for p in state.alive_players if p.vote_target is not None]
        if not votes:
            state.tie_count += 1
            if state.tie_count >= 2:
                state.tie_count = 0
                return None, False, True
            return None, True, False

        counts = Counter(votes)
        max_votes = max(counts.values())
        candidates = sorted(uid for uid, count in counts.items() if count == max_votes)
        if len(candidates) > 1:
            state.tie_count += 1
            if state.tie_count >= 2:
                state.tie_count = 0
                return None, False, True
            return None, True, False

        state.tie_count = 0
        eliminated_id = candidates[0]
        eliminated_player = state.get_player(eliminated_id)
        if eliminated_player and eliminated_player.is_alive:
            eliminated_player.is_alive = False
            eliminated_player.death_round = state.round_number
            eliminated_player.death_reason = "VOTED_OUT"
            if eliminated_player.role == Role.MAFIA:
                for p in state.alive_players:
                    if p.vote_target == eliminated_id:
                        p.correct_votes += 1
        return eliminated_id, False, False

    @classmethod
    def check_win_condition(cls, state: GameState) -> Optional[WinnerTeam]:
        state.phase = GamePhase.WIN_CHECK
        alive_maf = len(state.alive_mafia)
        alive_cit = len(state.alive_citizens)
        if alive_maf == 0:
            state.winner = WinnerTeam.CITIZENS
            state.phase = GamePhase.GAME_OVER
            cls.calculate_mvp(state)
            return WinnerTeam.CITIZENS
        if alive_maf >= alive_cit:
            state.winner = WinnerTeam.MAFIA
            state.phase = GamePhase.GAME_OVER
            cls.calculate_mvp(state)
            return WinnerTeam.MAFIA
        return None

    @classmethod
    def calculate_mvp(cls, state: GameState) -> Optional[PlayerState]:
        best_player: Optional[PlayerState] = None
        highest_score = -1
        for player in state.players.values():
            score = 0
            if state.winner == WinnerTeam.MAFIA and player.role == Role.MAFIA:
                score += 30
            elif state.winner == WinnerTeam.CITIZENS and player.role != Role.MAFIA:
                score += 30
            score += player.saves * 25
            score += player.investigations * 20
            score += player.kills * 15
            score += player.correct_votes * 10
            if player.is_alive:
                score += 15
            # Stable tie-breaker: lower Telegram user ID wins.
            if score > highest_score or (score == highest_score and (best_player is None or player.user_id < best_player.user_id)):
                highest_score = score
                best_player = player
        if best_player:
            state.mvp_player_id = best_player.user_id
        return best_player
