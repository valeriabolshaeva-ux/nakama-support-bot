"""
Handler for client messages (when ticket is active).
"""

import logging
from typing import TYPE_CHECKING

from aiogram import Bot, F, Router
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

from app.bot.keyboards import get_categories_keyboard, get_reopen_or_new_keyboard
from app.bot.keyboards.ticket import get_active_ticket_menu
from app.config.texts import Texts
from app.database import operations as ops
from app.services.notification import NotificationService

if TYPE_CHECKING:
    from app.database.models import Ticket

logger = logging.getLogger(__name__)

router = Router(name="client_message")


@router.message(F.chat.type == "private")
async def handle_client_message(
    message: Message,
    session: AsyncSession,
    bot: Bot,
    state: FSMContext
) -> None:
    """
    Handle messages from clients in private chat.
    
    Logic:
    0. If user is in ticket creation flow - skip (let ticket handlers process)
    1. If user has active ticket - forward to that ticket's topic
    2. If user has recently closed ticket - offer reopen or new
    3. Otherwise - show categories menu
    """
    user_id = message.from_user.id
    
    logger.info(f"handle_client_message: got message from user {user_id}")
    
    # Check if user is in any FSM state (creating ticket, etc.)
    current_state = await state.get_state()
    if current_state is not None:
        logger.info(f"Skipping client_message handler - user {user_id} has state: {current_state}")
        return
    
    # Also check state data - if category is set, user is creating a ticket
    state_data = await state.get_data()
    if state_data.get("category"):
        logger.debug(f"Skipping client_message handler - user {user_id} has category in state data")
        return
    
    logger.debug(f"handle_client_message triggered for user {user_id}")
    
    # Check user binding first
    binding = await ops.get_user_binding(session, user_id)
    logger.info(f"User {user_id} binding: {binding}")
    
    if not binding:
        await message.answer(Texts.ERROR_NOT_BOUND)
        return
    
    # Check for active ticket
    active_ticket = await ops.get_active_ticket(session, user_id)
    logger.info(f"User {user_id} active_ticket: {active_ticket}")
    
    if active_ticket:
        # User has active ticket - add message to it
        logger.info(f"Forwarding message from user {user_id} to ticket #{active_ticket.number}")
        await add_message_to_ticket(message, session, active_ticket, bot)
        return
    
    # Check for recently closed ticket (< 48 hours)
    recent_ticket = await ops.get_recent_closed_ticket(session, user_id, hours=48)
    
    if recent_ticket:
        # Offer reopen or new
        await message.answer(
            Texts.reopen_or_new(recent_ticket.number),
            reply_markup=get_reopen_or_new_keyboard(recent_ticket.number)
        )
        return
    
    # No active or recent ticket - show categories
    await message.answer(
        Texts.WELCOME_BACK,
        reply_markup=get_categories_keyboard()
    )


async def add_message_to_ticket(
    message: Message,
    session: AsyncSession,
    ticket: "Ticket",
    bot: Bot
) -> None:
    """
    Add client message to existing ticket.
    
    Saves message to DB and forwards to support group topic.
    """
    user_id = message.from_user.id
    
    # Determine message type and content
    if message.text:
        msg_type = "text"
        content = message.text
        file_id = None
    elif message.photo:
        msg_type = "photo"
        content = message.caption
        file_id = message.photo[-1].file_id
    elif message.video:
        msg_type = "video"
        content = message.caption
        file_id = message.video.file_id
    elif message.document:
        msg_type = "document"
        content = message.caption
        file_id = message.document.file_id
    elif message.voice:
        msg_type = "voice"
        content = None
        file_id = message.voice.file_id
    elif message.audio:
        msg_type = "audio"
        content = message.caption
        file_id = message.audio.file_id
    else:
        # Unsupported message type
        return
    
    # Save message to database
    await ops.create_message(
        session,
        ticket_id=ticket.id,
        direction="client",
        tg_message_id=message.message_id,
        msg_type=msg_type,
        author_tg_user_id=user_id,
        content=content,
        file_id=file_id
    )
    
    logger.info(f"Added message to ticket #{ticket.number} from user {user_id}")
    
    # Forward message to support group topic
    notification = NotificationService(bot, session)
    await notification.forward_client_message(ticket, message)
    
    # Acknowledge with menu
    await message.answer(
        Texts.active_ticket_exists(ticket.number),
        reply_markup=get_active_ticket_menu()
    )
