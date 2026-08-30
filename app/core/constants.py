import os
from typing import List

BOT_NAME = "🤵🏻 Mafia Ku"
BOT_USERNAME = "mafiaku_gobot"
OFFICIAL_GROUP_URL = "https://t.me/mafiaku_uz"

# Game Default Settings
DEFAULT_LOBBY_DURATION = 180       # 3 minutes
DEFAULT_DISCUSSION_DURATION = 120  # 2 minutes
DEFAULT_VOTING_DURATION = 45       # 45 seconds
DEFAULT_NIGHT_DURATION = 45        # 45 seconds
LOBBY_UPDATE_INTERVAL = 20         # 20 seconds progress refresh
MIN_PLAYERS_COUNT = 4
MAX_PLAYERS_COUNT = 20

# Rank Thresholds (XP based)
RANKS = [
    ("Newbie", 0),
    ("Rookie", 100),
    ("Player", 300),
    ("Skilled", 700),
    ("Veteran", 1500),
    ("Master", 3000),
    ("Legend", 6000),
]

ACHIEVEMENT_DEFINITIONS = [
    {"id": "first_game", "name": "First Game", "icon": "🎮", "desc": "Play your first Mafia game"},
    {"id": "10_games", "name": "10 Games", "icon": "🔟", "desc": "Participate in 10 completed games"},
    {"id": "mafia_hunter", "name": "Mafia Hunter", "icon": "🎯", "desc": "Vote to eliminate 5 Mafia members"},
    {"id": "doctor_hero", "name": "Doctor Hero", "icon": "💉", "desc": "Successfully save 3 targets at night"},
    {"id": "detective", "name": "Detective", "icon": "🔍", "desc": "Discover 3 Mafia as Commissar"},
    {"id": "survivor", "name": "Survivor", "icon": "🛡️", "desc": "Win a game without dying"},
    {"id": "5_win_streak", "name": "5 Win Streak", "icon": "🔥", "desc": "Achieve 5 wins in a row"},
    {"id": "10_win_streak", "name": "10 Win Streak", "icon": "⚡", "desc": "Achieve 10 wins in a row"},
    {"id": "mvp", "name": "MVP", "icon": "⭐", "desc": "Earn Most Valuable Player recognition"},
    {"id": "mafia_master", "name": "Mafia Master", "icon": "👑", "desc": "Win 10 games playing as Mafia"},
]
