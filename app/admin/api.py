import os
from typing import Optional

from fastapi import FastAPI, Depends, HTTPException, Header, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from sqlalchemy import select, func, desc

from app.core.config import settings
from app.database.session import AsyncSessionLocal
from app.database.models import User, Group, Game, UserStatistics, UserRank, GroupSettings
from app.bot.handlers.game_orchestrator import active_games, GameOrchestrator
from app.localization.languages import SUPPORTED_LANGUAGES
from app.services.recovery_service import recovery_service

app = FastAPI(title="Mafia Ku Admin API", version="2.0.0")

origins = ["http://localhost:3000", "http://localhost:5173"]
if settings.WEBAPP_URL:
    origins.insert(0, settings.WEBAPP_URL.rstrip("/"))
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

_bot = None


def set_bot(bot) -> None:
    global _bot
    _bot = bot


async def verify_admin_key(x_admin_key: Optional[str] = Header(None)):
    admin_secret = settings.ADMIN_API_KEY
    if not admin_secret:
        raise HTTPException(status_code=500, detail="ADMIN_API_KEY is not configured")
    if x_admin_key != admin_secret:
        raise HTTPException(status_code=401, detail="Unauthorized admin access")
    return True


class GroupSettingsUpdate(BaseModel):
    language: Optional[str] = None
    lobby_duration: Optional[int] = Field(default=None, ge=5, le=3600)
    discussion_duration: Optional[int] = Field(default=None, ge=5, le=3600)
    voting_duration: Optional[int] = Field(default=None, ge=5, le=3600)
    night_duration: Optional[int] = Field(default=None, ge=5, le=3600)
    min_players: Optional[int] = Field(default=None, ge=4, le=20)
    max_players: Optional[int] = Field(default=None, ge=4, le=20)


class BroadcastRequest(BaseModel):
    text: str = Field(min_length=1, max_length=4096)


@app.get("/health")
async def health_check():
    return {"status": "ok", "service": "mafiaku-backend", "active_games": len(active_games)}


@app.get("/api/stats")
async def get_dashboard_stats(authorized: bool = Depends(verify_admin_key)):
    async with AsyncSessionLocal() as session:
        user_count = await session.scalar(select(func.count(User.id))) or 0
        group_count = await session.scalar(select(func.count(Group.id))) or 0
        game_count = await session.scalar(select(func.count(Game.id))) or 0
        cit_wins = await session.scalar(select(func.count(Game.id)).where(Game.winner == "CITIZENS")) or 0
        maf_wins = await session.scalar(select(func.count(Game.id)).where(Game.winner == "MAFIA")) or 0
    return {
        "total_users": user_count,
        "total_groups": group_count,
        "total_games": game_count,
        "active_games": len(active_games),
        "citizens_wins": cit_wins,
        "mafia_wins": maf_wins,
    }


@app.get("/api/users")
async def list_users(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    authorized: bool = Depends(verify_admin_key),
):
    async with AsyncSessionLocal() as session:
        stmt = (
            select(User, UserStatistics, UserRank)
            .outerjoin(UserStatistics, User.id == UserStatistics.user_id)
            .outerjoin(UserRank, User.id == UserRank.user_id)
            .order_by(desc(User.created_at)).limit(limit).offset(offset)
        )
        rows = (await session.execute(stmt)).all()
    return [
        {
            "id": user.id, "first_name": user.first_name, "last_name": user.last_name,
            "username": user.username, "language": user.language_code,
            "is_banned": user.is_banned,
            "created_at": user.created_at.isoformat() if user.created_at else None,
            "games_played": stats.games_played if stats else 0,
            "wins": stats.wins if stats else 0,
            "xp": rank.xp if rank else 0,
            "rank": rank.rank_name if rank else "Newbie",
        }
        for user, stats, rank in rows
    ]


@app.post("/api/users/{user_id}/ban")
async def ban_user(user_id: int, authorized: bool = Depends(verify_admin_key)):
    async with AsyncSessionLocal() as session:
        user = await session.get(User, user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        user.is_banned = True
        await session.commit()
    return {"ok": True, "user_id": user_id, "is_banned": True}


@app.post("/api/users/{user_id}/unban")
async def unban_user(user_id: int, authorized: bool = Depends(verify_admin_key)):
    async with AsyncSessionLocal() as session:
        user = await session.get(User, user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        user.is_banned = False
        await session.commit()
    return {"ok": True, "user_id": user_id, "is_banned": False}


@app.get("/api/groups")
async def list_groups(limit: int = Query(50, ge=1, le=200), authorized: bool = Depends(verify_admin_key)):
    async with AsyncSessionLocal() as session:
        stmt = select(Group).order_by(desc(Group.created_at)).limit(limit)
        groups = (await session.execute(stmt)).scalars().all()
    return [
        {
            "id": g.id, "title": g.title, "username": g.username,
            "is_active": g.is_active, "is_banned": g.is_banned,
            "bot_is_admin": g.bot_is_admin,
            "created_at": g.created_at.isoformat() if g.created_at else None,
        }
        for g in groups
    ]


@app.put("/api/groups/{group_id}/settings")
async def update_group_settings(group_id: int, payload: GroupSettingsUpdate, authorized: bool = Depends(verify_admin_key)):
    if payload.min_players and payload.max_players and payload.max_players < payload.min_players:
        raise HTTPException(status_code=400, detail="max_players must be >= min_players")
    async with AsyncSessionLocal() as session:
        group = await session.get(Group, group_id)
        if not group:
            raise HTTPException(status_code=404, detail="Group not found")
        gs = await session.get(GroupSettings, group_id)
        if not gs:
            gs = GroupSettings(group_id=group_id)
            session.add(gs)
        for field in ("language", "lobby_duration", "discussion_duration", "voting_duration", "night_duration", "min_players", "max_players"):
            value = getattr(payload, field)
            if value is not None:
                setattr(gs, field, value)
        if gs.max_players < gs.min_players:
            raise HTTPException(status_code=400, detail="max_players must be >= min_players")
        await session.commit()
    return {"ok": True, "group_id": group_id}


@app.post("/api/groups/{group_id}/ban")
async def ban_group(group_id: int, authorized: bool = Depends(verify_admin_key)):
    async with AsyncSessionLocal() as session:
        group = await session.get(Group, group_id)
        if not group:
            raise HTTPException(status_code=404, detail="Group not found")
        group.is_banned = True
        await session.commit()
    return {"ok": True, "group_id": group_id, "is_banned": True}


@app.post("/api/groups/{group_id}/unban")
async def unban_group(group_id: int, authorized: bool = Depends(verify_admin_key)):
    async with AsyncSessionLocal() as session:
        group = await session.get(Group, group_id)
        if not group:
            raise HTTPException(status_code=404, detail="Group not found")
        group.is_banned = False
        await session.commit()
    return {"ok": True, "group_id": group_id, "is_banned": False}


@app.get("/api/active-games")
async def list_active_games(authorized: bool = Depends(verify_admin_key)):
    return [
        {
            "game_id": state.game_id,
            "group_id": state.group_id,
            "group_title": state.group_title,
            "phase": state.phase.value,
            "players_count": len(state.players),
            "alive_count": len(state.alive_players),
            "round_number": state.round_number,
            "deadline": state.phase_deadline,
            "players": [
                {
                    "user_id": p.user_id,
                    "name": p.display_name,
                    "role": (p.role.value if not p.is_alive else "HIDDEN") if p.role else None,
                    "is_alive": p.is_alive,
                }
                for p in state.players.values()
            ],
        }
        for state in active_games.values()
    ]


@app.post("/api/active-games/{group_id}/reset")
async def reset_active_game(group_id: int, authorized: bool = Depends(verify_admin_key)):
    GameOrchestrator.remove_game(group_id)
    await recovery_service.clear_active_game(group_id)
    return {"ok": True, "group_id": group_id}


@app.post("/api/broadcast")
async def broadcast(payload: BroadcastRequest, authorized: bool = Depends(verify_admin_key)):
    if _bot is None:
        raise HTTPException(status_code=503, detail="Telegram bot is not ready")
    async with AsyncSessionLocal() as session:
        user_ids = (await session.execute(select(User.id).where(User.is_banned.is_(False)))).scalars().all()
    sent = failed = 0
    for uid in user_ids:
        try:
            await _bot.send_message(chat_id=uid, text=payload.text)
            sent += 1
        except Exception:
            failed += 1
    return {"ok": True, "sent": sent, "failed": failed}


@app.get("/api/languages")
async def get_languages():
    return SUPPORTED_LANGUAGES


static_dir = "/app/web_dist"
if os.path.isdir(static_dir):
    app.mount("/", StaticFiles(directory=static_dir, html=True), name="admin-dashboard")
