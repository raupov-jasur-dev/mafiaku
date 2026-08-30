from enum import Enum

class GamePhase(str, Enum):
    LOBBY = "LOBBY"
    GAME_START = "GAME_START"
    ROLE_ASSIGNMENT = "ROLE_ASSIGNMENT"
    NIGHT = "NIGHT"
    NIGHT_RESOLUTION = "NIGHT_RESOLUTION"
    MORNING = "MORNING"
    DISCUSSION = "DISCUSSION"
    VOTING = "VOTING"
    VOTE_RESOLUTION = "VOTE_RESOLUTION"
    WIN_CHECK = "WIN_CHECK"
    GAME_OVER = "GAME_OVER"

class Role(str, Enum):
    MAFIA = "MAFIA"
    CITIZEN = "CITIZEN"
    DOCTOR = "DOCTOR"
    COMMISSAR = "COMMISSAR"

class Team(str, Enum):
    MAFIA = "MAFIA"
    CITIZENS = "CITIZENS"

class WinnerTeam(str, Enum):
    MAFIA = "MAFIA"
    CITIZENS = "CITIZENS"
    DRAW = "DRAW"
