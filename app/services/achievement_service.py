from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database.models import UserAchievement, UserStatistics, Achievement
from app.game.models import GameState

class AchievementService:
    @staticmethod
    async def check_and_unlock_achievements(session: AsyncSession, user_id: int) -> List[str]:
        """Evaluates conditions for all achievements and unlocks any newly achieved ones."""
        ustats = await session.get(UserStatistics, user_id)
        if not ustats:
            return []

        # Get existing unlocked IDs
        stmt = select(UserAchievement.achievement_id).where(UserAchievement.user_id == user_id)
        res = await session.execute(stmt)
        unlocked_ids = set(res.scalars().all())

        newly_unlocked = []

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

        for ach_id, condition_met in conditions:
            if condition_met and ach_id not in unlocked_ids:
                new_entry = UserAchievement(user_id=user_id, achievement_id=ach_id)
                session.add(new_entry)
                newly_unlocked.append(ach_id)

        if newly_unlocked:
            await session.flush()

        return newly_unlocked

achievement_service = AchievementService()
