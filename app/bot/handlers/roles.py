from aiogram import Router, F
from aiogram.types import CallbackQuery
from app.localization.manager import i18n
from app.bot.keyboards.inline import get_back_to_start_keyboard

router = Router()

@router.callback_query(F.data == "menu:roles")
async def show_roles_info(callback: CallbackQuery, user_lang: str = "uz"):
    text = i18n.get("about_roles_text", user_lang)
    keyboard = get_back_to_start_keyboard(user_lang)
    if callback.message:
        await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="Markdown")
    await callback.answer()
