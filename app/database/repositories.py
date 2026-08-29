from typing import Optional, List, Dict, Any
from datetime import datetime
from sqlalchemy import select, update, func, desc
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.models import (
    User, Group, GroupMember, Game, GamePlayer, 
    UserStatistics, GroupStatistics, UserRank, 
    UserSettings, GroupSettings, UserAchievement, Achievement, AuditLog
)
from app.core.constants import RANKS

class UserRepository:
    @staticmethod
    async def get_or_create(session: AsyncSession, user_id: int, first_name: str, last_name: Optional[str] = None, username: Optional[str] = None, language_code: str = "uz") -> User:
        user = await session.get(User, user_id)
        if not user:
            user = User(
                id=user_id,
                first_name=first_name,
                last_name=last_name,
                username=username,
                language_code=language_code or "uz"
            )
            session.add(user)
            
            # Init stats, settings, and rank
            stats = UserStatistics(user_id=user_id)
            settings = UserSettings(user_id=user_id, language=language_code or "uz")
            rank = UserRank(user_id=user_id, xp=0, rank_name="Newbie")
            
            session.add_all([stats, settings, rank])
            await session.flush()
        else:
            # Update user info if changed
            user.first_name = first_name
            user.last_name = last_name
            user.username = username
            await session.flush()
        return user

    @staticmethod
    async def get_user(session: AsyncSession, user_id: int) -> Optional[User]:
        return await session.get(User, user_id)

    @staticmethod
    async def get_user_stats(session: AsyncSession, user_id: int) -> Optional[UserStatistics]:
        return await session.get(UserStatistics, user_id)

    @staticmethod
    async def get_user_rank(session: AsyncSession, user_id: int) -> Optional[UserRank]:
        return await session.get(UserRank, user_id)

    @staticmethod
    async def get_user_settings(session: AsyncSession, user_id: int) -> Optional[UserSettings]:
        return await session.get(UserSettings, user_id)

    @staticmethod
    async def update_language(session: AsyncSession, user_id: int, language: str) -> None:
        stmt = update(UserSettings).where(UserSettings.user_id == user_id).values(language=language, updated_at=datetime.utcnow())
        await session.execute(stmt)
        user = await session.get(User, user_id)
        if user:
            user.language_code = language
        await session.flush()

    @staticmethod
    async def toggle_notifications(session: AsyncSession, user_id: int) -> bool:
        settings = await session.get(UserSettings, user_id)
        if not settings:
            settings = UserSettings(user_id=user_id, notifications_enabled=False)
            session.add(settings)
            new_val = False
        else:
            settings.notifications_enabled = not settings.notifications_enabled
            settings.updated_at = datetime.utcnow()
            new_val = settings.notifications_enabled
        await session.flush()
        return new_val

class GroupRepository:
    @staticmethod
    async def get_or_create(session: AsyncSession, group_id: int, title: str, username: Optional[str] = None, bot_is_admin: bool = False) -> Group:
        group = await session.get(Group, group_id)
        if not group:
            group = Group(
                id=group_id,
                title=title,
                username=username,
                bot_is_admin=bot_is_admin
            )
            session.add(group)
            
            settings = GroupSettings(group_id=group_id)
            stats = GroupStatistics(group_id=group_id)
            session.add_all([settings, stats])
            await session.flush()
        else:
            group.title = title
            group.username = username
            group.bot_is_admin = bot_is_admin
            await session.flush()
        return group

    @staticmethod
    async def get_group(session: AsyncSession, group_id: int) -> Optional[Group]:
        return await session.get(Group, group_id)

    @staticmethod
    async def get_group_settings(session: AsyncSession, group_id: int) -> Optional[GroupSettings]:
        return await session.get(GroupSettings, group_id)

    @staticmethod
    async def get_group_members(session: AsyncSession, group_id: int, limit: int = 10) -> List[GroupMember]:
        stmt = select(GroupMember).where(GroupMember.group_id == group_id).order_by(desc(GroupMember.xp)).limit(limit)
        result = await session.execute(stmt)
        return list(result.scalars().all())

    @staticmethod
    async def record_member_game(session: AsyncSession, group_id: int, user_id: int, won: bool, xp_gained: int) -> None:
        stmt = select(GroupMember).where(GroupMember.group_id == group_id, GroupMember.user_id == user_id)
        res = await session.execute(stmt)
        member = res.scalar_one_or_none()
        if not member:
            member = GroupMember(
                group_id=group_id,
                user_id=user_id,
                xp=xp_gained,
                games_played=1,
                wins=1 if won else 0
            )
            session.add(member)
        else:
            member.xp += xp_gained
            member.games_played += 1
            if won:
                member.wins += 1
        await session.flush()

class GameRepository:
    @staticmethod
    async def create_game_record(session: AsyncSession, game_id: str, group_id: int, total_players: int) -> Game:
        game = Game(
            id=game_id,
            group_id=group_id,
            status="IN_PROGRESS",
            total_players=total_players,
            started_at=datetime.utcnow()
        )
        session.add(game)
        await session.flush()
        return game

    @staticmethod
    async def complete_game_record(
        session: AsyncSession, 
        game_id: str, 
        winner: str, 
        rounds: int, 
        mvp_user_id: Optional[int]
    ) -> None:
        game = await session.get(Game, game_id)
        if game:
            game.status = "COMPLETED"
            game.winner = winner
            game.rounds_count = rounds
            game.mvp_user_id = mvp_user_id
            game.ended_at = datetime.utcnow()
            await session.flush()

    @staticmethod
    async def save_game_player(
        session: AsyncSession,
        game_id: str,
        user_id: int,
        role: str,
        is_alive: bool = True,
        death_round: Optional[int] = None,
        death_reason: Optional[str] = None,
        kills: int = 0,
        saves: int = 0,
        investigations: int = 0,
        xp_earned: int = 0
    ) -> None:
        gp = GamePlayer(
            game_id=game_id,
            user_id=user_id,
            role=role,
            is_alive=is_alive,
            death_round=death_round,
            death_reason=death_reason,
            kills=kills,
            saves=saves,
            investigations=investigations,
            xp_earned=xp_earned
        )
        session.add(gp)
        await session.flush()

    @staticmethod
    async def save_game_action(
        session: AsyncSession,
        game_id: str,
        round_number: int,
        actor_id: int,
        action_type: str,
        target_id: Optional[int],
        is_successful: bool = True
    ) -> None:
        action = GameAction(
            game_id=game_id,
            round_number=round_number,
            actor_id=actor_id,
            action_type=action_type,
            target_id=target_id,
            is_successful=is_successful
        )
        session.add(action)
        await session.flush()

    @staticmethod
    async def save_game_vote(
        session: AsyncSession,
        game_id: str,
        round_number: int,
        attempt: int,
        voter_id: int,
        target_id: int
    ) -> None:
        vote = GameVote(
            game_id=game_id,
            round_number=round_number,
            attempt=attempt,
            voter_id=voter_id,
            target_id=target_id
        )
        session.add(vote)
        await session.flush()

    @staticmethod
    async def record_game_event(
        session: AsyncSession,
        game_id: str,
        event_type: str,
        payload: Optional[str] = None
    ) -> None:
        event = GameEvent(
            game_id=game_id,
            event_type=event_type,
            payload=payload
        )
        session.add(event)
        await session.flush()

