import time
import uuid
from typing import Dict, List, Optional, Tuple
from collections import Counter

from app.game.enums import GamePhase, Role, WinnerTeam
from app.game.models import GameState, PlayerState
from app.game.role_distributor import RoleDistributor

class GameEngine:
    """
    Pure authoritative state machine and rules engine for Mafia.
    Completely decoupled from Telegram I/O for 100% testability and reliability.
    """

    @staticmethod
    def create_game(group_id: int, group_title: str, lobby_duration: int = 180, group_language: str = "uz") -> GameState:
        game_id = str(uuid.uuid4())
        state = GameState(
            game_id=game_id,
            group_id=group_id,
            group_title=group_title,
            group_language=group_language,
            phase=GamePhase.LOBBY,
            phase_started_at=time.time(),
            phase_deadline=time.time() + lobby_duration,
        )
        return state

    @staticmethod
    def add_player(state: GameState, user_id: int, full_name: str, username: Optional[str] = None, language_code: str = "uz") -> Tuple[bool, str]:
        if state.phase != GamePhase.LOBBY:
            return False, "LOBBY_CLOSED"
        if user_id in state.players:
            return False, "ALREADY_JOINED"
        if len(state.players) >= 20:
            return False, "LOBBY_FULL"

        player = PlayerState(
            user_id=user_id,
            full_name=full_name,
            username=username,
            language_code=language_code or "uz",
            joined_at=time.time()
        )
        state.players[user_id] = player
        return True, "JOINED"

    @staticmethod
    def remove_player(state: GameState, user_id: int) -> Tuple[bool, str]:
        if user_id not in state.players:
            return False, "PLAYER_NOT_FOUND"

        if state.phase == GamePhase.LOBBY:
            del state.players[user_id]
            return True, "REMOVED_FROM_LOBBY"

        player = state.players[user_id]
        if player.is_alive:
            player.is_alive = False
            return True, "PLAYER_KILLED_ON_LEAVE"
        return True, "ALREADY_DEAD"

    @staticmethod
    def start_game(state: GameState, seed: Optional[int] = None) -> Tuple[bool, str]:
        if state.phase != GamePhase.LOBBY:
            return False, "INVALID_PHASE"
        if len(state.players) < 4:
            return False, "NOT_ENOUGH_PLAYERS"

        state.phase = GamePhase.ROLE_ASSIGNMENT
        players_list = list(state.players.values())
        RoleDistributor.assign_roles(players_list, seed=seed)
        return True, "ROLES_ASSIGNED"

    @staticmethod
    def begin_night(state: GameState, duration: int = 45) -> GamePhase:
        state.phase = GamePhase.NIGHT
        state.phase_started_at = time.time()
        state.phase_deadline = time.time() + duration
        state.mafia_votes.clear()
        state.doctor_target_id = None
        state.commissar_target_id = None
        state.last_killed_player_id = None
        
        # Reset current turn actions
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
    def record_commissar_target(state: GameState, actor_id: int, target_id: int) -> Tuple[bool, Optional[bool], str]:
        """Returns (success, is_mafia, message)"""
        if state.phase != GamePhase.NIGHT:
            return False, None, "NOT_NIGHT"
        actor = state.get_player(actor_id)
        if not actor or not actor.is_alive or actor.role != Role.COMMISSAR:
            return False, None, "UNAUTHORIZED"
        target = state.get_player(target_id)
        if not target or not target.is_alive:
            return False, None, "INVALID_TARGET"

        actor.night_action_target = target_id
        actor.investigations += 1
        state.commissar_target_id = target_id
        is_mafia = (target.role == Role.MAFIA)
        return True, is_mafia, "INVESTIGATED"

    @classmethod
    def resolve_night(cls, state: GameState) -> Tuple[Optional[int], bool]:
        """
        Resolves night actions deterministically.
        Returns: (killed_player_id, was_saved_by_doctor)
        """
        state.phase = GamePhase.NIGHT_RESOLUTION
        
        # 1. Determine Mafia target
        mafia_target_id: Optional[int] = None
        if state.mafia_votes:
            # Count targets
            counts = Counter(state.mafia_votes.values())
            # Select target with most votes
            most_common = counts.most_common(1)
            if most_common:
                mafia_target_id = most_common[0][0]

        # 2. Check Doctor protection
        was_saved = False
        killed_id: Optional[int] = None

        if mafia_target_id:
            if state.doctor_target_id and state.doctor_target_id == mafia_target_id:
                was_saved = True
                # Reward doctor
                for p in state.players.values():
                    if p.role == Role.DOCTOR and p.is_alive:
                        p.saves += 1
            else:
                # Target is killed
                target_player = state.get_player(mafia_target_id)
                if target_player and target_player.is_alive:
                    target_player.is_alive = False
                    killed_id = mafia_target_id
                    # Reward active mafias
                    for m_id in state.mafia_votes:
                        m_player = state.get_player(m_id)
                        if m_player:
                            m_player.kills += 1

        state.last_killed_player_id = killed_id
        return killed_id, was_saved

    @staticmethod
    def begin_discussion(state: GameState, duration: int = 120) -> GamePhase:
        state.phase = GamePhase.DISCUSSION
        state.phase_started_at = time.time()
        state.phase_deadline = time.time() + duration
        return state.phase

    @staticmethod
    def begin_voting(state: GameState, duration: int = 45) -> GamePhase:
        state.phase = GamePhase.VOTING
        state.phase_started_at = time.time()
        state.phase_deadline = time.time() + duration
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
        """
        Calculates vote outcomes.
        Returns: (eliminated_player_id, is_tie, is_double_tie)
        """
        state.phase = GamePhase.VOTE_RESOLUTION
        
        votes = [p.vote_target for p in state.alive_players if p.vote_target is not None]
        if not votes:
            # Nobody voted -> treated as tie/no execution
            state.tie_count += 1
            if state.tie_count >= 2:
                state.tie_count = 0
                return None, False, True
            return None, True, False

        counts = Counter(votes)
        most_common = counts.most_common(2)

        # Check for tie
        if len(most_common) > 1 and most_common[0][1] == most_common[1][1]:
            state.tie_count += 1
            if state.tie_count >= 2:
                # Second tie in a row -> nobody eliminated today
                state.tie_count = 0
                return None, False, True
            return None, True, False

        # Clear tie count on definitive outcome
        state.tie_count = 0
        eliminated_id = most_common[0][0]
        eliminated_player = state.get_player(eliminated_id)
        if eliminated_player and eliminated_player.is_alive:
            eliminated_player.is_alive = False
            # Reward voters who voted correctly for Mafia
            if eliminated_player.role == Role.MAFIA:
                for p in state.alive_players:
                    if p.vote_target == eliminated_id:
                        p.correct_votes += 1

        return eliminated_id, False, False

    @classmethod
    def check_win_condition(cls, state: GameState) -> Optional[WinnerTeam]:
        """
        Win Conditions:
        - Citizens win: All Mafia members are eliminated (alive_mafia == 0)
        - Mafia win: Mafia count >= alive non-mafia count
        """
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
        """
        Calculates match MVP based on dynamic gameplay impact:
        - Team Victory: +30
        - Doctor Saves: +25 per save
        - Commissar Successful Investigations: +20 each
        - Mafia Kills: +15 each
        - Correct Daytime Votes: +10 each
        - Survival: +15
        """
        best_player: Optional[PlayerState] = None
        highest_score = -1

        for player in state.players.values():
            score = 0
            # Victory bonus
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

            if score > highest_score:
                highest_score = score
                best_player = player

        if best_player:
            state.mvp_player_id = best_player.user_id
        return best_player
