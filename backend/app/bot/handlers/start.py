"""
Start command handler with invite-code support.
"""

import logging
from typing import Optional

from aiogram import F, Router
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message, User
from sqlalchemy.ext.asyncio import AsyncSession

from app.bot.keyboards import get_categories_keyboard, get_triage_keyboard
from app.bot.states.ticket import TriageFlow
from app.config.texts import Texts
from app.database import operations as ops

logger = logging.getLogger(__name__)

router = Router(name="start")


def _display_name(user: Optional[User]) -> str:
    """Get greeting name: first name, or @username, or fallback."""
    if not user:
        return "друг"
    if user.first_name:
        return user.first_name.strip()
    if user.username:
        return f"@{user.username}"
    return "друг"


@router.message(CommandStart(deep_link=True))
async def handle_start_with_code(
    message: Message,
    command: Command,
    session: AsyncSession,
    state: FSMContext
) -> None:
    """
    Handle /start with invite code deep link.
    
    URL format: t.me/<bot>?start=<INVITE_CODE>
    """
    # Clear any existing state
    await state.clear()
    
    # Extract code from deep link
    code = command.args if hasattr(command, 'args') else None
    
    if not code:
        await handle_start_no_code(message, session, state)
        return
    
    logger.info(f"User {message.from_user.id} started with code: {code}")
    
    # Validate invite code
    project = await ops.get_project_by_invite_code(session, code)
    
    if project:
        # Create or update user binding
        await ops.create_or_update_user_binding(
            session,
            tg_user_id=message.from_user.id,
            project_id=project.id,
            tg_username=message.from_user.username,
            tg_name=message.from_user.full_name
        )
        
        # Get project with client for name
        project_with_client = await ops.get_project_with_client(session, project.id)
        project_name = project_with_client.name if project_with_client else project.name
        
        logger.info(f"User {message.from_user.id} bound to project {project.id}")
        
        # Send personalized welcome with categories
        name = _display_name(message.from_user)
        await message.answer(
            Texts.code_accepted_personal(name=name, project_name=project_name),
            reply_markup=get_categories_keyboard()
        )
    else:
        # Invalid code
        logger.warning(f"Invalid invite code: {code}")
        await message.answer(
            Texts.INVALID_CODE,
            reply_markup=get_triage_keyboard()
        )


@router.message(CommandStart())
async def handle_start_no_code(
    message: Message,
    session: AsyncSession,
    state: FSMContext
) -> None:
    """
    Handle /start without invite code.
    
    Priority:
    1. Check if user has existing binding
    2. Check predefined_users by username (auto-bind)
    3. Otherwise show triage
    """
    # Clear any existing state
    await state.clear()
    
    user_id = message.from_user.id
    username = message.from_user.username
    
    # Check existing binding
    binding = await ops.get_user_binding(session, user_id)
    
    if binding:
        # Known user - show categories with personalized greeting
        project = await ops.get_project_with_client(session, binding.project_id)
        project_name = project.name if project else "Unknown"
        
        logger.info(f"Known user {user_id} started, project: {project_name}")
        
        # Check if user has any tickets (to distinguish first visit from return)
        user_tickets = await ops.get_user_tickets(session, user_id, limit=1)
        user_name = message.from_user.full_name or message.from_user.first_name
        
        if user_tickets:
            # Returning user
            welcome_text = Texts.welcome_back_personal(user_name)
        else:
            # First time user (just bound, no tickets yet)
            welcome_text = Texts.welcome_personal(user_name)
        
        await message.answer(
            welcome_text,
            reply_markup=get_categories_keyboard()
        )
        return
    
    # Check predefined_users by username
    if username:
        client = await ops.get_client_by_username(session, username)
        
        if client:
            # Found in predefined users - auto-bind to first project
            # Get first active project of this client
            from sqlalchemy import select
            from app.database.models import Project
            
            result = await session.execute(
                select(Project)
                .where(Project.client_id == client.id)
                .where(Project.is_active == True)  # noqa: E712
                .limit(1)
            )
            project = result.scalar_one_or_none()
            
            if project:
                # Create binding
                await ops.create_or_update_user_binding(
                    session,
                    tg_user_id=user_id,
                    project_id=project.id,
                    tg_username=username,
                    tg_name=message.from_user.full_name
                )
                
                logger.info(
                    f"Auto-bound user {user_id} (@{username}) to client {client.name} "
                    f"via predefined_users"
                )
                
                # Personalized welcome for new auto-bound user
                user_name = message.from_user.full_name or message.from_user.first_name
                welcome_text = Texts.welcome_personal(user_name)
                
                await message.answer(
                    welcome_text,
                    reply_markup=get_categories_keyboard()
                )
                return
    
    # Unknown user - show triage
    logger.info(f"Unknown user {user_id} started without code")
    
    await message.answer(
        Texts.NO_CODE_PROMPT,
        reply_markup=get_triage_keyboard()
    )


# =============================================================================
# TRIAGE CALLBACKS
# =============================================================================

@router.callback_query(F.data == "triage:enter_code")
async def callback_enter_code(
    callback: CallbackQuery,
    state: FSMContext
) -> None:
    """Handle 'Enter code' button - ask user to type code."""
    await callback.answer()
    await state.set_state(TriageFlow.waiting_code)
    
    await callback.message.answer("Введите код проекта:")


@router.message(TriageFlow.waiting_code)
async def handle_code_input(
    message: Message,
    session: AsyncSession,
    state: FSMContext
) -> None:
    """Handle invite code input during triage."""
    code = message.text.strip().upper()
    
    # Validate code
    project = await ops.get_project_by_invite_code(session, code)
    
    if project:
        # Valid code - bind user
        await ops.create_or_update_user_binding(
            session,
            tg_user_id=message.from_user.id,
            project_id=project.id,
            tg_username=message.from_user.username,
            tg_name=message.from_user.full_name
        )
        
        await state.clear()
        
        project_with_client = await ops.get_project_with_client(session, project.id)
        project_name = project_with_client.name if project_with_client else project.name
        
        name = _display_name(message.from_user)
        await message.answer(
            Texts.code_accepted_personal(name=name, project_name=project_name),
            reply_markup=get_categories_keyboard()
        )
    else:
        # Invalid code
        await message.answer(
            Texts.INVALID_CODE,
            reply_markup=get_triage_keyboard()
        )
        await state.clear()


@router.callback_query(F.data == "triage:no_code")
async def callback_no_code(
    callback: CallbackQuery,
    state: FSMContext
) -> None:
    """Handle 'No code' button - start triage flow."""
    await callback.answer()
    await state.set_state(TriageFlow.waiting_company)
    
    await callback.message.answer(Texts.TRIAGE_ASK_COMPANY)


@router.message(TriageFlow.waiting_company)
async def handle_company_input(
    message: Message,
    state: FSMContext
) -> None:
    """Handle company name input during triage."""
    company = message.text.strip()
    
    await state.update_data(company=company)
    await state.set_state(TriageFlow.waiting_contact)
    
    from app.bot.keyboards import get_skip_contact_keyboard
    
    await message.answer(
        Texts.TRIAGE_ASK_CONTACT,
        reply_markup=get_skip_contact_keyboard()
    )


@router.callback_query(F.data == "triage:skip_contact")
async def callback_skip_contact(
    callback: CallbackQuery,
    state: FSMContext,
    session: AsyncSession
) -> None:
    """Handle skip contact button."""
    await callback.answer()
    await finish_triage(callback.message, state, session, contact=None)


@router.message(TriageFlow.waiting_contact)
async def handle_contact_input(
    message: Message,
    state: FSMContext,
    session: AsyncSession
) -> None:
    """Handle contact input during triage."""
    contact = message.text.strip()
    await finish_triage(message, state, session, contact=contact)


async def finish_triage(
    message: Message,
    state: FSMContext,
    session: AsyncSession,
    contact: Optional[str]
) -> None:
    """
    Complete triage flow.
    
    TODO: Create triage ticket and send to TRIAGE topic.
    """
    data = await state.get_data()
    company = data.get("company", "Unknown")
    
    logger.info(f"Triage completed: company={company}, contact={contact}")
    
    # TODO: Create triage ticket when ticket handlers are ready
    # For now, just acknowledge
    
    await state.clear()
    await message.answer(Texts.TRIAGE_DONE)
