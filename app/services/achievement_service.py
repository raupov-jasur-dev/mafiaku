from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database.models import UserAchievement, UserStatistics, Achievement, UserRank
from app.core.constants import RANKS


class AchievementService:
    @staticmethod
    async def check_and_unlock_achievements(session: AsyncSession, user_id: int) -> List[str]:
        """Unlock newly earned achievements and grant each achievement's configured XP reward."""
        ustats = await session.get(UserStatistics, user_id)
        if not ustats:
            return []

        stmt = select(UserAchievement.achievement_id).where(UserAchievement.user_id == user_id)
        res = await session.execute(stmt)
        unlocked_ids = set(res.scalars().all())

        conditions = [
            ("first_game", ustats.games_played >= 1),
            ("10_games", ustats.games_played >= 10),
            ("mafia_hunter", ustats.kills >= 5 or ustats.investigations >= 5),
            ("doctor_hero", ustats.saves >= 3),
            ("detective", ustats.investigations >= 3),
            ("survivor", ustats.wins >= 3),
            ("5_win_streak", ustats.win_streak >= 5 or ustats.max_win_streak >= 5),
            ("10_win_streak", ustats.win_streak >= 10 or ustats.max_win_streak >= 10),
            ("mvp", ustats.mvp_count >= 1),
            ("mafia_master", ustats.mafia_games >= 10 and ustats.wins >= 5),
        ]

        newly_unlocked: List[str] = []
        rank = await session.get(UserRank, user_id)
        if not rank:
            rank = UserRank(user_id=user_id, xp=0, rank_name="Newbie")
            session.add(rank)
            await session.flush()

        for ach_id, condition_met in conditions:
            if not condition_met or ach_id in unlocked_ids:
                continue
            achievement = await session.get(Achievement, ach_id)
            if not achievement:
                continue
            session.add(UserAchievement(user_id=user_id, achievement_id=ach_id))
            rank.xp += int(achievement.xp_reward or 0)
            rank.rank_name = next((name for name, threshold in reversed(RANKS) if rank.xp >= threshold), "Newbie")
            newly_unlocked.append(ach_id)

        await session.flush()
        return newly_unlocked


achievement_service = AchievementService()
