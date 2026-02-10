"""
Database CRUD operations.

All functions are async and require an AsyncSession.
"""

import logging
from datetime import datetime, timedelta
from typing import List, Optional

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database.models import (
    Client,
    Feedback,
    Message,
    PredefinedUser,
    Project,
    Ticket,
    UserBinding,
)


# =============================================================================
# CLIENT OPERATIONS
# =============================================================================

async def get_client_by_id(
    session: AsyncSession,
    client_id: int
) -> Optional[Client]:
    """Get client by ID."""
    result = await session.execute(
        select(Client).where(Client.id == client_id)
    )
    return result.scalar_one_or_none()


async def create_client(
    session: AsyncSession,
    name: str
) -> Client:
    """Create a new client."""
    client = Client(name=name)
    session.add(client)
    await session.commit()
    await session.refresh(client)
    return client


async def get_client_by_username(
    session: AsyncSession,
    tg_username: str
) -> Optional[Client]:
    """
    Get client by predefined Telegram username.
    
    Searches in predefined_users table and returns associated client.
    
    Args:
        session: Database session
        tg_username: Telegram username (without @)
        
    Returns:
        Client if found in predefined_users, None otherwise
    """
    # Normalize username (remove @ if present)
    username = tg_username.lstrip("@").lower()
    
    result = await session.execute(
        select(PredefinedUser)
        .options(selectinload(PredefinedUser.client))
        .where(func.lower(PredefinedUser.tg_username) == username)
    )
    predefined = result.scalar_one_or_none()
    
    if predefined:
        return predefined.client
    return None


async def update_client_topic(
    session: AsyncSession,
    client_id: int,
    topic_id: int,
    support_chat_id: int
) -> Optional[Client]:
    """
    Update client's support topic.
    
    Args:
        session: Database session
        client_id: Client ID
        topic_id: Topic ID in support group
        support_chat_id: Support group chat ID
        
    Returns:
        Updated Client or None if not found
    """
    client = await get_client_by_id(session, client_id)
    if not client:
        return None
    
    client.topic_id = topic_id
    client.support_chat_id = support_chat_id
    
    await session.commit()
    await session.refresh(client)
    return client


async def get_client_with_topic(
    session: AsyncSession,
    client_id: int
) -> Optional[Client]:
    """Get client with topic info."""
    result = await session.execute(
        select(Client).where(Client.id == client_id)
    )
    return result.scalar_one_or_none()


# =============================================================================
# PREDEFINED USER OPERATIONS
# =============================================================================

async def create_predefined_user(
    session: AsyncSession,
    tg_username: str,
    client_id: int
) -> PredefinedUser:
    """
    Create a predefined user mapping.
    
    Args:
        session: Database session
        tg_username: Telegram username (without @)
        client_id: Client ID to bind to
        
    Returns:
        Created PredefinedUser
    """
    # Normalize username
    username = tg_username.lstrip("@").lower()
    
    predefined = PredefinedUser(
        tg_username=username,
        client_id=client_id
    )
    session.add(predefined)
    await session.commit()
    await session.refresh(predefined)
    return predefined


async def get_predefined_user(
    session: AsyncSession,
    tg_username: str
) -> Optional[PredefinedUser]:
    """Get predefined user by username."""
    username = tg_username.lstrip("@").lower()
    
    result = await session.execute(
        select(PredefinedUser)
        .where(func.lower(PredefinedUser.tg_username) == username)
    )
    return result.scalar_one_or_none()


async def get_predefined_users_by_client(
    session: AsyncSession,
    client_id: int
) -> List[PredefinedUser]:
    """Get all predefined users for a client."""
    result = await session.execute(
        select(PredefinedUser)
        .where(PredefinedUser.client_id == client_id)
    )
    return list(result.scalars().all())


# =============================================================================
# PROJECT OPERATIONS
# =============================================================================

async def get_project_by_id(
    session: AsyncSession,
    project_id: int
) -> Optional[Project]:
    """Get project by ID."""
    result = await session.execute(
        select(Project).where(Project.id == project_id)
    )
    return result.scalar_one_or_none()


async def get_project_by_invite_code(
    session: AsyncSession,
    invite_code: str
) -> Optional[Project]:
    """
    Get project by invite code.
    
    Comparison is case-insensitive and trims whitespace from input.
    
    Args:
        session: Database session
        invite_code: Invite code to search (will be stripped)
        
    Returns:
        Project if found and active, None otherwise
    """
    code = invite_code.strip() if invite_code else ""
    if not code:
        return None
    result = await session.execute(
        select(Project)
        .where(Project.invite_code.isnot(None))
        .where(func.lower(Project.invite_code) == code.lower())
        .where(Project.is_active == True)  # noqa: E712
    )
    return result.scalar_one_or_none()


async def get_project_with_client(
    session: AsyncSession,
    project_id: int
) -> Optional[Project]:
    """Get project with client eagerly loaded."""
    result = await session.execute(
        select(Project)
        .options(selectinload(Project.client))
        .where(Project.id == project_id)
    )
    return result.scalar_one_or_none()


async def create_project(
    session: AsyncSession,
    client_id: int,
    name: str,
    invite_code: Optional[str] = None
) -> Project:
    """Create a new project."""
    project = Project(
        client_id=client_id,
        name=name,
        invite_code=invite_code,
        is_active=True
    )
    session.add(project)
    await session.commit()
    await session.refresh(project)
    return project


async def ensure_default_project(session: AsyncSession) -> None:
    """
    If no projects exist, create default client "Nakama" and project with invite_code "nakama".
    Used so first deploy (e.g. on Railway) has a working invite link without running init_data.
    """
    result = await session.execute(select(func.count()).select_from(Project))
    count = result.scalar() or 0
    if count > 0:
        return
    client = await create_client(session, "Nakama")
    await create_project(session, client_id=client.id, name="Support", invite_code="nakama")
    logger = logging.getLogger(__name__)
    logger.info("Created default client Nakama and project with invite code 'nakama'")


# =============================================================================
# USER BINDING OPERATIONS
# =============================================================================

async def get_user_binding(
    session: AsyncSession,
    tg_user_id: int
) -> Optional[UserBinding]:
    """
    Get user's most recent project binding.
    
    Args:
        session: Database session
        tg_user_id: Telegram user ID
        
    Returns:
        Most recent UserBinding or None
    """
    result = await session.execute(
        select(UserBinding)
        .where(UserBinding.tg_user_id == tg_user_id)
        .order_by(UserBinding.updated_at.desc())
        .limit(1)
    )
    return result.scalar_one_or_none()


async def get_user_bindings(
    session: AsyncSession,
    tg_user_id: int
) -> List[UserBinding]:
    """Get all user's project bindings."""
    result = await session.execute(
        select(UserBinding)
        .options(selectinload(UserBinding.project))
        .where(UserBinding.tg_user_id == tg_user_id)
        .order_by(UserBinding.updated_at.desc())
    )
    return list(result.scalars().all())


async def create_or_update_user_binding(
    session: AsyncSession,
    tg_user_id: int,
    project_id: int,
    tg_username: Optional[str] = None,
    tg_name: Optional[str] = None
) -> UserBinding:
    """
    Create or update user binding to project.
    
    If binding exists, updates username/name and updated_at.
    If not, creates new binding.
    """
    # Check existing binding for this user+project
    result = await session.execute(
        select(UserBinding)
        .where(UserBinding.tg_user_id == tg_user_id)
        .where(UserBinding.project_id == project_id)
    )
    binding = result.scalar_one_or_none()
    
    if binding:
        # Update existing
        binding.tg_username = tg_username
        binding.tg_name = tg_name
        binding.updated_at = datetime.utcnow()
    else:
        # Create new
        binding = UserBinding(
            tg_user_id=tg_user_id,
            project_id=project_id,
            tg_username=tg_username,
            tg_name=tg_name
        )
        session.add(binding)
    
    await session.commit()
    await session.refresh(binding)
    return binding


async def update_active_binding(
    session: AsyncSession,
    tg_user_id: int,
    project_id: int
) -> Optional[UserBinding]:
    """
    Set project as active for user (update updated_at to make it most recent).
    """
    result = await session.execute(
        select(UserBinding)
        .where(UserBinding.tg_user_id == tg_user_id)
        .where(UserBinding.project_id == project_id)
    )
    binding = result.scalar_one_or_none()
    
    if binding:
        binding.updated_at = datetime.utcnow()
        await session.commit()
        await session.refresh(binding)
    
    return binding


# =============================================================================
# TICKET OPERATIONS
# =============================================================================

async def get_next_ticket_number(session: AsyncSession) -> int:
    """Get next ticket number (max + 1)."""
    result = await session.execute(
        select(func.coalesce(func.max(Ticket.number), 0))
    )
    max_number = result.scalar_one()
    return max_number + 1


async def get_ticket_by_id(
    session: AsyncSession,
    ticket_id: int
) -> Optional[Ticket]:
    """Get ticket by ID."""
    result = await session.execute(
        select(Ticket).where(Ticket.id == ticket_id)
    )
    return result.scalar_one_or_none()


async def get_ticket_by_number(
    session: AsyncSession,
    number: int
) -> Optional[Ticket]:
    """Get ticket by number."""
    result = await session.execute(
        select(Ticket).where(Ticket.number == number)
    )
    return result.scalar_one_or_none()


async def get_ticket_by_topic_id(
    session: AsyncSession,
    topic_id: int,
    chat_id: int
) -> Optional[Ticket]:
    """Get ticket by topic ID and chat ID."""
    result = await session.execute(
        select(Ticket)
        .where(Ticket.topic_id == topic_id)
        .where(Ticket.support_chat_id == chat_id)
    )
    return result.scalar_one_or_none()


async def get_active_ticket(
    session: AsyncSession,
    tg_user_id: int
) -> Optional[Ticket]:
    """
    Get user's active (non-closed) ticket.
    
    Active statuses: new, in_progress, on_hold.
    Closed statuses: completed, cancelled, closed.
    """
    active_statuses = ("new", "in_progress", "on_hold")
    result = await session.execute(
        select(Ticket)
        .where(Ticket.tg_user_id == tg_user_id)
        .where(Ticket.status.in_(active_statuses))
        .order_by(Ticket.created_at.desc())
        .limit(1)
    )
    return result.scalar_one_or_none()


async def get_user_tickets(
    session: AsyncSession,
    tg_user_id: int,
    limit: int = 10
) -> List[Ticket]:
    """
    Get all user's tickets ordered by creation date (newest first).
    
    Args:
        session: Database session
        tg_user_id: Telegram user ID
        limit: Maximum number of tickets to return
        
    Returns:
        List of Ticket objects
    """
    result = await session.execute(
        select(Ticket)
        .where(Ticket.tg_user_id == tg_user_id)
        .order_by(Ticket.created_at.desc())
        .limit(limit)
    )
    return list(result.scalars().all())


async def get_recent_closed_ticket(
    session: AsyncSession,
    tg_user_id: int,
    hours: int = 48
) -> Optional[Ticket]:
    """
    Get user's recently closed ticket (within hours).
    
    Used for reopen functionality.
    Closed statuses: completed, cancelled, closed.
    """
    cutoff = datetime.utcnow() - timedelta(hours=hours)
    closed_statuses = ("completed", "cancelled", "closed")
    
    result = await session.execute(
        select(Ticket)
        .where(Ticket.tg_user_id == tg_user_id)
        .where(Ticket.status.in_(closed_statuses))
        .where(Ticket.closed_at >= cutoff)
        .order_by(Ticket.closed_at.desc())
        .limit(1)
    )
    return result.scalar_one_or_none()


async def get_ticket_with_project(
    session: AsyncSession,
    ticket_id: int
) -> Optional[Ticket]:
    """Get ticket with project and client eagerly loaded."""
    result = await session.execute(
        select(Ticket)
        .options(
            selectinload(Ticket.project).selectinload(Project.client)
        )
        .where(Ticket.id == ticket_id)
    )
    return result.scalar_one_or_none()


async def get_operator_tickets(
    session: AsyncSession,
    operator_tg_user_id: int,
    status_filter: Optional[str] = None
) -> List[Ticket]:
    """
    Get tickets assigned to operator.
    
    Args:
        session: Database session
        operator_tg_user_id: Operator's Telegram user ID
        status_filter: Optional status filter ('active', 'all', or specific status)
    
    Returns:
        List of Ticket objects
    """
    query = select(Ticket).where(Ticket.assigned_to_tg_user_id == operator_tg_user_id)
    
    if status_filter == "active":
        active_statuses = ("in_progress", "on_hold")
        query = query.where(Ticket.status.in_(active_statuses))
    elif status_filter and status_filter != "all":
        query = query.where(Ticket.status == status_filter)
    
    query = query.order_by(Ticket.updated_at.desc()).limit(20)
    
    result = await session.execute(query)
    return list(result.scalars().all())


async def get_unassigned_tickets(
    session: AsyncSession,
    limit: int = 20
) -> List[Ticket]:
    """
    Get unassigned tickets (new tickets without operator).
    
    Returns:
        List of Ticket objects
    """
    result = await session.execute(
        select(Ticket)
        .where(Ticket.assigned_to_tg_user_id.is_(None))
        .where(Ticket.status == "new")
        .order_by(Ticket.created_at.asc())
        .limit(limit)
    )
    return list(result.scalars().all())


async def create_ticket(
    session: AsyncSession,
    project_id: int,
    tg_user_id: int,
    category: str,
    support_chat_id: int,
    description: Optional[str] = None,
    priority: str = "normal",
    topic_id: Optional[int] = None
) -> Ticket:
    """
    Create a new support ticket.
    
    Args:
        session: Database session
        project_id: Project ID
        tg_user_id: Client's Telegram user ID
        category: Ticket category
        support_chat_id: Support group chat ID
        description: Ticket description text
        priority: normal or urgent
        topic_id: Topic ID in support group (if already created)
        
    Returns:
        Created Ticket
    """
    number = await get_next_ticket_number(session)
    
    ticket = Ticket(
        number=number,
        project_id=project_id,
        tg_user_id=tg_user_id,
        category=category,
        description=description,
        priority=priority,
        status="new",
        support_chat_id=support_chat_id,
        topic_id=topic_id
    )
    session.add(ticket)
    await session.commit()
    await session.refresh(ticket)
    return ticket


async def update_ticket_topic(
    session: AsyncSession,
    ticket_id: int,
    topic_id: int
) -> None:
    """Update ticket's topic ID."""
    await session.execute(
        update(Ticket)
        .where(Ticket.id == ticket_id)
        .values(topic_id=topic_id)
    )
    await session.commit()


async def update_ticket_status(
    session: AsyncSession,
    ticket_id: int,
    status: str,
    assigned_to: Optional[int] = None
) -> Optional[Ticket]:
    """
    Update ticket status.
    
    Handles:
        - Setting assigned_to when status = in_progress
        - Setting first_response_at on first in_progress
        - Setting closed_at when status = closed
    """
    ticket = await get_ticket_by_id(session, ticket_id)
    if not ticket:
        return None
    
    ticket.status = status
    ticket.updated_at = datetime.utcnow()
    
    if status == "in_progress":
        if assigned_to:
            ticket.assigned_to_tg_user_id = assigned_to
        if ticket.first_response_at is None:
            ticket.first_response_at = datetime.utcnow()
    elif status == "closed":
        ticket.closed_at = datetime.utcnow()
    elif status == "new":
        # Reopening: clear closed_at
        ticket.closed_at = None
    
    await session.commit()
    await session.refresh(ticket)
    return ticket


async def reopen_ticket(
    session: AsyncSession,
    ticket_id: int
) -> Optional[Ticket]:
    """Reopen a closed ticket."""
    return await update_ticket_status(session, ticket_id, "in_progress")


# =============================================================================
# MESSAGE OPERATIONS
# =============================================================================

async def create_message(
    session: AsyncSession,
    ticket_id: int,
    direction: str,
    tg_message_id: int,
    msg_type: str,
    author_tg_user_id: int,
    content: Optional[str] = None,
    file_id: Optional[str] = None
) -> Message:
    """
    Save a message to ticket history.
    
    Args:
        session: Database session
        ticket_id: Ticket ID
        direction: client, operator, or system
        tg_message_id: Telegram message ID
        msg_type: text, photo, video, document, voice, audio
        author_tg_user_id: Author's Telegram user ID
        content: Text content (for text messages)
        file_id: Telegram file_id (for media)
        
    Returns:
        Created Message
    """
    message = Message(
        ticket_id=ticket_id,
        direction=direction,
        tg_message_id=tg_message_id,
        type=msg_type,
        content=content,
        file_id=file_id,
        author_tg_user_id=author_tg_user_id
    )
    session.add(message)
    await session.commit()
    await session.refresh(message)
    return message


async def get_ticket_messages(
    session: AsyncSession,
    ticket_id: int,
    limit: int = 100
) -> List[Message]:
    """Get ticket messages ordered by creation time."""
    result = await session.execute(
        select(Message)
        .where(Message.ticket_id == ticket_id)
        .order_by(Message.created_at.asc())
        .limit(limit)
    )
    return list(result.scalars().all())


# =============================================================================
# FEEDBACK OPERATIONS
# =============================================================================

async def get_feedback_by_ticket(
    session: AsyncSession,
    ticket_id: int
) -> Optional[Feedback]:
    """Get feedback for a ticket."""
    result = await session.execute(
        select(Feedback).where(Feedback.ticket_id == ticket_id)
    )
    return result.scalar_one_or_none()


async def create_feedback(
    session: AsyncSession,
    ticket_id: int,
    csat: str,
    comment: Optional[str] = None
) -> Feedback:
    """
    Save CSAT feedback.
    
    Args:
        session: Database session
        ticket_id: Ticket ID
        csat: positive or negative
        comment: Optional comment (usually for negative)
        
    Returns:
        Created Feedback
    """
    feedback = Feedback(
        ticket_id=ticket_id,
        csat=csat,
        comment=comment
    )
    session.add(feedback)
    await session.commit()
    await session.refresh(feedback)
    return feedback


async def update_feedback_comment(
    session: AsyncSession,
    feedback_id: int,
    comment: str
) -> Optional[Feedback]:
    """Update feedback comment."""
    result = await session.execute(
        select(Feedback).where(Feedback.id == feedback_id)
    )
    feedback = result.scalar_one_or_none()
    
    if feedback:
        feedback.comment = comment
        await session.commit()
        await session.refresh(feedback)
    
    return feedback
