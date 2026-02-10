"""
Triage flow keyboards.
"""

from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from app.config.texts import Texts


def get_triage_keyboard() -> InlineKeyboardMarkup:
    """
    Build triage keyboard for users without invite code.
    
    Buttons:
        - Enter code
        - No code
    """
    builder = InlineKeyboardBuilder()
    
    builder.button(text=Texts.BTN_ENTER_CODE, callback_data="triage:enter_code")
    builder.button(text=Texts.BTN_NO_CODE, callback_data="triage:no_code")
    
    builder.adjust(1)
    return builder.as_markup()


def get_skip_contact_keyboard() -> InlineKeyboardMarkup:
    """
    Build skip button for optional contact input.
    """
    builder = InlineKeyboardBuilder()
    
    builder.button(text=Texts.BTN_SKIP, callback_data="triage:skip_contact")
    
    return builder.as_markup()
