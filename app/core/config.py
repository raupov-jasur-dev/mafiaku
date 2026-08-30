import os
from typing import List
from dataclasses import dataclass, field
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

@dataclass
class Settings:
    BOT_TOKEN: str = os.getenv("BOT_TOKEN", "")
    BOT_USERNAME: str = os.getenv("BOT_USERNAME", "mafiaku_gobot")
    OFFICIAL_GROUP: str = os.getenv("OFFICIAL_GROUP", "https://t.me/mafiaku_uz")
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///mafiaku.db")
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    ADMIN_IDS_RAW: str = os.getenv("ADMIN_IDS", "")
    ADMIN_API_KEY: str = os.getenv("ADMIN_API_KEY", "")
    SECRET_KEY: str = os.getenv("SECRET_KEY", "")
    WEBAPP_URL: str = os.getenv("WEBAPP_URL", "")
    PORT: int = int(os.getenv("PORT", "3000"))
    HOST: str = os.getenv("HOST", "0.0.0.0")
    DEBUG: bool = os.getenv("DEBUG", "False").lower() in ("true", "1", "yes")
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", os.getenv("ENV", "development")).lower()

    LOBBY_DURATION: int = int(os.getenv("LOBBY_DURATION", "180"))
    DISCUSSION_DURATION: int = int(os.getenv("DISCUSSION_DURATION", "120"))
    VOTING_DURATION: int = int(os.getenv("VOTING_DURATION", "45"))
    NIGHT_DURATION: int = int(os.getenv("NIGHT_DURATION", "45"))
    MIN_PLAYERS: int = int(os.getenv("MIN_PLAYERS", "4"))
    MAX_PLAYERS: int = int(os.getenv("MAX_PLAYERS", "20"))
    AUTO_START_DELAY: int = int(os.getenv("AUTO_START_DELAY", "5"))


    def validate_for_production(self) -> None:
        """Fail fast when required production configuration is missing or unsafe."""
        if self.ENVIRONMENT != "production":
            return
        required = {
            "BOT_TOKEN": self.BOT_TOKEN,
            "DATABASE_URL": self.DATABASE_URL,
            "REDIS_URL": self.REDIS_URL,
            "ADMIN_IDS": self.ADMIN_IDS_RAW,
            "ADMIN_API_KEY": self.ADMIN_API_KEY,
            "SECRET_KEY": self.SECRET_KEY,
        }
        missing = [key for key, value in required.items() if not str(value).strip()]
        if missing:
            raise RuntimeError(
                "Missing required production environment variables: " + ", ".join(missing)
            )
        if not (self.DATABASE_URL.startswith("postgresql") or self.DATABASE_URL.startswith("postgres")):
            raise RuntimeError("Production DATABASE_URL must use PostgreSQL.")
        if self.DEBUG:
            raise RuntimeError("DEBUG must be false in production.")
        if self.MIN_PLAYERS < 4 or self.MAX_PLAYERS < self.MIN_PLAYERS or self.MAX_PLAYERS > 20:
            raise RuntimeError("MIN_PLAYERS/MAX_PLAYERS must satisfy 4 <= MIN_PLAYERS <= MAX_PLAYERS <= 20")
        if min(self.LOBBY_DURATION, self.DISCUSSION_DURATION, self.VOTING_DURATION, self.NIGHT_DURATION) < 1:
            raise RuntimeError("All game phase durations must be positive.")

    @property
    def admin_ids(self) -> List[int]:
        ids = []
        for part in self.ADMIN_IDS_RAW.split(","):
            part = part.strip()
            if part.isdigit():
                ids.append(int(part))
        return ids

settings = Settings()
