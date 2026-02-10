"""
CSAT feedback keyboards.
"""

from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder


def get_csat_keyboard(ticket_id: int) -> InlineKeyboardMarkup:
    """
    Build CSAT rating keyboard.
    
    Args:
        ticket_id: Ticket ID for callback data
    """
    builder = InlineKeyboardBuilder()
    
    builder.button(text="👍", callback_data=f"csat:positive:{ticket_id}")
    builder.button(text="👎", callback_data=f"csat:negative:{ticket_id}")
    
    builder.adjust(2)  # Both buttons in one row
    return builder.as_markup()


def get_detailed_csat_keyboard(ticket_id: int, dimension: str) -> InlineKeyboardMarkup:
    """
    Build detailed CSAT rating keyboard (1-5 stars).
    
    Args:
        ticket_id: Ticket ID for callback data
        dimension: speed, quality, or politeness
    """
    builder = InlineKeyboardBuilder()
    
    # 5 star buttons
    for i in range(1, 6):
        stars = "⭐" * i
        builder.button(text=stars, callback_data=f"csat_detail:{dimension}:{i}:{ticket_id}")
    
    builder.adjust(5)  # All in one row
    return builder.as_markup()


def get_skip_detailed_csat_keyboard(ticket_id: int) -> InlineKeyboardMarkup:
    """
    Build skip button for detailed CSAT.
    """
    builder = InlineKeyboardBuilder()
    builder.button(text="⏭️ Пропустить детальную оценку", callback_data=f"csat:skip_detailed:{ticket_id}")
    return builder.as_markup()
