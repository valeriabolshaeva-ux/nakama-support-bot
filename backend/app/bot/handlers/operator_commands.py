"""
Operator commands in private chat.

Handles:
- /mytickets - show operator's assigned tickets
- /unassigned - show unassigned tickets
"""

import logging

from aiogram import Bot, F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy.ext.asyncio import AsyncSession

from app.bot.filters.operator import IsOperator
from app.config.categories import get_category_label
from app.config.texts import Texts
from app.database import operations as ops

logger = logging.getLogger(__name__)

router = Router(name="operator_commands")


@router.message(Command("mytickets"), F.chat.type == "private", IsOperator())
async def cmd_my_tickets(
    message: Message,
    session: AsyncSession
) -> None:
    """Show operator's assigned tickets."""
    operator_id = message.from_user.id
    
    # Get active tickets assigned to this operator
    tickets = await ops.get_operator_tickets(session, operator_id, status_filter="active")
    
    if not tickets:
        await message.answer(
            Texts.OPERATOR_MY_TICKETS_HEADER + "\n" + Texts.OPERATOR_NO_TICKETS,
            parse_mode="HTML"
        )
        return
    
    # Build message
    text = Texts.OPERATOR_MY_TICKETS_HEADER + "\n"
    
    builder = InlineKeyboardBuilder()
    
    for ticket in tickets:
        category_label = get_category_label(ticket.category)
        text += Texts.operator_ticket_item(
            number=ticket.number,
            status=ticket.status,
            category=category_label,
            description=ticket.description or ""
        ) + "\n"
        
        # Add button to go to ticket
        builder.button(
            text=f"🔗 #{ticket.number}",
            url=f"https://t.me/c/{str(ticket.support_chat_id)[4:]}/{ticket.topic_id}"
        )
    
    builder.adjust(3)
    
    await message.answer(
        text,
        reply_markup=builder.as_markup() if tickets else None,
        parse_mode="HTML"
    )


@router.message(Command("unassigned"), F.chat.type == "private", IsOperator())
async def cmd_unassigned_tickets(
    message: Message,
    session: AsyncSession
) -> None:
    """Show unassigned (new) tickets."""
    tickets = await ops.get_unassigned_tickets(session)
    
    if not tickets:
        await message.answer(
            Texts.OPERATOR_UNASSIGNED_HEADER + "\n" + Texts.OPERATOR_NO_UNASSIGNED,
            parse_mode="HTML"
        )
        return
    
    # Build message
    text = Texts.OPERATOR_UNASSIGNED_HEADER + "\n"
    
    builder = InlineKeyboardBuilder()
    
    for ticket in tickets:
        category_label = get_category_label(ticket.category)
        text += Texts.operator_ticket_item(
            number=ticket.number,
            status=ticket.status,
            category=category_label,
            description=ticket.description or ""
        ) + "\n"
        
        # Add button to go to ticket
        builder.button(
            text=f"🔗 #{ticket.number}",
            url=f"https://t.me/c/{str(ticket.support_chat_id)[4:]}/{ticket.topic_id}"
        )
    
    builder.adjust(3)
    
    await message.answer(
        text,
        reply_markup=builder.as_markup() if tickets else None,
        parse_mode="HTML"
    )


@router.callback_query(F.data == "op:my_tickets", IsOperator())
async def callback_my_tickets(
    callback: CallbackQuery,
    session: AsyncSession
) -> None:
    """Show operator's tickets via callback."""
    await callback.answer()
    
    operator_id = callback.from_user.id
    tickets = await ops.get_operator_tickets(session, operator_id, status_filter="active")
    
    if not tickets:
        await callback.message.answer(
            Texts.OPERATOR_MY_TICKETS_HEADER + "\n" + Texts.OPERATOR_NO_TICKETS,
            parse_mode="HTML"
        )
        return
    
    text = Texts.OPERATOR_MY_TICKETS_HEADER + "\n"
    
    builder = InlineKeyboardBuilder()
    
    for ticket in tickets:
        category_label = get_category_label(ticket.category)
        text += Texts.operator_ticket_item(
            number=ticket.number,
            status=ticket.status,
            category=category_label,
            description=ticket.description or ""
        ) + "\n"
        
        builder.button(
            text=f"🔗 #{ticket.number}",
            url=f"https://t.me/c/{str(ticket.support_chat_id)[4:]}/{ticket.topic_id}"
        )
    
    builder.adjust(3)
    
    await callback.message.answer(
        text,
        reply_markup=builder.as_markup() if tickets else None,
        parse_mode="HTML"
    )
