import random
from typing import Dict, List
from app.game.enums import Role
from app.game.models import PlayerState

class RoleDistributor:
    """
    Deterministically and fairly distributes roles among 4-20 players.
    Roles:
    - 🔴 MAFIA
    - 👨‍⚕️ DOCTOR
    - 🕵️ COMMISSAR
    - 👨‍🌾 CITIZEN
    """

    @staticmethod
    def calculate_role_counts(player_count: int) -> Dict[Role, int]:
        if player_count < 4:
            raise ValueError("Minimum 4 players required to play Mafia.")
        
        # Mafia scaling table:
        # 4-5 players: 1 Mafia
        # 6-8 players: 2 Mafia
        # 9-12 players: 3 Mafia
        # 13-16 players: 4 Mafia
        # 17-20 players: 5 Mafia
        if player_count <= 5:
            mafia_count = 1
        elif player_count <= 8:
            mafia_count = 2
        elif player_count <= 12:
            mafia_count = 3
        elif player_count <= 16:
            mafia_count = 4
        else:
            mafia_count = 5

        doctor_count = 1
        commissar_count = 1
        citizen_count = player_count - (mafia_count + doctor_count + commissar_count)

        return {
            Role.MAFIA: mafia_count,
            Role.DOCTOR: doctor_count,
            Role.COMMISSAR: commissar_count,
            Role.CITIZEN: citizen_count,
        }

    @classmethod
    def assign_roles(cls, players: List[PlayerState], seed: int = None) -> List[PlayerState]:
        count = len(players)
        role_counts = cls.calculate_role_counts(count)
        
        role_pool: List[Role] = []
        for role, num in role_counts.items():
            role_pool.extend([role] * num)

        rng = random.Random(seed) if seed is not None else random.Random()
        rng.shuffle(role_pool)

        for player, role in zip(players, role_pool):
            player.role = role
            player.is_alive = True
            player.night_action_target = None
            player.vote_target = None

        return players
