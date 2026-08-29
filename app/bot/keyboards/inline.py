from typing import List, Optional
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from app.core.config import settings
from app.localization.manager import i18n
from app.localization.languages import SUPPORTED_LANGUAGES
from app.game.models import PlayerState

def get_start_keyboard(lang: str = "uz") -> InlineKeyboardMarkup:
    add_group_url = f"https://t.me/{settings.BOT_USERNAME}?startgroup=botstart"
    
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text=i18n.get("btn_add_group", lang), url=add_group_url),
                InlineKeyboardButton(text=i18n.get("btn_main_group", lang), url=settings.OFFICIAL_GROUP),
            ],
            [
                InlineKeyboardButton(text=i18n.get("btn_my_profile", lang), callback_data="menu:profile"),
                InlineKeyboardButton(text=i18n.get("btn_top_players", lang), callback_data="menu:top"),
            ],
            [
                InlineKeyboardButton(text=i18n.get("btn_settings", lang), callback_data="menu:settings"),
                InlineKeyboardButton(text=i18n.get("btn_about_roles", lang), callback_data="menu:roles"),
            ]
        ]
    )
    return keyboard

def get_lobby_keyboard(game_id: str, lang: str = "uz", group_id: Optional[int] = None) -> InlineKeyboardMarkup:
    """Lobby keyboard. Players always join through the bot private chat deep link.

    The game_id is retained for compatibility with persisted keyboards, while the
    actual join action uses Telegram's deep-link flow so private messaging is guaranteed.
    """
    buttons = []
    if group_id is not None:
        pm_join_url = f"https://t.me/{settings.BOT_USERNAME}?start=join_{group_id}"
        buttons.append([
            InlineKeyboardButton(
                text=i18n.get("btn_join_game", lang),
                url=pm_join_url
            )
        ])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_night_action_keyboard(game_id: str, alive_targets: List[PlayerState], exclude_user_id: Optional[int] = None) -> InlineKeyboardMarkup:
    buttons = []
    for player in alive_targets:
        if exclude_user_id and player.user_id == exclude_user_id:
            continue
        buttons.append([
            InlineKeyboardButton(
                text=f"🎯 {player.display_name}",
                callback_data=f"night:action:{game_id}:{player.user_id}"
            )
        ])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_voting_keyboard(game_id: str, alive_targets: List[PlayerState], voter_id: int) -> InlineKeyboardMarkup:
    buttons = []
    for player in alive_targets:
        if player.user_id == voter_id:
            continue  # cannot vote for self
        buttons.append([
            InlineKeyboardButton(
                text=f"🗳 {player.display_name}",
                callback_data=f"vote:cast:{game_id}:{player.user_id}"
            )
        ])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_languages_keyboard() -> InlineKeyboardMarkup:
    buttons = []
    row = []
    for code, info in SUPPORTED_LANGUAGES.items():
        row.append(InlineKeyboardButton(text=f"{info['flag']} {info['name']}", callback_data=f"set_lang:{code}"))
        if len(row) == 2:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)
    buttons.append([InlineKeyboardButton(text="⬅️ Orqaga", callback_data="menu:settings")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_settings_keyboard(lang: str = "uz") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=i18n.get("btn_language", lang), callback_data="settings:lang")],
            [InlineKeyboardButton(text=i18n.get("btn_notifications", lang), callback_data="settings:notify")],
            [InlineKeyboardButton(text=i18n.get("btn_about_bot", lang), callback_data="settings:about")],
            [InlineKeyboardButton(text=i18n.get("btn_back", lang), callback_data="menu:back_start")],
        ]
    )

def get_back_to_start_keyboard(lang: str = "uz") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=i18n.get("btn_back", lang), callback_data="menu:back_start")]
        ]
    )
