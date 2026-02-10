"""Bot keyboards package."""

from app.bot.keyboards.categories import get_categories_keyboard, get_urgency_keyboard
from app.bot.keyboards.csat import get_csat_keyboard
from app.bot.keyboards.operator import (
    get_ticket_actions_keyboard,
    get_ticket_inprogress_keyboard,
)
from app.bot.keyboards.ticket import (
    get_active_ticket_menu,
    get_after_ticket_menu,
    get_done_attachments_keyboard,
    get_preview_keyboard,
    get_reopen_or_new_keyboard,
    get_skip_attachments_keyboard,
    get_summary_keyboard,
)
from app.bot.keyboards.triage import get_skip_contact_keyboard, get_triage_keyboard

__all__ = [
    "get_active_ticket_menu",
    "get_after_ticket_menu",
    "get_categories_keyboard",
    "get_urgency_keyboard",
    "get_csat_keyboard",
    "get_ticket_actions_keyboard",
    "get_ticket_inprogress_keyboard",
    "get_done_attachments_keyboard",
    "get_preview_keyboard",
    "get_reopen_or_new_keyboard",
    "get_skip_attachments_keyboard",
    "get_summary_keyboard",
    "get_skip_contact_keyboard",
    "get_triage_keyboard",
]
