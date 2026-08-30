from aiogram import Router, F
from aiogram.types import CallbackQuery
from app.localization.manager import i18n
from app.localization.languages import SUPPORTED_LANGUAGES
from app.database.session import AsyncSessionLocal
from app.database.repositories import UserRepository
from app.bot.keyboards.inline import (
    get_settings_keyboard, get_languages_keyboard, 
    get_start_keyboard, get_back_to_start_keyboard
)

router = Router()

@router.callback_query(F.data == "menu:settings")
async def show_settings(callback: CallbackQuery, user_lang: str = "uz"):
    text = i18n.get("settings_title", user_lang)
    keyboard = get_settings_keyboard(user_lang)
    if callback.message:
        await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="Markdown")
    await callback.answer()

@router.callback_query(F.data == "settings:lang")
async def show_language_picker(callback: CallbackQuery, user_lang: str = "uz"):
    text = i18n.get("choose_language", user_lang)
    keyboard = get_languages_keyboard()
    if callback.message:
        await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="Markdown")
    await callback.answer()

@router.callback_query(F.data.startswith("set_lang:"))
async def handle_set_language(callback: CallbackQuery):
    lang_code = callback.data.split(":")[1]
    if lang_code in SUPPORTED_LANGUAGES:
        async with AsyncSessionLocal() as session:
            await UserRepository.update_language(session, callback.from_user.id, lang_code)
            await session.commit()

        lang_name = SUPPORTED_LANGUAGES[lang_code]["name"]
        text = i18n.get("language_changed", lang_code, lang=lang_name)
        keyboard = get_settings_keyboard(lang_code)
        if callback.message:
            await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="Markdown")
        await callback.answer(f"Language set to {lang_name}!", show_alert=False)
    else:
        await callback.answer("Invalid language selection", show_alert=True)

@router.callback_query(F.data == "settings:about")
async def show_about_bot(callback: CallbackQuery, user_lang: str = "uz"):
    text = i18n.get("about_bot_info", user_lang)
    keyboard = get_back_to_start_keyboard(user_lang)
    if callback.message:
        await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="Markdown")
    await callback.answer()

@router.callback_query(F.data == "settings:notify")
async def toggle_notifications(callback: CallbackQuery, user_lang: str = "uz"):
    async with AsyncSessionLocal() as session:
        is_enabled = await UserRepository.toggle_notifications(session, callback.from_user.id)
        await session.commit()
    status_str = "ON (Faol)" if is_enabled else "OFF (O'chirilgan)"
    text = i18n.get("notifications_toggled", user_lang, status=status_str)
    await callback.answer(text, show_alert=True)

@router.callback_query(F.data == "menu:back_start")
async def back_to_main_menu(callback: CallbackQuery, user_lang: str = "uz"):
    text = i18n.get("welcome_title", user_lang)
    keyboard = get_start_keyboard(user_lang)
    if callback.message:
        await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="Markdown")
    await callback.answer()
