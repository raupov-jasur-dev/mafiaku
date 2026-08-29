from fastapi import FastAPI, Depends, HTTPException, Header, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from typing import Dict, Any, List, Optional
from sqlalchemy import select, func, desc
from app.core.config import settings
from app.database.session import AsyncSessionLocal
from app.database.models import User, Group, Game, GamePlayer, UserStatistics, UserRank
from app.bot.handlers.game_orchestrator import active_games
from app.localization.languages import SUPPORTED_LANGUAGES

app = FastAPI(title="Mafia Ku Admin API", version="1.0.0")

# Configure CORS securely
origins = ["http://localhost:3000", "http://localhost:5173"]
if settings.WEBAPP_URL:
    origins.insert(0, settings.WEBAPP_URL.rstrip("/"))
if settings.ENVIRONMENT == "production" and not settings.WEBAPP_URL:
    origins = []

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

async def verify_admin_key(x_admin_key: Optional[str] = Header(None)):
    """Admin security verification enforcing configured secret key."""
    admin_secret = settings.ADMIN_API_KEY
    if settings.ENVIRONMENT == "production" and not admin_secret:
        raise HTTPException(status_code=500, detail="Server misconfiguration: ADMIN_API_KEY required in production")
    
    if not admin_secret:
        raise HTTPException(status_code=500, detail="Server misconfiguration: ADMIN_API_KEY is not configured")
    if not x_admin_key or x_admin_key != admin_secret:
        raise HTTPException(status_code=401, detail="Unauthorized admin access")
    return True

@app.get("/health")
async def health_check():
    """Unauthenticated health endpoint for Railway / Cloud Run probes."""
    return {"status": "ok", "service": "mafiaku-backend"}

@app.get("/api/stats")
async def get_dashboard_stats(authorized: bool = Depends(verify_admin_key)):
    async with AsyncSessionLocal() as session:
        user_count = await session.scalar(select(func.count(User.id))) or 0
        group_count = await session.scalar(select(func.count(Group.id))) or 0
        game_count = await session.scalar(select(func.count(Game.id))) or 0
        
        # Win statistics
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
async def list_users(limit: int = 50, offset: int = 0, authorized: bool = Depends(verify_admin_key)):
    async with AsyncSessionLocal() as session:
        stmt = (
            select(User, UserStatistics, UserRank)
            .outerjoin(UserStatistics, User.id == UserStatistics.user_id)
            .outerjoin(UserRank, User.id == UserRank.user_id)
            .order_by(desc(User.created_at))
            .limit(limit)
            .offset(offset)
        )
        res = await session.execute(stmt)
        rows = res.all()

    users_list = []
    for user, stats, rank in rows:
        users_list.append({
            "id": user.id,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "username": user.username,
            "language": user.language_code,
            "is_banned": user.is_banned,
            "created_at": user.created_at.isoformat() if user.created_at else None,
            "games_played": stats.games_played if stats else 0,
            "wins": stats.wins if stats else 0,
            "xp": rank.xp if rank else 0,
            "rank": rank.rank_name if rank else "Newbie"
        })
    return users_list

@app.get("/api/groups")
async def list_groups(limit: int = 50, authorized: bool = Depends(verify_admin_key)):
    async with AsyncSessionLocal() as session:
        stmt = select(Group).order_by(desc(Group.created_at)).limit(limit)
        res = await session.execute(stmt)
        groups = res.scalars().all()

    return [
        {
            "id": g.id,
            "title": g.title,
            "username": g.username,
            "is_active": g.is_active,
            "bot_is_admin": g.bot_is_admin,
            "created_at": g.created_at.isoformat() if g.created_at else None
        }
        for g in groups
    ]

@app.get("/api/active-games")
async def list_active_games(authorized: bool = Depends(verify_admin_key)):
    """List active games while protecting role privacy during gameplay."""
    result = []
    for group_id, state in active_games.items():
        result.append({
            "game_id": state.game_id,
            "group_id": state.group_id,
            "group_title": state.group_title,
            "phase": state.phase.value,
            "players_count": len(state.players),
            "alive_count": len(state.alive_players),
            "round_number": state.round_number,
            "players": [
                {
                    "user_id": p.user_id,
                    "name": p.display_name,
                    # Conceal active role to prevent cheating / leakage
                    "role": (p.role.value if not p.is_alive else "HIDDEN") if p.role else None,
                    "is_alive": p.is_alive
                }
                for p in state.players.values()
            ]
        })
    return result

@app.get("/api/languages")
async def get_languages():
    return SUPPORTED_LANGUAGES


# Serve the built admin dashboard (if present) from the same FastAPI service.
# API routes are registered above, so /api/* remains protected and takes precedence.
static_dir = "/app/web_dist"
try:
    import os
    if os.path.isdir(static_dir):
        app.mount("/", StaticFiles(directory=static_dir, html=True), name="admin-dashboard")
except Exception:
    # Dashboard serving is optional; the Telegram bot and health endpoint remain available.
    pass
