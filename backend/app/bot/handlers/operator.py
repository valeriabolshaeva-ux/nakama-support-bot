"""
Operator handlers for Support Group.

Handles:
- Operator button actions (take, close, request details)
- Forwarding operator messages to clients
"""

import logging
from typing import Union

from aiogram import Bot, F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from app.bot.filters.operator import IsOperator, IsSupportGroup
from app.bot.states.ticket import OperatorFlow
from app.config.settings import settings
from app.config.texts import Texts
from app.database import operations as ops
from app.services.ticket import TicketService

logger = logging.getLogger(__name__)

router = Router(name="operator")

# Apply filters to all handlers in this router
router.message.filter(IsSupportGroup())
router.callback_query.filter(IsSupportGroup())


# =============================================================================
# OPERATOR BUTTON ACTIONS
# =============================================================================

@router.callback_query(F.data.startswith("op:take:"), IsOperator())
async def callback_take_ticket(
    callback: CallbackQuery,
    session: AsyncSession,
    bot: Bot
) -> None:
    """Handle 'Take in progress' button."""
    from app.config.categories import get_sla_time, get_category_label
    from app.bot.keyboards.operator import get_ticket_inprogress_keyboard
    
    ticket_id = int(callback.data.split(":")[2])
    operator_id = callback.from_user.id
    operator_username = callback.from_user.username
    
    service = TicketService(bot, session)
    ticket = await service.take_ticket(ticket_id, operator_id, operator_username)
    
    if ticket:
        await callback.answer("Тикет взят в работу!")
        
        # Get SLA time for this category
        sla_time = get_sla_time(ticket.category)
        category_label = get_category_label(ticket.category)
        
        # Build status message with SLA
        status_lines = [
            f"✅ Тикет #{ticket.number} взят в работу",
            f"👤 Оператор: @{operator_username or operator_id}",
            f"📁 Категория: {category_label}",
        ]
        
        if sla_time:
            status_lines.append(f"⏱️ Время на решение: {sla_time}")
        elif ticket.category == "feature":
            status_lines.append("💡 Это запрос на улучшение — без SLA")
        else:
            status_lines.append("📋 Вернитесь к клиенту с деталями")
        
        status_msg = "\n".join(status_lines)
        
        # Send status with action buttons
        await callback.message.reply(
            status_msg,
            reply_markup=get_ticket_inprogress_keyboard(ticket_id)
        )
        
        logger.info(f"Operator {operator_id} took ticket #{ticket.number}")
    else:
        # Ticket already taken by someone else
        existing_ticket = await ops.get_ticket_by_id(session, ticket_id)
        if existing_ticket and existing_ticket.assigned_to_tg_user_id:
            await callback.answer(
                f"Тикет уже в работе!",
                show_alert=True
            )
        else:
            await callback.answer("Ошибка", show_alert=True)


@router.callback_query(F.data.startswith("op:pause:"), IsOperator())
async def callback_pause_ticket(
    callback: CallbackQuery,
    session: AsyncSession,
    state: FSMContext
) -> None:
    """Handle 'Pause' button - ask for reason."""
    ticket_id = int(callback.data.split(":")[2])
    
    ticket = await ops.get_ticket_by_id(session, ticket_id)
    if not ticket:
        await callback.answer("Тикет не найден", show_alert=True)
        return
    
    await callback.answer()
    
    # Save ticket info and ask for reason
    await state.set_state(OperatorFlow.waiting_pause_reason)
    await state.update_data(
        pause_ticket_id=ticket_id,
        pause_ticket_number=ticket.number,
        pause_client_id=ticket.tg_user_id,
        pause_thread_id=callback.message.message_thread_id
    )
    
    await callback.message.reply(
        f"⏸️ Укажите причину паузы для обращения #{ticket.number}:\n\n"
        f"(Причина будет отправлена клиенту)"
    )


@router.callback_query(F.data.startswith("op:resume:"), IsOperator())
async def callback_resume_ticket(
    callback: CallbackQuery,
    session: AsyncSession,
    bot: Bot
) -> None:
    """Handle 'Resume' button."""
    ticket_id = int(callback.data.split(":")[2])
    operator_id = callback.from_user.id
    
    service = TicketService(bot, session)
    ticket = await service.resume_ticket(ticket_id, operator_id)
    
    if ticket:
        await callback.answer("Тикет возобновлён!")
        await callback.message.reply("▶️ Работа над тикетом возобновлена.")
        logger.info(f"Operator {operator_id} resumed ticket #{ticket.number}")
    else:
        await callback.answer("Ошибка", show_alert=True)


@router.callback_query(F.data.startswith("op:close:"), IsOperator())
async def callback_close_ticket(
    callback: CallbackQuery,
    session: AsyncSession,
    bot: Bot
) -> None:
    """Handle 'Close successfully' button."""
    ticket_id = int(callback.data.split(":")[2])
    operator_id = callback.from_user.id
    
    service = TicketService(bot, session)
    ticket = await service.close_ticket(ticket_id, operator_id)
    
    if ticket:
        await callback.answer("Тикет закрыт!")
        await callback.message.reply("✅ Тикет успешно закрыт. CSAT отправлен клиенту.")
        logger.info(f"Operator {operator_id} closed ticket #{ticket.number}")
    else:
        await callback.answer("Ошибка", show_alert=True)


@router.callback_query(F.data.startswith("op:cancel:"), IsOperator())
async def callback_cancel_ticket(
    callback: CallbackQuery,
    session: AsyncSession,
    state: FSMContext
) -> None:
    """Handle 'Cancel' button - ask for reason."""
    ticket_id = int(callback.data.split(":")[2])
    
    ticket = await ops.get_ticket_by_id(session, ticket_id)
    if not ticket:
        await callback.answer("Тикет не найден", show_alert=True)
        return
    
    await callback.answer()
    
    # Save ticket info and ask for reason
    await state.set_state(OperatorFlow.waiting_cancel_reason)
    await state.update_data(
        cancel_ticket_id=ticket_id,
        cancel_ticket_number=ticket.number,
        cancel_client_id=ticket.tg_user_id,
        cancel_thread_id=callback.message.message_thread_id
    )
    
    await callback.message.reply(
        f"📝 Укажите причину отмены обращения #{ticket.number}:\n\n"
        f"(Следующее сообщение будет отправлено клиенту)"
    )


@router.callback_query(F.data.startswith("op:"), ~IsOperator())
async def callback_operator_buttons_no_access(callback: CallbackQuery) -> None:
    """When a non-operator clicks operator buttons — show how to add their ID to OPERATORS."""
    user_id = callback.from_user.id
    logger.warning(
        "Operator button clicked by user_id=%s (not in OPERATORS list: %s)",
        user_id,
        settings.operators,
    )
    await callback.answer(
        Texts.OPERATOR_NEED_ID.format(user_id=user_id),
        show_alert=True
    )


@router.callback_query(F.data.startswith("op:details:"), IsOperator())
async def callback_request_details(
    callback: CallbackQuery,
    session: AsyncSession,
    state: FSMContext
) -> None:
    """Handle 'Request details' button - ask operator for custom question."""
    ticket_id = int(callback.data.split(":")[2])
    
    # Get ticket to show number
    ticket = await ops.get_ticket_by_id(session, ticket_id)
    if not ticket:
        await callback.answer("Тикет не найден", show_alert=True)
        return
    
    await callback.answer()
    
    # Save ticket info to state
    await state.set_state(OperatorFlow.waiting_details_question)
    await state.update_data(
        details_ticket_id=ticket_id,
        details_ticket_number=ticket.number,
        details_client_id=ticket.tg_user_id,
        details_thread_id=callback.message.message_thread_id
    )
    
    await callback.message.reply(
        f"📝 Напишите ваш вопрос для клиента по обращению #{ticket.number}:\n\n"
        f"(Следующее сообщение в этом топике будет отправлено как запрос деталей)"
    )
    
    logger.info(f"Operator started details request for ticket #{ticket.number}")


# =============================================================================
# CUSTOM DETAILS REQUEST
# =============================================================================

@router.message(
    OperatorFlow.waiting_details_question,
    F.text,
    IsOperator()
)
async def handle_details_question(
    message: Message,
    state: FSMContext,
    bot: Bot
) -> None:
    """Handle operator's custom details question."""
    data = await state.get_data()
    
    ticket_number = data.get("details_ticket_number")
    client_id = data.get("details_client_id")
    expected_thread = data.get("details_thread_id")
    
    # Verify we're in the right thread
    if message.message_thread_id != expected_thread:
        return  # Ignore messages from other threads
    
    # Clear state
    await state.clear()
    
    # Format and send to client
    from app.bot.keyboards.ticket import get_after_ticket_menu
    
    details_text = (
        "━━━━━━━━━━━━━━━━━━━━\n"
        "💬 <b>НУЖНО УТОЧНЕНИЕ</b>\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"
        f"🎫 Обращение <b>#{ticket_number}</b>\n\n"
        "Нам нужно ещё немного деталей,\n"
        "чтобы лучше помочь вам 🙏\n\n"
        f"❓ <i>{message.text}</i>"
    )
    
    try:
        await bot.send_message(
            chat_id=client_id,
            text=details_text,
            reply_markup=get_after_ticket_menu(),
            parse_mode="HTML"
        )
        
        await message.reply("✅ Вопрос отправлен клиенту!")
        logger.info(f"Sent custom details request for ticket #{ticket_number}")
        
    except Exception as e:
        logger.error(f"Failed to send details request: {e}")
        await message.reply("❌ Ошибка отправки клиенту")


# =============================================================================
# PAUSE REASON
# =============================================================================

@router.message(
    OperatorFlow.waiting_pause_reason,
    F.text,
    IsOperator()
)
async def handle_pause_reason(
    message: Message,
    state: FSMContext,
    session: AsyncSession,
    bot: Bot
) -> None:
    """Handle operator's pause reason."""
    from app.bot.keyboards.operator import get_ticket_paused_keyboard
    
    data = await state.get_data()
    
    ticket_id = data.get("pause_ticket_id")
    ticket_number = data.get("pause_ticket_number")
    expected_thread = data.get("pause_thread_id")
    
    # Verify we're in the right thread
    if message.message_thread_id != expected_thread:
        return  # Ignore messages from other threads
    
    # Clear state
    await state.clear()
    
    # Pause ticket in database
    service = TicketService(bot, session)
    ticket = await service.pause_ticket(ticket_id, message.from_user.id, message.text)
    
    if ticket:
        await message.reply(
            f"⏸️ Тикет #{ticket_number} поставлен на паузу.\n"
            f"Причина отправлена клиенту.",
            reply_markup=get_ticket_paused_keyboard(ticket_id)
        )
        logger.info(f"Paused ticket #{ticket_number} with reason: {message.text[:50]}...")
    else:
        await message.reply("❌ Ошибка при постановке на паузу")


# =============================================================================
# CANCELLATION REASON
# =============================================================================

@router.message(
    OperatorFlow.waiting_cancel_reason,
    F.text,
    IsOperator()
)
async def handle_cancel_reason(
    message: Message,
    state: FSMContext,
    session: AsyncSession,
    bot: Bot
) -> None:
    """Handle operator's cancellation reason."""
    data = await state.get_data()
    
    ticket_id = data.get("cancel_ticket_id")
    ticket_number = data.get("cancel_ticket_number")
    client_id = data.get("cancel_client_id")
    expected_thread = data.get("cancel_thread_id")
    
    # Verify we're in the right thread
    if message.message_thread_id != expected_thread:
        return  # Ignore messages from other threads
    
    # Clear state
    await state.clear()
    
    # Cancel ticket in database
    service = TicketService(bot, session)
    ticket = await service.cancel_ticket(ticket_id, message.from_user.id, message.text)
    
    if ticket:
        await message.reply("❌ Тикет отменён. Уведомление отправлено клиенту.")
        logger.info(f"Cancelled ticket #{ticket_number} with reason: {message.text[:50]}...")
    else:
        await message.reply("❌ Ошибка при отмене тикета")


# =============================================================================
# OPERATOR MESSAGES TO CLIENTS
# =============================================================================

@router.message(
    F.reply_to_message,
    F.message_thread_id,  # Must be in a topic
    IsOperator()
)
async def handle_operator_reply(
    message: Message,
    session: AsyncSession,
    bot: Bot
) -> None:
    """
    Handle operator's reply in topic - forward to client.
    
    Only processes messages in topics from operators.
    """
    topic_id = message.message_thread_id
    chat_id = message.chat.id
    operator_id = message.from_user.id
    
    # Find ticket by topic
    ticket = await ops.get_ticket_by_topic_id(session, topic_id, chat_id)
    
    if not ticket:
        logger.debug(f"No ticket found for topic {topic_id}")
        return
    
    # Check if ticket is still open
    closed_statuses = ("completed", "cancelled", "closed")
    if ticket.status in closed_statuses:
        return
    
    # Forward reply to client
    service = TicketService(bot, session)
    success = await service.forward_operator_reply(ticket, message, operator_id)
    
    if success:
        # React to confirm message was sent
        try:
            await message.react([{"emoji": "✅"}])
        except Exception:
            pass  # Reactions might not be available
        
        logger.info(f"Forwarded operator reply to client for ticket #{ticket.number}")


@router.message(
    F.message_thread_id,  # In a topic
    ~F.reply_to_message,  # Not a reply
    IsOperator()
)
async def handle_operator_message_in_topic(
    message: Message,
    session: AsyncSession,
    bot: Bot
) -> None:
    """
    Handle operator's direct message in topic - also forward to client.
    
    Any message from operator in ticket topic goes to client.
    """
    topic_id = message.message_thread_id
    chat_id = message.chat.id
    operator_id = message.from_user.id
    
    # Find ticket by topic
    ticket = await ops.get_ticket_by_topic_id(session, topic_id, chat_id)
    
    if not ticket:
        logger.debug(f"No ticket found for topic {topic_id}")
        return
    
    # Check if ticket is still open (not completed/cancelled)
    closed_statuses = ("completed", "cancelled", "closed")
    if ticket.status in closed_statuses:
        return
    
    # Forward to client
    service = TicketService(bot, session)
    success = await service.forward_operator_reply(ticket, message, operator_id)
    
    if success:
        try:
            await message.react([{"emoji": "✅"}])
        except Exception:
            pass
        
        logger.info(f"Forwarded operator message to client for ticket #{ticket.number}")


# =============================================================================
# NON-OPERATOR MESSAGES (IGNORED)
# =============================================================================

@router.message(
    F.message_thread_id,
    ~IsOperator()
)
async def handle_non_operator_message(message: Message) -> None:
    """
    Ignore messages from non-operators in support group topics.
    
    This handler catches and silently ignores messages from users
    who are not in the operators list.
    """
    logger.debug(
        f"Ignored message from non-operator {message.from_user.id} "
        f"in topic {message.message_thread_id}"
    )
    # Do nothing - message is ignored
