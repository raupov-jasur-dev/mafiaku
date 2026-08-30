# 🤵🏻 Mafia Ku (@mafiaku_gobot)

> **Multiplayer Mafia Telegram Bot** built with Python 3.12, aiogram 3.x, PostgreSQL, Redis, and a 26-language localization engine.

- **Telegram Bot**: [@mafiaku_gobot](https://t.me/mafiaku_gobot)  
- **Official Group**: [https://t.me/mafiaku_uz](https://t.me/mafiaku_uz)

---

## 1. Project Overview

Mafia Ku is a production-ready, Telegram-first multiplayer social deduction game engine. Games take place in Telegram groups while all confidential roles, night actions (Mafia kills, Doctor saves, Commissar investigations), and daytime voting ballots take place privately in the user's 1-on-1 chat with the bot.

---

## 2. Features

- **Dynamic Player Support**: 4 to 20 players per match with balanced role assignment. The match auto-starts when the minimum is reached, after a short configurable grace period (`AUTO_START_DELAY`) so additional players can still join.
- **Private Deep-Link Join Flow**: Players join via `t.me/mafiaku_gobot?start=join_<group_id>` to ensure direct PM communication channel before game starts.
- **Private Voting Engine**: Daytime ballots are cast in private PMs (`🗳 Kimni shahardan chiqaramiz?`), completely preventing public group peer pressure or role leakage.
- **Configurable Timers**: Lobby, night, discussion and voting durations are snapshotted into each game and survive restart recovery.
- **26 Natural Languages Localization**: Instant multi-language support covering Central Asia, Europe, East Asia, and more.
- **XP, Ranks & Achievements**: Comprehensive player statistics, MVP recognition, group-specific leaderboards, and achievements.
- **Fault-Tolerant State Recovery**: Redis-backed state machine and owner-safe distributed locks restore active games without resetting their current phase.
- **Admin Center & Health Probes**: FastAPI `/health` endpoint for Railway health checks and secure `/api/stats` dashboard.

---

## 3. Architecture

The application runs a clean, resilient single-process architecture managed by Python's `asyncio` event loop. The Railway Docker image also builds and serves the admin dashboard from FastAPI under `/` while preserving `/api/*` and `/health` routes:
- **Telegram Bot Worker**: Powered by `aiogram 3.x` with long-polling.
- **Web & Health Server**: Powered by `FastAPI` + `uvicorn` listening on `0.0.0.0:$PORT`; `/health` is public for Railway probes and the built admin dashboard is served from `/`.
- **Data Layer**: Async PostgreSQL / SQLite via SQLAlchemy 2.0.
- **Distributed Cache & State**: Redis for distributed locks, rate-limiting, and active match recovery.

---

## 4. Local Setup

### Prerequisites
- Python 3.11+ / 3.12
- Redis server
- PostgreSQL (or local SQLite for development)

```bash
# 1. Clone & create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure environment
cp .env.example .env

# 4. Start the application
python main.py
```

---

## 5. Environment Variables

| Variable | Required | Description | Example |
| :--- | :---: | :--- | :--- |
| `BOT_TOKEN` | **Yes** | Telegram Bot API Token from @BotFather | `1234567890:ABCdef...` |
| `DATABASE_URL` | **Yes** | PostgreSQL or SQLite async connection URL | `postgresql+asyncpg://user:pass@host:5432/db` |
| `REDIS_URL` | **Yes** | Redis connection URL | `redis://localhost:6379/0` |
| `ADMIN_IDS` | **Yes** | Comma-separated Telegram User IDs for bot admins | `123456789,987654321` |
| `ADMIN_API_KEY` | **Yes in production** | Secret key for Admin API `/api/*` endpoints | `your-secure-admin-api-key` |
| `SECRET_KEY` | **Yes in production** | Cryptographic secret | `generate-a-long-random-secret` |
| `WEBAPP_URL` | Optional | Web dashboard URL for CORS | `https://your-domain.up.railway.app` |
| `PORT` | Optional | HTTP web server port (default: 3000) | `3000` |

---

## 6. PostgreSQL Setup

The bot uses SQLAlchemy 2.0 Async. Existing tables are created safely at startup; no destructive schema changes are performed automatically.
- Production URL format: `postgresql+asyncpg://user:password@host:port/dbname`
- Automatic tables created: `users`, `groups`, `group_members`, `games`, `game_players`, `game_actions`, `game_votes`, `game_events`, `user_statistics`, `group_statistics`, `user_ranks`, `achievements`, `user_achievements`, `user_settings`, `group_settings`.

---

## 7. Redis Setup

Redis manages:
- **Concurrency Locks**: `create_game:<group_id>`, `join:<group_id>`, `vote:<group_id>`.
- **Match Recovery**: `active_game:<group_id>` serialization.
- **Rate-Limiting**: User command throttling.

---

## 8. Telegram Bot Setup

1. Open [@BotFather](https://t.me/BotFather) on Telegram.
2. Create a new bot with `/newbot`.
3. Set bot name: `🤵🏻 Mafia Ku`.
4. Set bot username: `@mafiaku_gobot`.
5. Enable group privacy settings if desired, or allow inline queries with `/setinline`.
6. Copy the API Token to `BOT_TOKEN`.

---

## 9. Required Telegram Group Permissions

For optimal gameplay, the bot requires Administrator status in your group with permissions:
- **Delete messages** (to clear expired lobby / action notices)
- **Pin messages** (to pin game status and daytime announcements)
- **Invite users via link**

When the bot is added to a group and promoted to admin, it will automatically send `/start@mafiaku_gobot` followed by the localized game prompt.

---

## 10. Admin Setup

Bot administrators specified in `ADMIN_IDS`:
- Can manage stuck games with `/resetgame` in groups.
- Can access the web API endpoints with header `X-Admin-Key: <ADMIN_API_KEY>`.

---

## 11. Automated Test Suite

Run all automated unit and integration tests:
```bash
pytest -q
```
Included test coverage:
- 4-player, 6-player, 12-player, 20-player role balancing.
- Doctor saves, Doctor misses, Commissar checks.
- Tie vote re-run, second tie cancellation.
- Mafia victory, Citizen victory conditions.
- Concurrency locks & simultaneous joins.
- Server restart recovery & state serialization.
- 26-language localization parity.

---

## 12. Railway Deployment Guide

Follow these exact steps to deploy to Railway:

- **STEP 1: Create Railway Project**: Go to [Railway.app](https://railway.app) and click **New Project**.
- **STEP 2: Add PostgreSQL**: Click **New** → **Database** → **Add PostgreSQL**.
- **STEP 3: Add Redis**: Click **New** → **Database** → **Add Redis**.
- **STEP 4: Configure Application Service**: Click **New** → **GitHub Repo** and select this repository.
- **STEP 5: Add Environment Variables**: Under the service **Variables** tab, set:
  - `BOT_TOKEN`: `<your-telegram-bot-token>`
  - `DATABASE_URL`: `${{Postgres.DATABASE_URL}}` (Use asyncpg: if Railway sets `postgresql://`, it will auto-convert to `postgresql+asyncpg://`)
  - `REDIS_URL`: `${{Redis.REDIS_URL}}`
  - `ADMIN_IDS`: `123456789`
  - `ADMIN_API_KEY`: `<generate-a-long-random-key>`
  - `SECRET_KEY`: `<generate-a-long-random-secret>`
  - `WEBAPP_URL`: `https://<your-railway-domain>`
  - `AUTO_START_DELAY`: `5`
  - `ENVIRONMENT`: `production`
  - `DEBUG`: `False`
  - `PORT`: Railway-provided value (do not hardcode in production)
- **STEP 6: Deploy**: Railway will build the Docker container using the included `railway.toml` and `Dockerfile`. The Docker build compiles the React admin dashboard and packages it into the FastAPI service.
- **STEP 7: Check Logs**: Verify the deployment log shows `✅ Uvicorn server running on http://0.0.0.0:3000` and `🚀 Mafia Ku Bot started successfully!`.
- **STEP 8: Check Health Endpoint**: Open `https://<your-railway-domain>/health` in your browser. It should return `{"status": "ok", "service": "mafiaku-backend"}`.
- **STEP 9: Open Telegram and Test `/start`**: Send `/start` to `@mafiaku_gobot` in a private chat. The rich welcome menu and language picker should appear.
- **STEP 10: Add Bot to a Test Group**:
  1. Add `@mafiaku_gobot` to your group.
  2. Promote the bot to Administrator.
  3. Notice the bot automatically sends `/start@mafiaku_gobot` and instructions.
  4. Type `/game` to open the lobby.
  5. Have players click `🎭 Mafiyaga qo'shilish`; each player must be a group member.
  6. When the minimum player count is reached, the game starts automatically after the configured grace delay.
  7. Verify role delivery, Night actions, Morning summary, Discussion, and Private Voting.

---

## 13. Troubleshooting

- **Bot not responding in group**: Ensure the bot is granted Administrator rights with Message Send and Delete rights.
- **Player not receiving role**: Players must start the bot in private chat at least once (handled automatically by deep-link join button).
- **Healthcheck failing on Railway**: Confirm Railway's `PORT` variable is set (default 3000) and `healthcheckPath = "/health"` matches `railway.toml`.
