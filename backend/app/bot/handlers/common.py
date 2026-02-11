"""
Common handlers: /help, /project, reopen/new ticket.
"""

import logging
from typing import List

from aiogram import Bot, F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy.ext.asyncio import AsyncSession

from app.bot.keyboards import get_categories_keyboard
from app.config.settings import settings
from app.config.texts import Texts
from app.database import operations as ops
from app.database.models import UserBinding
from app.services.notification import NotificationService

logger = logging.getLogger(__name__)

router = Router(name="common")


@router.message(Command("help"))
async def handle_help(message: Message) -> None:
    """Handle /help command."""
    await message.answer(Texts.HELP_TEXT)


@router.message(Command("myid"))
async def handle_myid(message: Message) -> None:
    """Show user's Telegram ID (for adding to OPERATORS in bot settings)."""
    user_id = message.from_user.id
    await message.answer(Texts.MYID_RESPONSE.format(user_id=user_id))


@router.message(Command("am_i_operator"))
async def handle_am_i_operator(message: Message) -> None:
    """Check if current user is in OPERATORS list (for debugging)."""
    user_id = message.from_user.id
    if user_id in settings.operators:
        await message.answer(Texts.AM_I_OPERATOR_YES)
    else:
        await message.answer(Texts.AM_I_OPERATOR_NO.format(user_id=user_id))


@router.message(Command("project"))
async def handle_project(
    message: Message,
    session: AsyncSession
) -> None:
    """
    Handle /project command.
    
    Shows user's projects and allows switching active project.
    """
    user_id = message.from_user.id
    
    # Get all user bindings
    bindings = await ops.get_user_bindings(session, user_id)
    
    if not bindings:
        await message.answer(Texts.ERROR_NOT_BOUND)
        return
    
    if len(bindings) == 1:
        # Single project
        project = bindings[0].project
        project_name = project.name if project else "Unknown"
        await message.answer(Texts.project_single(project_name))
        return
    
    # Multiple projects - show selection
    # Get current active (most recent)
    active_binding = bindings[0]  # Already sorted by updated_at desc
    
    builder = InlineKeyboardBuilder()
    
    for binding in bindings:
        project = binding.project
        if project:
            # Mark active project with checkmark
            prefix = "✓ " if binding.id == active_binding.id else ""
            builder.button(
                text=f"{prefix}{project.name}",
                callback_data=f"project:switch:{project.id}"
            )
    
    builder.adjust(1)
    
    await message.answer(
        Texts.PROJECT_LIST,
        reply_markup=builder.as_markup()
    )


@router.callback_query(F.data.startswith("project:switch:"))
async def callback_switch_project(
    callback: CallbackQuery,
    session: AsyncSession
) -> None:
    """Handle project switch callback."""
    await callback.answer()
    
    # Extract project ID
    project_id = int(callback.data.split(":")[2])
    user_id = callback.from_user.id
    
    # Update active binding
    binding = await ops.update_active_binding(session, user_id, project_id)
    
    if binding:
        project = await ops.get_project_by_id(session, project_id)
        project_name = project.name if project else "Unknown"
        
        logger.info(f"User {user_id} switched to project {project_id}")
        
        await callback.message.answer(Texts.project_switched(project_name))
    else:
        await callback.message.answer(Texts.ERROR_GENERIC)


@router.callback_query(F.data.startswith("ticket:reopen:"))
async def callback_reopen_ticket(
    callback: CallbackQuery,
    session: AsyncSession,
    bot: Bot
) -> None:
    """
    Handle ticket reopen callback.
    
    Reopens the closed ticket and notifies support group.
    """
    await callback.answer()
    
    # Extract ticket number
    ticket_number = int(callback.data.split(":")[2])
    user_id = callback.from_user.id
    
    # Get ticket by number
    ticket = await ops.get_ticket_by_number(session, ticket_number)
    
    if not ticket or ticket.tg_user_id != user_id:
        await callback.message.answer(Texts.ERROR_GENERIC)
        return
    
    # Reopen ticket
    reopened = await ops.reopen_ticket(session, ticket.id)
    
    if reopened:
        logger.info(f"User {user_id} reopened ticket #{ticket_number}")
        
        # Notify support group
        notification = NotificationService(bot, session)
        if ticket.topic_id:
            try:
                await bot.send_message(
                    chat_id=ticket.support_chat_id,
                    message_thread_id=ticket.topic_id,
                    text="🔄 Клиент переоткрыл обращение"
                )
            except Exception as e:
                logger.error(f"Failed to notify reopen: {e}")
        
        await callback.message.answer(Texts.ticket_reopened(ticket_number))
    else:
        await callback.message.answer(Texts.ERROR_GENERIC)


@router.callback_query(F.data == "ticket:new")
async def callback_new_ticket(callback: CallbackQuery) -> None:
    """
    Handle new ticket callback (after offer to reopen).
    
    Shows categories menu to start new ticket flow.
    """
    await callback.answer()
    
    await callback.message.answer(
        Texts.WELCOME_BACK,
        reply_markup=get_categories_keyboard()
    )
