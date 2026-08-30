import time
from datetime import datetime
from typing import Optional, List
from sqlalchemy import (
    Column, Integer, BigInteger, String, Boolean, Float, DateTime, 
    ForeignKey, Text, Index, UniqueConstraint
)
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()

class User(Base):
    __tablename__ = "users"

    id = Column(BigInteger, primary_key=True, index=True) # Telegram user ID
    username = Column(String(64), nullable=True, index=True)
    first_name = Column(String(128), nullable=False, default="")
    last_name = Column(String(128), nullable=True)
    language_code = Column(String(16), default="uz", nullable=False)
    is_bot = Column(Boolean, default=False)
    is_banned = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    stats = relationship("UserStatistics", back_populates="user", uselist=False, cascade="all, delete-orphan")
    settings = relationship("UserSettings", back_populates="user", uselist=False, cascade="all, delete-orphan")
    ranks = relationship("UserRank", back_populates="user", uselist=False, cascade="all, delete-orphan")
    achievements = relationship("UserAchievement", back_populates="user", cascade="all, delete-orphan")

class Group(Base):
    __tablename__ = "groups"

    id = Column(BigInteger, primary_key=True, index=True) # Telegram chat ID (usually negative)
    title = Column(String(255), nullable=False)
    username = Column(String(64), nullable=True)
    is_active = Column(Boolean, default=True)
    is_banned = Column(Boolean, default=False)
    bot_is_admin = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    settings = relationship("GroupSettings", back_populates="group", uselist=False, cascade="all, delete-orphan")
    stats = relationship("GroupStatistics", back_populates="group", uselist=False, cascade="all, delete-orphan")
    members = relationship("GroupMember", back_populates="group", cascade="all, delete-orphan")
    games = relationship("Game", back_populates="group")

class GroupMember(Base):
    __tablename__ = "group_members"

    id = Column(Integer, primary_key=True, autoincrement=True)
    group_id = Column(BigInteger, ForeignKey("groups.id", ondelete="CASCADE"), index=True)
    user_id = Column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"), index=True)
    xp = Column(Integer, default=0)
    games_played = Column(Integer, default=0)
    wins = Column(Integer, default=0)
    joined_at = Column(DateTime, default=datetime.utcnow)

    group = relationship("Group", back_populates="members")
    user = relationship("User")

    __table_args__ = (UniqueConstraint("group_id", "user_id", name="uq_group_user"),)

class Game(Base):
    __tablename__ = "games"

    id = Column(String(64), primary_key=True, index=True) # UUID
    group_id = Column(BigInteger, ForeignKey("groups.id", ondelete="CASCADE"), index=True)
    status = Column(String(32), default="LOBBY", index=True) # LOBBY, IN_PROGRESS, COMPLETED, CANCELLED
    winner = Column(String(32), nullable=True) # CITIZENS, MAFIA, DRAW
    total_players = Column(Integer, default=0)
    rounds_count = Column(Integer, default=1)
    mvp_user_id = Column(BigInteger, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    started_at = Column(DateTime, default=datetime.utcnow)
    ended_at = Column(DateTime, nullable=True)

    group = relationship("Group", back_populates="games")
    players = relationship("GamePlayer", back_populates="game", cascade="all, delete-orphan")
    actions = relationship("GameAction", back_populates="game", cascade="all, delete-orphan")
    votes = relationship("GameVote", back_populates="game", cascade="all, delete-orphan")
    events = relationship("GameEvent", back_populates="game", cascade="all, delete-orphan")

class GamePlayer(Base):
    __tablename__ = "game_players"

    id = Column(Integer, primary_key=True, autoincrement=True)
    game_id = Column(String(64), ForeignKey("games.id", ondelete="CASCADE"), index=True)
    user_id = Column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"), index=True)
    role = Column(String(32), nullable=True) # MAFIA, CITIZEN, DOCTOR, COMMISSAR
    is_alive = Column(Boolean, default=True)
    death_round = Column(Integer, nullable=True)
    death_reason = Column(String(32), nullable=True) # NIGHT_KILL, VOTED_OUT, DISCONNECTED
    kills = Column(Integer, default=0)
    saves = Column(Integer, default=0)
    investigations = Column(Integer, default=0)
    xp_earned = Column(Integer, default=0)

    game = relationship("Game", back_populates="players")
    user = relationship("User")

    __table_args__ = (UniqueConstraint("game_id", "user_id", name="uq_game_player"),)

class GameAction(Base):
    __tablename__ = "game_actions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    game_id = Column(String(64), ForeignKey("games.id", ondelete="CASCADE"), index=True)
    round_number = Column(Integer, default=1)
    actor_id = Column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"))
    action_type = Column(String(32), nullable=False) # MAFIA_KILL, DOCTOR_SAVE, COMMISSAR_CHECK
    target_id = Column(BigInteger, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    is_successful = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    game = relationship("Game", back_populates="actions")

class GameVote(Base):
    __tablename__ = "game_votes"

    id = Column(Integer, primary_key=True, autoincrement=True)
    game_id = Column(String(64), ForeignKey("games.id", ondelete="CASCADE"), index=True)
    round_number = Column(Integer, default=1)
    attempt = Column(Integer, default=1) # 1 or 2 (for tie)
    voter_id = Column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"))
    target_id = Column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"))
    created_at = Column(DateTime, default=datetime.utcnow)

    game = relationship("Game", back_populates="votes")

class GameEvent(Base):
    __tablename__ = "game_events"

    id = Column(Integer, primary_key=True, autoincrement=True)
    game_id = Column(String(64), ForeignKey("games.id", ondelete="CASCADE"), index=True)
    event_type = Column(String(64), nullable=False)
    payload = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    game = relationship("Game", back_populates="events")

class UserStatistics(Base):
    __tablename__ = "user_statistics"

    user_id = Column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    games_played = Column(Integer, default=0)
    wins = Column(Integer, default=0)
    losses = Column(Integer, default=0)
    mafia_games = Column(Integer, default=0)
    doctor_games = Column(Integer, default=0)
    commissar_games = Column(Integer, default=0)
    citizen_games = Column(Integer, default=0)
    kills = Column(Integer, default=0)
    saves = Column(Integer, default=0)
    investigations = Column(Integer, default=0)
    mvp_count = Column(Integer, default=0)
    win_streak = Column(Integer, default=0)
    max_win_streak = Column(Integer, default=0)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="stats")

class GroupStatistics(Base):
    __tablename__ = "group_statistics"

    group_id = Column(BigInteger, ForeignKey("groups.id", ondelete="CASCADE"), primary_key=True)
    total_games = Column(Integer, default=0)
    citizens_wins = Column(Integer, default=0)
    mafia_wins = Column(Integer, default=0)
    total_players_joined = Column(Integer, default=0)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    group = relationship("Group", back_populates="stats")

class UserRank(Base):
    __tablename__ = "user_ranks"

    user_id = Column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    xp = Column(Integer, default=0, index=True)
    rank_name = Column(String(32), default="Newbie")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="ranks")

class Achievement(Base):
    __tablename__ = "achievements"

    id = Column(String(64), primary_key=True) # e.g. 'first_game'
    name = Column(String(128), nullable=False)
    icon = Column(String(16), default="🏆")
    description = Column(String(255), nullable=False)
    xp_reward = Column(Integer, default=50)

class UserAchievement(Base):
    __tablename__ = "user_achievements"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"), index=True)
    achievement_id = Column(String(64), ForeignKey("achievements.id", ondelete="CASCADE"), index=True)
    unlocked_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="achievements")
    achievement = relationship("Achievement")

    __table_args__ = (UniqueConstraint("user_id", "achievement_id", name="uq_user_achievement"),)

class UserSettings(Base):
    __tablename__ = "user_settings"

    user_id = Column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    language = Column(String(16), default="uz")
    notifications_enabled = Column(Boolean, default=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="settings")

class GroupSettings(Base):
    __tablename__ = "group_settings"

    group_id = Column(BigInteger, ForeignKey("groups.id", ondelete="CASCADE"), primary_key=True)
    language = Column(String(16), default="uz")
    lobby_duration = Column(Integer, default=180)
    discussion_duration = Column(Integer, default=120)
    voting_duration = Column(Integer, default=45)
    night_duration = Column(Integer, default=45)
    min_players = Column(Integer, default=4)
    max_players = Column(Integer, default=20)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    group = relationship("Group", back_populates="settings")

class AdminUser(Base):
    __tablename__ = "admin_users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"), unique=True)
    role = Column(String(32), default="ADMIN") # SUPERADMIN, ADMIN, MODERATOR
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    admin_id = Column(BigInteger, nullable=True)
    action = Column(String(64), nullable=False)
    target_type = Column(String(32), nullable=True)
    target_id = Column(String(64), nullable=True)
    details = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
