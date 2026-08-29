from typing import Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from app.database.models import UserStatistics, UserRank, GroupStatistics, GroupMember
from app.game.models import GameState, PlayerState
from app.game.enums import WinnerTeam, Role
from app.core.constants import RANKS

class StatsService:
    @staticmethod
    def calculate_rank(xp: int) -> str:
        current_rank = "Newbie"
        for name, threshold in RANKS:
            if xp >= threshold:
                current_rank = name
            else:
                break
        return current_rank

    @classmethod
    async def process_game_completion(cls, session: AsyncSession, state: GameState) -> None:
        if not state.winner:
            return

        is_citizens_win = (state.winner == WinnerTeam.CITIZENS)
        
        # 1. Update Group Stats
        group_stat = await session.get(GroupStatistics, state.group_id)
        if not group_stat:
            group_stat = GroupStatistics(group_id=state.group_id)
            session.add(group_stat)

        group_stat.total_games += 1
        group_stat.total_players_joined += len(state.players)
        if is_citizens_win:
            group_stat.citizens_wins += 1
        else:
            group_stat.mafia_wins += 1

        # 2. Update each player stats & ranks
        for player in state.players.values():
            user_id = player.user_id
            player_won = False
            if is_citizens_win and player.role != Role.MAFIA:
                player_won = True
            elif not is_citizens_win and player.role == Role.MAFIA:
                player_won = True

            # Calculate XP gained
            xp_gained = 20 # baseline participation
            if player_won:
                xp_gained += 50
            if state.mvp_player_id == player.user_id:
                xp_gained += 50
            xp_gained += player.saves * 25
            xp_gained += player.investigations * 20
            xp_gained += player.kills * 15
            xp_gained += player.correct_votes * 10

            # Update UserStatistics
            ustats = await session.get(UserStatistics, user_id)
            if not ustats:
                ustats = UserStatistics(user_id=user_id)
                session.add(ustats)

            ustats.games_played += 1
            if player_won:
                ustats.wins += 1
                ustats.win_streak += 1
                if ustats.win_streak > ustats.max_win_streak:
                    ustats.max_win_streak = ustats.win_streak
            else:
                ustats.losses += 1
                ustats.win_streak = 0

            # Role distribution counts
            if player.role == Role.MAFIA:
                ustats.mafia_games += 1
            elif player.role == Role.DOCTOR:
                ustats.doctor_games += 1
            elif player.role == Role.COMMISSAR:
                ustats.commissar_games += 1
            else:
                ustats.citizen_games += 1

            ustats.kills += player.kills
            ustats.saves += player.saves
            ustats.investigations += player.investigations
            if state.mvp_player_id == player.user_id:
                ustats.mvp_count += 1

            # Update UserRank
            urank = await session.get(UserRank, user_id)
            if not urank:
                urank = UserRank(user_id=user_id, xp=0, rank_name="Newbie")
                session.add(urank)

            urank.xp += xp_gained
            urank.rank_name = cls.calculate_rank(urank.xp)

            # Update GroupMember (per-group leaderboard)
            stmt = select(GroupMember).where(GroupMember.group_id == state.group_id, GroupMember.user_id == user_id)
            res = await session.execute(stmt)
            member = res.scalar_one_or_none()
            if not member:
                member = GroupMember(group_id=state.group_id, user_id=user_id, xp=xp_gained, games_played=1, wins=1 if player_won else 0)
                session.add(member)
            else:
                member.xp += xp_gained
                member.games_played += 1
                if player_won:
                    member.wins += 1

        await session.flush()

stats_service = StatsService()
