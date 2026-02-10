"""
Ticket-related keyboards.
"""

from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from app.config.texts import Texts


def get_skip_attachments_keyboard() -> InlineKeyboardMarkup:
    """
    Build skip button for attachments step.
    Shows "Пропустить" initially when no attachments.
    """
    builder = InlineKeyboardBuilder()
    
    builder.button(text=Texts.BTN_SKIP, callback_data="ticket:skip_attachments")
    
    return builder.as_markup()


def get_preview_keyboard() -> InlineKeyboardMarkup:
    """
    Build preview button after receiving attachments.
    Shows "Превью и отправить" after each attachment.
    """
    builder = InlineKeyboardBuilder()
    
    builder.button(text=Texts.BTN_PREVIEW, callback_data="ticket:show_summary")
    
    return builder.as_markup()


def get_summary_keyboard() -> InlineKeyboardMarkup:
    """
    Build keyboard for ticket summary/preview screen.
    
    Buttons:
    - Edit category
    - Edit description
    - Edit attachments
    - Cancel
    - Submit
    """
    builder = InlineKeyboardBuilder()
    
    # Edit buttons in first row
    builder.button(text=Texts.BTN_EDIT_CATEGORY, callback_data="ticket:edit_category")
    builder.button(text=Texts.BTN_EDIT_DESCRIPTION, callback_data="ticket:edit_description")
    
    # Edit attachments in second row
    builder.button(text=Texts.BTN_EDIT_ATTACHMENTS, callback_data="ticket:edit_attachments")
    
    # Cancel and Submit in third row
    builder.button(text=Texts.BTN_CANCEL, callback_data="ticket:cancel")
    builder.button(text=Texts.BTN_SUBMIT, callback_data="ticket:submit")
    
    builder.adjust(2, 1, 2)
    return builder.as_markup()


def get_reopen_or_new_keyboard(ticket_number: int) -> InlineKeyboardMarkup:
    """
    Build keyboard for choosing between reopen and new ticket.
    
    Args:
        ticket_number: Number of the recently closed ticket
    """
    builder = InlineKeyboardBuilder()
    
    builder.button(
        text=Texts.reopen_button(ticket_number),
        callback_data=f"ticket:reopen:{ticket_number}"
    )
    builder.button(text=Texts.BTN_NEW_TICKET, callback_data="ticket:new")
    
    builder.adjust(1)
    return builder.as_markup()


# Keep old name for backward compatibility
def get_done_attachments_keyboard() -> InlineKeyboardMarkup:
    """Deprecated: use get_preview_keyboard() instead."""
    return get_preview_keyboard()


def get_after_ticket_menu() -> InlineKeyboardMarkup:
    """
    Build menu shown after ticket creation.
    
    Buttons:
    - My tickets (library)
    - New request
    """
    builder = InlineKeyboardBuilder()
    
    builder.button(text=Texts.BTN_MY_TICKETS, callback_data="menu:my_tickets")
    builder.button(text=Texts.BTN_NEW_REQUEST, callback_data="menu:new_request")
    
    builder.adjust(1)
    return builder.as_markup()


def get_active_ticket_menu() -> InlineKeyboardMarkup:
    """
    Build menu for active ticket message.
    
    Buttons:
    - My tickets (library)
    - New request
    """
    builder = InlineKeyboardBuilder()
    
    builder.button(text=Texts.BTN_MY_TICKETS, callback_data="menu:my_tickets")
    builder.button(text=Texts.BTN_NEW_REQUEST, callback_data="menu:new_request")
    
    builder.adjust(1)
    return builder.as_markup()
