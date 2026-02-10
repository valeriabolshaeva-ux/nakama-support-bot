"""
Operator action keyboards.
"""

from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from app.config.texts import Texts


def get_ticket_actions_keyboard(ticket_id: int) -> InlineKeyboardMarkup:
    """
    Build operator action buttons for new ticket.
    
    Args:
        ticket_id: Ticket ID for callback data
    """
    builder = InlineKeyboardBuilder()
    
    builder.button(text=Texts.BTN_TAKE, callback_data=f"op:take:{ticket_id}")
    builder.button(text=Texts.BTN_DETAILS, callback_data=f"op:details:{ticket_id}")
    
    builder.adjust(2)
    return builder.as_markup()


def get_ticket_inprogress_keyboard(ticket_id: int) -> InlineKeyboardMarkup:
    """
    Build action buttons for ticket in progress.
    
    Args:
        ticket_id: Ticket ID for callback data
    """
    builder = InlineKeyboardBuilder()
    
    builder.button(text=Texts.BTN_PAUSE, callback_data=f"op:pause:{ticket_id}")
    builder.button(text=Texts.BTN_DETAILS, callback_data=f"op:details:{ticket_id}")
    builder.button(text=Texts.BTN_CLOSE_SUCCESS, callback_data=f"op:close:{ticket_id}")
    builder.button(text=Texts.BTN_CANCEL_TICKET, callback_data=f"op:cancel:{ticket_id}")
    
    builder.adjust(2, 2)
    return builder.as_markup()


def get_ticket_paused_keyboard(ticket_id: int) -> InlineKeyboardMarkup:
    """
    Build action buttons for paused ticket.
    
    Args:
        ticket_id: Ticket ID for callback data
    """
    builder = InlineKeyboardBuilder()
    
    builder.button(text=Texts.BTN_RESUME, callback_data=f"op:resume:{ticket_id}")
    builder.button(text=Texts.BTN_DETAILS, callback_data=f"op:details:{ticket_id}")
    builder.button(text=Texts.BTN_CLOSE_SUCCESS, callback_data=f"op:close:{ticket_id}")
    builder.button(text=Texts.BTN_CANCEL_TICKET, callback_data=f"op:cancel:{ticket_id}")
    
    builder.adjust(2, 2)
    return builder.as_markup()
