"""
Unit tests for database operations.
"""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import operations as ops
from app.database.models import Client, Project


# =============================================================================
# CLIENT TESTS
# =============================================================================

@pytest.mark.asyncio
async def test_create_client(session: AsyncSession):
    """Test client creation."""
    client = await ops.create_client(session, name="New Company")
    
    assert client.id is not None
    assert client.name == "New Company"
    assert client.created_at is not None


@pytest.mark.asyncio
async def test_get_client_by_id(session: AsyncSession):
    """Test getting client by ID."""
    # Create client
    client = await ops.create_client(session, name="Test Client")
    
    # Get by ID
    found = await ops.get_client_by_id(session, client.id)
    
    assert found is not None
    assert found.id == client.id
    assert found.name == "Test Client"


@pytest.mark.asyncio
async def test_get_client_by_id_not_found(session: AsyncSession):
    """Test getting non-existent client."""
    found = await ops.get_client_by_id(session, 99999)
    assert found is None


# =============================================================================
# PROJECT TESTS
# =============================================================================

@pytest.mark.asyncio
async def test_create_project(session: AsyncSession):
    """Test project creation."""
    client = await ops.create_client(session, name="Client")
    project = await ops.create_project(
        session,
        client_id=client.id,
        name="New Project",
        invite_code="NEW001"
    )
    
    assert project.id is not None
    assert project.client_id == client.id
    assert project.name == "New Project"
    assert project.invite_code == "NEW001"
    assert project.is_active is True


@pytest.mark.asyncio
async def test_get_project_by_invite_code(session: AsyncSession, sample_data):
    """Test getting project by invite code."""
    project = await ops.get_project_by_invite_code(session, "TEST001")
    
    assert project is not None
    assert project.name == "Main Project"


@pytest.mark.asyncio
async def test_get_project_by_invite_code_not_found(session: AsyncSession):
    """Test getting project with invalid invite code."""
    project = await ops.get_project_by_invite_code(session, "INVALID")
    assert project is None


@pytest.mark.asyncio
async def test_get_project_with_client(session: AsyncSession, sample_data):
    """Test getting project with client eagerly loaded."""
    project = await ops.get_project_with_client(
        session, 
        sample_data["project1"].id
    )
    
    assert project is not None
    assert project.client is not None
    assert project.client.name == "Test Company"


# =============================================================================
# USER BINDING TESTS
# =============================================================================

@pytest.mark.asyncio
async def test_create_user_binding(session: AsyncSession, sample_data):
    """Test creating user binding."""
    binding = await ops.create_or_update_user_binding(
        session,
        tg_user_id=999999,
        project_id=sample_data["project1"].id,
        tg_username="newuser",
        tg_name="New User"
    )
    
    assert binding.id is not None
    assert binding.tg_user_id == 999999
    assert binding.tg_username == "newuser"


@pytest.mark.asyncio
async def test_update_user_binding(session: AsyncSession, sample_data):
    """Test updating existing user binding."""
    # Update existing binding
    binding = await ops.create_or_update_user_binding(
        session,
        tg_user_id=123456789,  # Same as in sample_data
        project_id=sample_data["project1"].id,
        tg_username="updated_username",
        tg_name="Updated Name"
    )
    
    assert binding.tg_username == "updated_username"
    assert binding.tg_name == "Updated Name"


@pytest.mark.asyncio
async def test_get_user_binding(session: AsyncSession, sample_data):
    """Test getting user binding."""
    binding = await ops.get_user_binding(session, 123456789)
    
    assert binding is not None
    assert binding.tg_user_id == 123456789


@pytest.mark.asyncio
async def test_get_user_binding_not_found(session: AsyncSession):
    """Test getting binding for non-existent user."""
    binding = await ops.get_user_binding(session, 999999999)
    assert binding is None


@pytest.mark.asyncio
async def test_get_user_bindings_multiple(session: AsyncSession, sample_data):
    """Test getting multiple user bindings."""
    # Create second binding
    await ops.create_or_update_user_binding(
        session,
        tg_user_id=123456789,
        project_id=sample_data["project2"].id,
        tg_username="testuser"
    )
    
    bindings = await ops.get_user_bindings(session, 123456789)
    
    assert len(bindings) == 2


# =============================================================================
# TICKET TESTS
# =============================================================================

@pytest.mark.asyncio
async def test_get_next_ticket_number_first(session: AsyncSession):
    """Test getting first ticket number."""
    number = await ops.get_next_ticket_number(session)
    assert number == 1


@pytest.mark.asyncio
async def test_create_ticket(session: AsyncSession, sample_data):
    """Test ticket creation."""
    ticket = await ops.create_ticket(
        session,
        project_id=sample_data["project1"].id,
        tg_user_id=123456789,
        category="bug",
        support_chat_id=-100123456789
    )
    
    assert ticket.id is not None
    assert ticket.number == 1
    assert ticket.status == "new"
    assert ticket.priority == "normal"
    assert ticket.category == "bug"


@pytest.mark.asyncio
async def test_create_ticket_urgent(session: AsyncSession, sample_data):
    """Test urgent ticket creation."""
    ticket = await ops.create_ticket(
        session,
        project_id=sample_data["project1"].id,
        tg_user_id=123456789,
        category="urgent",
        support_chat_id=-100123456789,
        priority="urgent"
    )
    
    assert ticket.priority == "urgent"


@pytest.mark.asyncio
async def test_get_active_ticket(session: AsyncSession, sample_data):
    """Test getting active ticket."""
    # Create ticket
    ticket = await ops.create_ticket(
        session,
        project_id=sample_data["project1"].id,
        tg_user_id=123456789,
        category="bug",
        support_chat_id=-100123456789
    )
    
    # Get active
    active = await ops.get_active_ticket(session, 123456789)
    
    assert active is not None
    assert active.id == ticket.id


@pytest.mark.asyncio
async def test_get_active_ticket_none_when_closed(session: AsyncSession, sample_data):
    """Test that closed ticket is not returned as active."""
    # Create and close ticket
    ticket = await ops.create_ticket(
        session,
        project_id=sample_data["project1"].id,
        tg_user_id=123456789,
        category="bug",
        support_chat_id=-100123456789
    )
    await ops.update_ticket_status(session, ticket.id, "closed")
    
    # Get active
    active = await ops.get_active_ticket(session, 123456789)
    
    assert active is None


@pytest.mark.asyncio
async def test_update_ticket_status_in_progress(session: AsyncSession, sample_data):
    """Test updating ticket to in_progress."""
    ticket = await ops.create_ticket(
        session,
        project_id=sample_data["project1"].id,
        tg_user_id=123456789,
        category="bug",
        support_chat_id=-100123456789
    )
    
    updated = await ops.update_ticket_status(
        session, 
        ticket.id, 
        "in_progress",
        assigned_to=987654321
    )
    
    assert updated.status == "in_progress"
    assert updated.assigned_to_tg_user_id == 987654321
    assert updated.first_response_at is not None


@pytest.mark.asyncio
async def test_update_ticket_status_closed(session: AsyncSession, sample_data):
    """Test closing ticket."""
    ticket = await ops.create_ticket(
        session,
        project_id=sample_data["project1"].id,
        tg_user_id=123456789,
        category="bug",
        support_chat_id=-100123456789
    )
    
    updated = await ops.update_ticket_status(session, ticket.id, "closed")
    
    assert updated.status == "closed"
    assert updated.closed_at is not None


@pytest.mark.asyncio
async def test_ticket_numbers_increment(session: AsyncSession, sample_data):
    """Test that ticket numbers increment correctly."""
    ticket1 = await ops.create_ticket(
        session,
        project_id=sample_data["project1"].id,
        tg_user_id=123456789,
        category="bug",
        support_chat_id=-100123456789
    )
    
    ticket2 = await ops.create_ticket(
        session,
        project_id=sample_data["project1"].id,
        tg_user_id=123456789,
        category="feature",
        support_chat_id=-100123456789
    )
    
    assert ticket1.number == 1
    assert ticket2.number == 2


# =============================================================================
# MESSAGE TESTS
# =============================================================================

@pytest.mark.asyncio
async def test_create_message(session: AsyncSession, sample_data):
    """Test message creation."""
    ticket = await ops.create_ticket(
        session,
        project_id=sample_data["project1"].id,
        tg_user_id=123456789,
        category="bug",
        support_chat_id=-100123456789
    )
    
    message = await ops.create_message(
        session,
        ticket_id=ticket.id,
        direction="client",
        tg_message_id=12345,
        msg_type="text",
        author_tg_user_id=123456789,
        content="Test message"
    )
    
    assert message.id is not None
    assert message.direction == "client"
    assert message.content == "Test message"


@pytest.mark.asyncio
async def test_create_message_with_file(session: AsyncSession, sample_data):
    """Test message creation with file."""
    ticket = await ops.create_ticket(
        session,
        project_id=sample_data["project1"].id,
        tg_user_id=123456789,
        category="bug",
        support_chat_id=-100123456789
    )
    
    message = await ops.create_message(
        session,
        ticket_id=ticket.id,
        direction="client",
        tg_message_id=12345,
        msg_type="photo",
        author_tg_user_id=123456789,
        file_id="AgACAgIAAxkBAAI..."
    )
    
    assert message.type == "photo"
    assert message.file_id is not None


@pytest.mark.asyncio
async def test_get_ticket_messages(session: AsyncSession, sample_data):
    """Test getting ticket messages."""
    ticket = await ops.create_ticket(
        session,
        project_id=sample_data["project1"].id,
        tg_user_id=123456789,
        category="bug",
        support_chat_id=-100123456789
    )
    
    # Create messages
    await ops.create_message(
        session, ticket.id, "client", 1, "text", 123456789, content="First"
    )
    await ops.create_message(
        session, ticket.id, "operator", 2, "text", 987654321, content="Reply"
    )
    
    messages = await ops.get_ticket_messages(session, ticket.id)
    
    assert len(messages) == 2
    assert messages[0].content == "First"
    assert messages[1].content == "Reply"


# =============================================================================
# FEEDBACK TESTS
# =============================================================================

@pytest.mark.asyncio
async def test_create_feedback_positive(session: AsyncSession, sample_data):
    """Test positive feedback creation."""
    ticket = await ops.create_ticket(
        session,
        project_id=sample_data["project1"].id,
        tg_user_id=123456789,
        category="bug",
        support_chat_id=-100123456789
    )
    
    feedback = await ops.create_feedback(
        session,
        ticket_id=ticket.id,
        csat="positive"
    )
    
    assert feedback.id is not None
    assert feedback.csat == "positive"
    assert feedback.comment is None


@pytest.mark.asyncio
async def test_create_feedback_negative_with_comment(session: AsyncSession, sample_data):
    """Test negative feedback with comment."""
    ticket = await ops.create_ticket(
        session,
        project_id=sample_data["project1"].id,
        tg_user_id=123456789,
        category="bug",
        support_chat_id=-100123456789
    )
    
    feedback = await ops.create_feedback(
        session,
        ticket_id=ticket.id,
        csat="negative",
        comment="Slow response"
    )
    
    assert feedback.csat == "negative"
    assert feedback.comment == "Slow response"


@pytest.mark.asyncio
async def test_get_feedback_by_ticket(session: AsyncSession, sample_data):
    """Test getting feedback by ticket."""
    ticket = await ops.create_ticket(
        session,
        project_id=sample_data["project1"].id,
        tg_user_id=123456789,
        category="bug",
        support_chat_id=-100123456789
    )
    await ops.create_feedback(session, ticket.id, "positive")
    
    feedback = await ops.get_feedback_by_ticket(session, ticket.id)
    
    assert feedback is not None
    assert feedback.csat == "positive"


# =============================================================================
# PREDEFINED USER TESTS
# =============================================================================

@pytest.mark.asyncio
async def test_create_predefined_user(session: AsyncSession, sample_data):
    """Test creating a predefined user."""
    predefined = await ops.create_predefined_user(
        session,
        tg_username="predefined_user",
        client_id=sample_data["client"].id
    )
    
    assert predefined.id is not None
    assert predefined.tg_username == "predefined_user"
    assert predefined.client_id == sample_data["client"].id


@pytest.mark.asyncio
async def test_create_predefined_user_normalizes_username(session: AsyncSession, sample_data):
    """Test that username is normalized (lowercase, no @)."""
    predefined = await ops.create_predefined_user(
        session,
        tg_username="@TestUser123",
        client_id=sample_data["client"].id
    )
    
    assert predefined.tg_username == "testuser123"


@pytest.mark.asyncio
async def test_get_client_by_username(session: AsyncSession, sample_data):
    """Test finding client by predefined username."""
    # Create predefined user
    await ops.create_predefined_user(
        session,
        tg_username="vbolshaeva",
        client_id=sample_data["client"].id
    )
    
    # Find by username
    client = await ops.get_client_by_username(session, "vbolshaeva")
    
    assert client is not None
    assert client.id == sample_data["client"].id


@pytest.mark.asyncio
async def test_get_client_by_username_case_insensitive(session: AsyncSession, sample_data):
    """Test that username lookup is case-insensitive."""
    await ops.create_predefined_user(
        session,
        tg_username="lookup_user",
        client_id=sample_data["client"].id
    )
    
    # Search with different case
    client = await ops.get_client_by_username(session, "LOOKUP_USER")
    
    assert client is not None
    assert client.id == sample_data["client"].id


@pytest.mark.asyncio
async def test_get_client_by_username_not_found(session: AsyncSession, sample_data):
    """Test that None is returned for unknown username."""
    client = await ops.get_client_by_username(session, "unknownuser")
    
    assert client is None


@pytest.mark.asyncio
async def test_get_client_by_username_strips_at_sign(session: AsyncSession, sample_data):
    """Test that @ prefix is handled."""
    await ops.create_predefined_user(
        session,
        tg_username="at_user",
        client_id=sample_data["client"].id
    )
    
    # Search with @ prefix
    client = await ops.get_client_by_username(session, "@at_user")
    
    assert client is not None
    assert client.id == sample_data["client"].id


@pytest.mark.asyncio
async def test_update_client_topic(session: AsyncSession, sample_data):
    """Test updating client's topic info."""
    client = await ops.update_client_topic(
        session,
        client_id=sample_data["client"].id,
        topic_id=12345,
        support_chat_id=-100987654321
    )
    
    assert client is not None
    assert client.topic_id == 12345
    assert client.support_chat_id == -100987654321


@pytest.mark.asyncio
async def test_get_predefined_users_by_client(session: AsyncSession, sample_data):
    """Test getting all predefined users for a client."""
    # Create multiple predefined users
    await ops.create_predefined_user(
        session,
        tg_username="batch_user1",
        client_id=sample_data["client"].id
    )
    await ops.create_predefined_user(
        session,
        tg_username="batch_user2",
        client_id=sample_data["client"].id
    )
    
    # Get all for client
    users = await ops.get_predefined_users_by_client(session, sample_data["client"].id)
    
    assert len(users) == 2
    usernames = [u.tg_username for u in users]
    assert "batch_user1" in usernames
    assert "batch_user2" in usernames
