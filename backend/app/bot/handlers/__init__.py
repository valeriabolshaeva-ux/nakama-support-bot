"""Bot handlers package."""

from app.bot.handlers.client_message import router as client_message_router
from app.bot.handlers.common import router as common_router
from app.bot.handlers.csat import router as csat_router
from app.bot.handlers.operator import router as operator_router
from app.bot.handlers.operator_commands import router as operator_commands_router
from app.bot.handlers.start import router as start_router
from app.bot.handlers.ticket import router as ticket_router

__all__ = [
    "start_router",
    "common_router",
    "ticket_router",
    "client_message_router",
    "operator_router",
    "operator_commands_router",
    "csat_router",
]
