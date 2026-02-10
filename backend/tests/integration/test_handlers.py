"""
Integration tests for bot handlers.

Tests handler logic with mocked Telegram API.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock

from aiogram.types import User, Chat, Message, CallbackQuery

from app.bot.handlers.common import handle_help, handle_project
from app.database import operations as ops
from app.config.texts import Texts


def create_mock_user(user_id: int = 123456, username: str = "testuser", first_name: str = "Test") -> User:
    """Create a mock Telegram user."""
    return User(
        id=user_id,
        is_bot=False,
        first_name=first_name,
        username=username,
    )


def create_mock_message(
    text: str = "test",
    user: User = None,
    chat_id: int = 123456,
    message_id: int = 1
) -> Message:
    """Create a mock Telegram message."""
    if user is None:
        user = create_mock_user()
    
    chat = Chat(id=chat_id, type="private")
    
    message = MagicMock(spec=Message)
    message.text = text
    message.from_user = user
    message.chat = chat
    message.message_id = message_id
    message.answer = AsyncMock()
    message.reply = AsyncMock()
    message.photo = None
    message.video = None
    message.document = None
    message.voice = None
    message.audio = None
    message.caption = None
    
    return message


def create_mock_callback(
    data: str,
    user: User = None,
    message: Message = None
) -> CallbackQuery:
    """Create a mock callback query."""
    if user is None:
        user = create_mock_user()
    if message is None:
        message = create_mock_message(user=user)
    
    callback = MagicMock(spec=CallbackQuery)
    callback.data = data
    callback.from_user = user
    callback.message = message
    callback.answer = AsyncMock()
    
    return callback


class TestHelpHandler:
    """Tests for /help command."""
    
    @pytest.mark.asyncio
    async def test_help_returns_help_text(self):
        """Test that /help returns help text."""
        message = create_mock_message("/help")
        
        await handle_help(message)
        
        message.answer.assert_called_once_with(Texts.HELP_TEXT)


class TestProjectHandler:
    """Tests for /project command."""
    
    @pytest.mark.asyncio
    async def test_project_no_binding_shows_error(self, session):
        """Test /project without binding shows error."""
        message = create_mock_message("/project")
        
        await handle_project(message, session)
        
        message.answer.assert_called_once_with(Texts.ERROR_NOT_BOUND)
    
    @pytest.mark.asyncio
    async def test_project_single_binding_shows_info(self, session):
        """Test /project with single binding shows project info."""
        # Create binding
        client = await ops.create_client(session, "Client")
        project = await ops.create_project(session, client.id, "My Project")
        await ops.create_or_update_user_binding(
            session,
            tg_user_id=123456,
            project_id=project.id
        )
        
        message = create_mock_message("/project")
        
        await handle_project(message, session)
        
        message.answer.assert_called_once()
        call_args = message.answer.call_args
        assert "My Project" in call_args[0][0]


class TestDatabaseOperationsIntegration:
    """Integration tests for database operations."""
    
    @pytest.mark.asyncio
    async def test_full_ticket_lifecycle(self, session):
        """Test complete ticket lifecycle: create -> update -> close."""
        # Setup
        client = await ops.create_client(session, "Test Client")
        project = await ops.create_project(session, client.id, "Test Project")
        
        # Create ticket
        ticket = await ops.create_ticket(
            session,
            project_id=project.id,
            tg_user_id=12345,
            category="bug",
            support_chat_id=-100123,
            priority="normal"
        )
        
        assert ticket.status == "new"
        assert ticket.number == 1
        
        # Take ticket (in_progress)
        updated = await ops.update_ticket_status(
            session,
            ticket.id,
            "in_progress",
            assigned_to=99999
        )
        
        assert updated.status == "in_progress"
        assert updated.assigned_to_tg_user_id == 99999
        assert updated.first_response_at is not None
        
        # Close ticket
        closed = await ops.update_ticket_status(session, ticket.id, "closed")
        
        assert closed.status == "closed"
        assert closed.closed_at is not None
    
    @pytest.mark.asyncio
    async def test_user_binding_flow(self, session):
        """Test user binding creation and retrieval."""
        client = await ops.create_client(session, "Client")
        project = await ops.create_project(
            session,
            client.id,
            "Project",
            invite_code="ABC123"
        )
        
        # Find by invite code
        found = await ops.get_project_by_invite_code(session, "ABC123")
        assert found is not None
        assert found.id == project.id
        
        # Create binding
        binding = await ops.create_or_update_user_binding(
            session,
            tg_user_id=555,
            project_id=project.id,
            tg_username="user555",
            tg_name="User 555"
        )
        
        assert binding.tg_user_id == 555
        assert binding.project_id == project.id
        
        # Retrieve binding
        retrieved = await ops.get_user_binding(session, 555)
        assert retrieved is not None
        assert retrieved.tg_username == "user555"
    
    @pytest.mark.asyncio
    async def test_message_creation_and_retrieval(self, session):
        """Test message saving and retrieval."""
        # Setup
        client = await ops.create_client(session, "Client")
        project = await ops.create_project(session, client.id, "Project")
        ticket = await ops.create_ticket(
            session,
            project_id=project.id,
            tg_user_id=123,
            category="bug",
            support_chat_id=-100123
        )
        
        # Create messages
        msg1 = await ops.create_message(
            session,
            ticket_id=ticket.id,
            direction="client",
            tg_message_id=1,
            msg_type="text",
            author_tg_user_id=123,
            content="Hello, I have a problem"
        )
        
        msg2 = await ops.create_message(
            session,
            ticket_id=ticket.id,
            direction="operator",
            tg_message_id=2,
            msg_type="text",
            author_tg_user_id=999,
            content="Hi, let me help you"
        )
        
        # Retrieve messages
        messages = await ops.get_ticket_messages(session, ticket.id)
        
        assert len(messages) == 2
        assert messages[0].direction == "client"
        assert messages[1].direction == "operator"
    
    @pytest.mark.asyncio
    async def test_feedback_creation(self, session):
        """Test feedback creation."""
        # Setup
        client = await ops.create_client(session, "Client")
        project = await ops.create_project(session, client.id, "Project")
        ticket = await ops.create_ticket(
            session,
            project_id=project.id,
            tg_user_id=123,
            category="bug",
            support_chat_id=-100123
        )
        
        # Create positive feedback
        feedback = await ops.create_feedback(
            session,
            ticket_id=ticket.id,
            csat="positive"
        )
        
        assert feedback.csat == "positive"
        assert feedback.comment is None
        
        # Retrieve
        retrieved = await ops.get_feedback_by_ticket(session, ticket.id)
        assert retrieved is not None
        assert retrieved.csat == "positive"


class TestTextsIntegration:
    """Tests for text template integration."""
    
    def test_ticket_created_contains_number(self):
        """Test ticket created message contains ticket number."""
        message = Texts.ticket_created(42)
        assert "#42" in message
    
    def test_ticket_created_urgent_has_emoji(self):
        """Test urgent ticket message has warning emoji."""
        message = Texts.ticket_created(42, urgent=True)
        assert "🚨" in message
        assert "#42" in message
    
    def test_off_hours_message_mentions_time(self):
        """Test off-hours message mentions working hours."""
        message = Texts.ticket_created(42, off_hours=True)
        assert "нерабочее время" in message
    
    def test_operator_reply_formats_correctly(self):
        """Test operator reply formatting."""
        reply = Texts.operator_reply("Hello, your issue is fixed!")
        assert "Hello, your issue is fixed!" in reply
        assert "поддержки" in reply.lower()
    
    def test_reopen_button_text(self):
        """Test reopen button text formatting."""
        text = Texts.reopen_button(123)
        assert "123" in text
        assert "Продолжить" in text
    
    def test_code_accepted_includes_project(self):
        """Test code accepted message includes project name."""
        message = Texts.code_accepted("Awesome Project")
        assert "Awesome Project" in message
