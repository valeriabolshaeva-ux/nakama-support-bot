"""
Category selection keyboards.
"""

from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from app.config.categories import CATEGORIES


def get_categories_keyboard() -> InlineKeyboardMarkup:
    """
    Build category selection inline keyboard.
    
    Returns:
        InlineKeyboardMarkup with all categories as buttons
    """
    builder = InlineKeyboardBuilder()
    
    for cat in CATEGORIES:
        builder.button(
            text=f"{cat.emoji} {cat.label}",
            callback_data=f"category:{cat.id}"
        )
    
    builder.adjust(1)  # One button per row
    return builder.as_markup()


def get_urgency_keyboard() -> InlineKeyboardMarkup:
    """
    Build urgency level selection keyboard.
    
    For "Urgent" category additional question.
    """
    builder = InlineKeyboardBuilder()
    
    builder.button(text="🔴 Полностью блокирует", callback_data="urgency:full_block")
    builder.button(text="🟡 Частично мешает", callback_data="urgency:partial")
    builder.button(text="🟢 Не блокирует, но важно", callback_data="urgency:not_blocking")
    
    builder.adjust(1)
    return builder.as_markup()
