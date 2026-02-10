"""
Ticket creation handlers with summary flow.
"""

import logging
from typing import List, Optional

from aiogram import Bot, F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from app.bot.keyboards import (
    get_categories_keyboard,
    get_preview_keyboard,
    get_reopen_or_new_keyboard,
    get_skip_attachments_keyboard,
    get_summary_keyboard,
    get_urgency_keyboard,
)
from app.bot.states.ticket import TicketCreation
from app.config.categories import get_category_by_id, get_category_label
from app.config.settings import settings
from app.config.texts import Texts
from app.database import operations as ops

logger = logging.getLogger(__name__)

router = Router(name="ticket")


# =============================================================================
# CATEGORY SELECTION
# =============================================================================

@router.callback_query(F.data.startswith("category:"))
async def callback_category(
    callback: CallbackQuery,
    state: FSMContext,
    session: AsyncSession
) -> None:
    """Handle category selection."""
    await callback.answer()
    
    # Extract category
    category_id = callback.data.split(":")[1]
    category = get_category_by_id(category_id)
    
    if not category:
        await callback.message.answer(Texts.ERROR_GENERIC)
        return
    
    # Check user binding
    user_id = callback.from_user.id
    binding = await ops.get_user_binding(session, user_id)
    
    if not binding:
        await callback.message.answer(Texts.ERROR_NOT_BOUND)
        return
    
    # Get current state to check if editing
    current_state = await state.get_state()
    is_editing = current_state == TicketCreation.editing_category.state
    
    # Save category to state
    if is_editing:
        # Keep existing data, just update category
        await state.update_data(category=category_id)
        # Go back to summary
        await show_summary(callback.message, state)
    else:
        # New ticket - initialize state
        await state.update_data(
            category=category_id,
            project_id=binding.project_id,
            attachments=[]
        )
        
        # Check if urgent - need additional questions
        if category_id == "urgent":
            await state.set_state(TicketCreation.waiting_urgency_level)
            await callback.message.answer(
                Texts.URGENT_ASK_BLOCKING,
                reply_markup=get_urgency_keyboard()
            )
        else:
            await state.set_state(TicketCreation.waiting_description)
            logger.info(f"Set state to waiting_description for user {user_id}")
            
            # Custom message per category
            category_prompts = {
                "report": Texts.ASK_DESCRIPTION_REPORT,
                "rating": Texts.ASK_DESCRIPTION_RATING,
                "widget": Texts.ASK_DESCRIPTION_WIDGET,
                "access": Texts.ASK_DESCRIPTION_ACCESS,
                "howto": Texts.ASK_DESCRIPTION_HOWTO,
                "billing": Texts.ASK_DESCRIPTION_BILLING,
                "feature": Texts.ASK_DESCRIPTION_FEATURE,
                "other": Texts.ASK_DESCRIPTION_OTHER,
            }
            prompt = category_prompts.get(category_id, Texts.ASK_DESCRIPTION)
            await callback.message.answer(prompt)


# =============================================================================
# URGENT FLOW
# =============================================================================

@router.callback_query(
    TicketCreation.waiting_urgency_level,
    F.data.startswith("urgency:")
)
async def callback_urgency_level(
    callback: CallbackQuery,
    state: FSMContext
) -> None:
    """Handle urgency level selection."""
    await callback.answer()
    
    urgency_level = callback.data.split(":")[1]
    await state.update_data(urgency_level=urgency_level)
    
    await state.set_state(TicketCreation.waiting_urgency_details)
    await callback.message.answer(Texts.URGENT_ASK_DETAILS)


@router.message(TicketCreation.waiting_urgency_details)
async def handle_urgency_details(
    message: Message,
    state: FSMContext
) -> None:
    """Handle urgency details input."""
    details = message.text.strip() if message.text else ""
    
    data = await state.get_data()
    description = f"[{data.get('urgency_level', 'urgent')}] {details}"
    
    await state.update_data(description=description)
    await state.set_state(TicketCreation.waiting_attachments)
    
    await message.answer(
        Texts.ASK_ATTACHMENTS,
        reply_markup=get_skip_attachments_keyboard()
    )


# =============================================================================
# DESCRIPTION
# =============================================================================

@router.message(TicketCreation.waiting_description, F.text)
async def handle_description(
    message: Message,
    state: FSMContext
) -> None:
    """Handle problem description input."""
    logger.info(f"handle_description triggered for user {message.from_user.id}")
    
    description = message.text.strip()
    
    await state.update_data(description=description)
    await state.set_state(TicketCreation.waiting_attachments)
    
    await message.answer(
        Texts.ASK_ATTACHMENTS,
        reply_markup=get_skip_attachments_keyboard()
    )


@router.message(F.chat.type == "private", F.text)
async def handle_description_fallback(
    message: Message,
    state: FSMContext,
    session: AsyncSession,
    bot: Bot
) -> None:
    """
    Fallback handler for description when FSM state is lost but category is in state data.
    Also handles forwarding messages to active tickets.
    """
    user_id = message.from_user.id
    
    # Check if user has category in state data (meaning they're creating a ticket)
    state_data = await state.get_data()
    category = state_data.get("category")
    
    if not category:
        # Not in ticket creation flow - check for active ticket to forward message
        binding = await ops.get_user_binding(session, user_id)
        if not binding:
            await message.answer(Texts.ERROR_NOT_BOUND)
            return
        
        active_ticket = await ops.get_active_ticket(session, user_id)
        if active_ticket:
            # Forward message to ticket topic
            from app.services.notification import NotificationService
            from app.bot.keyboards.ticket import get_active_ticket_menu
            
            # Save message to database
            await ops.create_message(
                session,
                ticket_id=active_ticket.id,
                direction="client",
                tg_message_id=message.message_id,
                msg_type="text",
                author_tg_user_id=user_id,
                content=message.text,
                file_id=None
            )
            
            # Forward to operators
            notification = NotificationService(bot, session)
            await notification.forward_client_message(active_ticket, message)
            
            logger.info(f"Forwarded message from user {user_id} to ticket #{active_ticket.number}")
            
            await message.answer(
                Texts.active_ticket_exists(active_ticket.number),
                reply_markup=get_active_ticket_menu()
            )
            return
        
        # No active ticket - show categories
        await message.answer(
            Texts.WELCOME_BACK,
            reply_markup=get_categories_keyboard()
        )
        return
    
    # User has category but lost state - recover and continue
    if state_data.get("description"):
        # Already has description - this is additional message, skip
        return
    
    logger.info(f"handle_description_fallback recovered ticket flow for user {message.from_user.id}")
    
    description = message.text.strip()
    
    await state.update_data(description=description)
    await state.set_state(TicketCreation.waiting_attachments)
    
    await message.answer(
        Texts.ASK_ATTACHMENTS,
        reply_markup=get_skip_attachments_keyboard()
    )


@router.message(TicketCreation.editing_description, F.text)
async def handle_edit_description(
    message: Message,
    state: FSMContext
) -> None:
    """Handle edited description input."""
    description = message.text.strip()
    
    await state.update_data(description=description)
    
    # Go back to summary
    await show_summary(message, state)


# =============================================================================
# ATTACHMENTS
# =============================================================================

@router.message(
    TicketCreation.waiting_attachments,
    F.photo | F.video | F.document | F.voice | F.audio
)
async def handle_attachment(
    message: Message,
    state: FSMContext
) -> None:
    """Handle file attachment."""
    data = await state.get_data()
    attachments: List[dict] = data.get("attachments", [])
    
    # Determine file type and ID
    if message.photo:
        file_id = message.photo[-1].file_id  # Largest photo
        file_type = "photo"
    elif message.video:
        file_id = message.video.file_id
        file_type = "video"
    elif message.document:
        file_id = message.document.file_id
        file_type = "document"
    elif message.voice:
        file_id = message.voice.file_id
        file_type = "voice"
    elif message.audio:
        file_id = message.audio.file_id
        file_type = "audio"
    else:
        return
    
    attachments.append({
        "file_id": file_id,
        "type": file_type,
        "message_id": message.message_id
    })
    
    await state.update_data(attachments=attachments)
    
    # Show preview button after each attachment
    await message.answer(
        Texts.ATTACHMENTS_MORE,
        reply_markup=get_preview_keyboard()
    )


@router.message(
    TicketCreation.editing_attachments,
    F.photo | F.video | F.document | F.voice | F.audio
)
async def handle_edit_attachment(
    message: Message,
    state: FSMContext
) -> None:
    """Handle file attachment during edit mode."""
    data = await state.get_data()
    attachments: List[dict] = data.get("attachments", [])
    
    # Determine file type and ID
    if message.photo:
        file_id = message.photo[-1].file_id
        file_type = "photo"
    elif message.video:
        file_id = message.video.file_id
        file_type = "video"
    elif message.document:
        file_id = message.document.file_id
        file_type = "document"
    elif message.voice:
        file_id = message.voice.file_id
        file_type = "voice"
    elif message.audio:
        file_id = message.audio.file_id
        file_type = "audio"
    else:
        return
    
    attachments.append({
        "file_id": file_id,
        "type": file_type,
        "message_id": message.message_id
    })
    
    await state.update_data(attachments=attachments)
    
    # Show preview button
    await message.answer(
        Texts.ATTACHMENTS_MORE,
        reply_markup=get_preview_keyboard()
    )


@router.callback_query(
    TicketCreation.waiting_attachments,
    F.data == "ticket:skip_attachments"
)
async def callback_skip_attachments(
    callback: CallbackQuery,
    state: FSMContext
) -> None:
    """Handle skip attachments button - go to summary."""
    await callback.answer()
    await show_summary(callback.message, state)


@router.callback_query(
    TicketCreation.editing_attachments,
    F.data == "ticket:skip_attachments"
)
async def callback_skip_attachments_edit(
    callback: CallbackQuery,
    state: FSMContext
) -> None:
    """Handle skip attachments during edit - clear attachments and go to summary."""
    await callback.answer()
    await state.update_data(attachments=[])
    await show_summary(callback.message, state)


@router.callback_query(
    TicketCreation.waiting_attachments,
    F.data == "ticket:show_summary"
)
async def callback_show_summary(
    callback: CallbackQuery,
    state: FSMContext
) -> None:
    """Handle preview button - show summary."""
    await callback.answer()
    await show_summary(callback.message, state)


@router.callback_query(
    TicketCreation.editing_attachments,
    F.data == "ticket:show_summary"
)
async def callback_show_summary_edit(
    callback: CallbackQuery,
    state: FSMContext
) -> None:
    """Handle preview button during edit - show summary."""
    await callback.answer()
    await show_summary(callback.message, state)


# =============================================================================
# SUMMARY / PREVIEW
# =============================================================================

async def show_summary(message: Message, state: FSMContext) -> None:
    """
    Show ticket summary/preview to user.
    
    Displays:
    - Category
    - Description
    - Attachments count
    - Edit/Cancel/Submit buttons
    """
    data = await state.get_data()
    
    category_id = data.get("category", "other")
    description = data.get("description", "")
    attachments = data.get("attachments", [])
    
    # Get category label with emoji
    category_label = get_category_label(category_id)
    
    # Format summary message
    summary_text = Texts.ticket_summary(
        category=category_label,
        description=description,
        attachments_count=len(attachments)
    )
    
    await state.set_state(TicketCreation.showing_summary)
    
    await message.answer(
        summary_text,
        reply_markup=get_summary_keyboard()
    )


# =============================================================================
# EDIT CALLBACKS
# =============================================================================

@router.callback_query(
    TicketCreation.showing_summary,
    F.data == "ticket:edit_category"
)
async def callback_edit_category(
    callback: CallbackQuery,
    state: FSMContext
) -> None:
    """Handle edit category button."""
    await callback.answer()
    
    await state.set_state(TicketCreation.editing_category)
    await callback.message.answer(
        Texts.EDIT_CATEGORY_PROMPT,
        reply_markup=get_categories_keyboard()
    )


@router.callback_query(
    TicketCreation.showing_summary,
    F.data == "ticket:edit_description"
)
async def callback_edit_description(
    callback: CallbackQuery,
    state: FSMContext
) -> None:
    """Handle edit description button."""
    await callback.answer()
    
    await state.set_state(TicketCreation.editing_description)
    await callback.message.answer(Texts.EDIT_DESCRIPTION_PROMPT)


@router.callback_query(
    TicketCreation.showing_summary,
    F.data == "ticket:edit_attachments"
)
async def callback_edit_attachments(
    callback: CallbackQuery,
    state: FSMContext
) -> None:
    """Handle edit attachments button."""
    await callback.answer()
    
    # Clear current attachments for re-upload
    await state.update_data(attachments=[])
    await state.set_state(TicketCreation.editing_attachments)
    
    await callback.message.answer(
        Texts.EDIT_ATTACHMENTS_PROMPT,
        reply_markup=get_skip_attachments_keyboard()
    )


@router.callback_query(
    TicketCreation.showing_summary,
    F.data == "ticket:cancel"
)
async def callback_cancel_ticket(
    callback: CallbackQuery,
    state: FSMContext
) -> None:
    """Handle cancel ticket button."""
    await callback.answer()
    
    await state.clear()
    await callback.message.answer(Texts.TICKET_CANCELLED)


@router.callback_query(
    TicketCreation.showing_summary,
    F.data == "ticket:submit"
)
async def callback_submit_ticket(
    callback: CallbackQuery,
    state: FSMContext,
    session: AsyncSession,
    bot: Bot
) -> None:
    """Handle submit ticket button - create ticket."""
    await callback.answer()
    await create_ticket_from_state(
        callback.message, 
        state, 
        session, 
        callback.from_user.id, 
        bot
    )


# =============================================================================
# TICKET CREATION
# =============================================================================

async def create_ticket_from_state(
    message: Message,
    state: FSMContext,
    session: AsyncSession,
    user_id: int,
    bot: Bot
) -> None:
    """
    Create ticket from collected state data.
    
    This function:
    1. Creates ticket in database
    2. Creates/uses topic in support group (per client)
    3. Sends ticket card to topic
    4. Sends confirmation to user
    """
    from app.services.ticket import TicketService
    from app.services.timezone import is_working_hours
    
    data = await state.get_data()
    
    category = data.get("category", "other")
    project_id = data.get("project_id")
    description = data.get("description", "")
    attachments = data.get("attachments", [])
    
    if not project_id:
        await message.answer(Texts.ERROR_NOT_BOUND)
        await state.clear()
        return
    
    # Get user info
    user = message.from_user if hasattr(message, 'from_user') and message.from_user else None
    tg_username = user.username if user else None
    tg_name = user.full_name if user else None
    
    # Determine priority
    priority = "urgent" if category == "urgent" else "normal"
    
    # Create ticket using service
    service = TicketService(bot, session)
    ticket, success = await service.create_ticket(
        tg_user_id=user_id,
        project_id=project_id,
        category=category,
        description=description,
        tg_username=tg_username,
        tg_name=tg_name,
        attachments=attachments,
        priority=priority
    )
    
    if not ticket:
        await message.answer(Texts.ERROR_GENERIC)
        await state.clear()
        return
    
    logger.info(f"Created ticket #{ticket.number} for user {user_id}, topic created: {success}")
    
    # Clear state
    await state.clear()
    
    # Check working hours for appropriate message
    off_hours = not is_working_hours()
    
    # Send confirmation with category-specific SLA
    await message.answer(Texts.ticket_created(ticket.number, category=category, off_hours=off_hours))
    
    # Show after-ticket menu
    from app.bot.keyboards import get_after_ticket_menu
    await message.answer(
        Texts.AFTER_TICKET_MENU,
        reply_markup=get_after_ticket_menu()
    )


# =============================================================================
# REOPEN / NEW TICKET
# =============================================================================

@router.callback_query(F.data.startswith("ticket:reopen:"))
async def callback_reopen_ticket(
    callback: CallbackQuery,
    session: AsyncSession
) -> None:
    """Handle ticket reopen callback."""
    await callback.answer()
    
    ticket_number = int(callback.data.split(":")[2])
    ticket = await ops.get_ticket_by_number(session, ticket_number)
    
    if ticket:
        await ops.reopen_ticket(session, ticket.id)
        logger.info(f"Reopened ticket #{ticket_number}")
        await callback.message.answer(Texts.ticket_reopened(ticket_number))
    else:
        await callback.message.answer(Texts.ERROR_GENERIC)


@router.callback_query(F.data == "ticket:new")
async def callback_new_ticket(
    callback: CallbackQuery
) -> None:
    """Handle new ticket button - show categories."""
    await callback.answer()
    await callback.message.answer(
        Texts.WELCOME,
        reply_markup=get_categories_keyboard()
    )


# =============================================================================
# MENU: MY TICKETS & NEW REQUEST
# =============================================================================

@router.callback_query(F.data == "menu:my_tickets")
async def callback_my_tickets(
    callback: CallbackQuery,
    session: AsyncSession
) -> None:
    """Show user's ticket history with detailed info."""
    await callback.answer()
    
    user_id = callback.from_user.id
    tickets = await ops.get_user_tickets(session, user_id, limit=10)
    
    if not tickets:
        from app.bot.keyboards import get_after_ticket_menu
        await callback.message.answer(
            Texts.MY_TICKETS_EMPTY,
            reply_markup=get_after_ticket_menu()
        )
        return
    
    # Status mappings
    status_emojis = {
        "new": "🆕",
        "in_progress": "🔄",
        "on_hold": "⏸️",
        "completed": "✅",
        "cancelled": "❌",
        "closed": "✅"  # legacy support
    }
    
    status_labels = {
        "new": "Новый",
        "in_progress": "В работе",
        "on_hold": "На паузе",
        "completed": "Выполнен",
        "cancelled": "Отменён",
        "closed": "Выполнен"  # legacy support
    }
    
    # Active statuses that allow adding details
    active_statuses = ("new", "in_progress", "on_hold")
    
    # Category labels
    from app.config.categories import get_category_label
    from aiogram.utils.keyboard import InlineKeyboardBuilder
    
    # Build ticket list
    lines = [Texts.MY_TICKETS_HEADER]
    
    # Collect active tickets for buttons
    active_tickets = []
    
    # Progress bar mapping
    progress_bars = {
        "new": Texts.PROGRESS_NEW,
        "in_progress": Texts.PROGRESS_IN_PROGRESS,
        "on_hold": Texts.PROGRESS_ON_HOLD,
        "completed": Texts.PROGRESS_COMPLETED,
        "cancelled": Texts.PROGRESS_CANCELLED,
        "closed": Texts.PROGRESS_COMPLETED  # legacy
    }
    
    for ticket in tickets:
        date_str = ticket.created_at.strftime("%d.%m.%Y")
        time_str = ticket.created_at.strftime("%H:%M")
        status_emoji = status_emojis.get(ticket.status, "❓")
        status_label = status_labels.get(ticket.status, ticket.status)
        category_label = get_category_label(ticket.category)
        progress_bar = progress_bars.get(ticket.status, "⚪⚪⚪⚪")
        
        # Truncate description to 50 chars
        description = ticket.description or ""
        if len(description) > 50:
            description = description[:47] + "..."
        
        line = Texts.MY_TICKETS_ITEM.format(
            number=ticket.number,
            category=category_label,
            description=description,
            date=date_str,
            time=time_str,
            progress_bar=progress_bar,
            status_emoji=status_emoji,
            status=status_label
        )
        lines.append(line)
        
        # Track active tickets
        if ticket.status in active_statuses:
            active_tickets.append(ticket)
    
    # Build keyboard with "Add details" buttons for active tickets
    builder = InlineKeyboardBuilder()
    
    for ticket in active_tickets:
        # Short description for button (max 20 chars)
        short_desc = (ticket.description or "")[:20]
        if len(ticket.description or "") > 20:
            short_desc += "…"
        
        builder.button(
            text=f"📝 #{ticket.number}: {short_desc}",
            callback_data=f"menu:add_details:{ticket.number}"
        )
        # Cancel button for active tickets (only if not yet in progress by operator)
        if ticket.status == "new":
            builder.button(
                text=f"❌ Отменить #{ticket.number}",
                callback_data=f"client:cancel:{ticket.number}"
            )
    
    # Reopen button for recently completed tickets (within 48h)
    from datetime import datetime, timedelta
    cutoff = datetime.utcnow() - timedelta(hours=48)
    
    for ticket in tickets:
        if ticket.status == "completed" and ticket.closed_at and ticket.closed_at >= cutoff:
            # Short description for button
            short_desc = (ticket.description or "")[:15]
            if len(ticket.description or "") > 15:
                short_desc += "…"
            
            builder.button(
                text=f"🔄 #{ticket.number}: {short_desc}",
                callback_data=f"client:reopen:{ticket.number}"
            )
    
    # Only "New request" button - we're already viewing tickets
    builder.button(text=Texts.BTN_NEW_REQUEST, callback_data="menu:new_request")
    
    # Adjust: one button per row
    builder.adjust(1)
    
    await callback.message.answer(
        "\n".join(lines),
        reply_markup=builder.as_markup()
    )


@router.callback_query(F.data == "menu:new_request")
async def callback_new_request(
    callback: CallbackQuery,
    session: AsyncSession,
    state: FSMContext
) -> None:
    """Start new ticket creation from menu."""
    await callback.answer()
    
    # Check if user has binding
    user_id = callback.from_user.id
    binding = await ops.get_user_binding(session, user_id)
    
    if not binding:
        await callback.message.answer(Texts.ERROR_NOT_BOUND)
        return
    
    # Clear any existing state and show categories
    await state.clear()
    await callback.message.answer(
        Texts.WELCOME,
        reply_markup=get_categories_keyboard()
    )


@router.callback_query(F.data.startswith("menu:add_details:"))
async def callback_add_details(
    callback: CallbackQuery,
    session: AsyncSession
) -> None:
    """Prompt user to add details to their ticket."""
    await callback.answer()
    
    ticket_number = int(callback.data.split(":")[2])
    
    # Verify ticket exists and is active
    ticket = await ops.get_ticket_by_number(session, ticket_number)
    
    if not ticket or ticket.status not in ("new", "in_progress", "on_hold"):
        await callback.message.answer(Texts.ERROR_TICKET_NOT_ACTIVE)
        return
    
    await callback.message.answer(
        Texts.add_details_prompt(ticket_number)
    )


# =============================================================================
# CLIENT SELF-CANCEL
# =============================================================================

@router.callback_query(F.data.startswith("client:cancel:"))
async def callback_client_cancel_ticket(
    callback: CallbackQuery,
    session: AsyncSession
) -> None:
    """Show confirmation for client to cancel their ticket."""
    await callback.answer()
    
    ticket_number = int(callback.data.split(":")[2])
    ticket = await ops.get_ticket_by_number(session, ticket_number)
    
    if not ticket:
        await callback.message.answer(Texts.ERROR_GENERIC)
        return
    
    # Only allow cancel if ticket is still "new" (not taken by operator)
    if ticket.status != "new":
        await callback.message.answer(Texts.CLIENT_CANCEL_NOT_ALLOWED)
        return
    
    # Show confirmation
    from aiogram.utils.keyboard import InlineKeyboardBuilder
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Да, отменить", callback_data=f"client:cancel_confirm:{ticket_number}")
    builder.button(text="❌ Нет, оставить", callback_data="menu:my_tickets")
    builder.adjust(2)
    
    await callback.message.answer(
        Texts.CLIENT_CANCEL_CONFIRM.format(number=ticket_number),
        reply_markup=builder.as_markup()
    )


@router.callback_query(F.data.startswith("client:cancel_confirm:"))
async def callback_client_cancel_confirm(
    callback: CallbackQuery,
    session: AsyncSession,
    bot: Bot
) -> None:
    """Confirm and execute client self-cancel."""
    await callback.answer()
    
    ticket_number = int(callback.data.split(":")[2])
    ticket = await ops.get_ticket_by_number(session, ticket_number)
    
    if not ticket or ticket.status != "new":
        await callback.message.answer(Texts.CLIENT_CANCEL_NOT_ALLOWED)
        return
    
    # Update ticket status to cancelled
    await ops.update_ticket_status(session, ticket.id, "cancelled")
    
    # Notify operators in support chat
    from app.services.notification import NotificationService
    notification = NotificationService(bot, session)
    
    try:
        await bot.send_message(
            chat_id=notification.support_chat_id,
            message_thread_id=ticket.topic_id,
            text=f"❌ Клиент сам отменил обращение #{ticket_number}\n\nПричина: Уже неактуально"
        )
    except Exception as e:
        logger.error(f"Failed to notify operators about cancellation: {e}")
    
    # Confirm to client
    from app.bot.keyboards.ticket import get_after_ticket_menu
    await callback.message.answer(
        Texts.CLIENT_CANCEL_SUCCESS.format(number=ticket_number),
        reply_markup=get_after_ticket_menu()
    )


# =============================================================================
# CLIENT REOPEN TICKET
# =============================================================================

@router.callback_query(F.data.startswith("client:reopen:"))
async def callback_client_reopen_ticket(
    callback: CallbackQuery,
    session: AsyncSession
) -> None:
    """Show confirmation for client to reopen their ticket."""
    await callback.answer()
    
    ticket_number = int(callback.data.split(":")[2])
    ticket = await ops.get_ticket_by_number(session, ticket_number)
    
    if not ticket:
        await callback.message.answer(Texts.ERROR_GENERIC)
        return
    
    # Check if ticket was completed recently (within 48h)
    from datetime import datetime, timedelta
    cutoff = datetime.utcnow() - timedelta(hours=48)
    
    if ticket.status != "completed" or not ticket.closed_at or ticket.closed_at < cutoff:
        await callback.message.answer(Texts.REOPEN_TICKET_TOO_OLD)
        return
    
    # Show confirmation
    from aiogram.utils.keyboard import InlineKeyboardBuilder
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Да, переоткрыть", callback_data=f"client:reopen_confirm:{ticket_number}")
    builder.button(text="❌ Нет, создам новый", callback_data="menu:new_request")
    builder.adjust(2)
    
    await callback.message.answer(
        Texts.REOPEN_TICKET_CONFIRM.format(number=ticket_number),
        reply_markup=builder.as_markup()
    )


@router.callback_query(F.data.startswith("client:reopen_confirm:"))
async def callback_client_reopen_confirm(
    callback: CallbackQuery,
    session: AsyncSession,
    bot: Bot
) -> None:
    """Confirm and execute client ticket reopen."""
    await callback.answer()
    
    ticket_number = int(callback.data.split(":")[2])
    ticket = await ops.get_ticket_by_number(session, ticket_number)
    
    if not ticket or ticket.status != "completed":
        await callback.message.answer(Texts.ERROR_GENERIC)
        return
    
    # Reopen ticket - set status back to new
    await ops.update_ticket_status(session, ticket.id, "new")
    
    # Clear closed_at
    ticket.closed_at = None
    await session.commit()
    
    # Notify operators in support chat
    from app.services.notification import NotificationService
    notification = NotificationService(bot, session)
    
    try:
        await bot.send_message(
            chat_id=notification.support_chat_id,
            message_thread_id=ticket.topic_id,
            text=(
                f"🔄 <b>ТИКЕТ ПЕРЕОТКРЫТ</b>\n\n"
                f"Клиент переоткрыл обращение #{ticket_number}\n"
                f"Причина: Проблема вернулась"
            ),
            parse_mode="HTML"
        )
    except Exception as e:
        logger.error(f"Failed to notify operators about reopen: {e}")
    
    # Confirm to client
    from app.bot.keyboards.ticket import get_after_ticket_menu
    await callback.message.answer(
        Texts.REOPEN_TICKET_SUCCESS.format(number=ticket_number),
        reply_markup=get_after_ticket_menu()
    )
