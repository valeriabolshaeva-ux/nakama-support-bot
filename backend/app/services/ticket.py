"""
Ticket business logic service.
"""

import logging
from typing import Optional, List, Tuple

from aiogram import Bot
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.settings import settings
from app.database import operations as ops
from app.database.models import Ticket
from app.services.notification import NotificationService
from app.services.timezone import is_working_hours

logger = logging.getLogger(__name__)


class TicketService:
    """Service for ticket business logic."""
    
    def __init__(self, bot: Bot, session: AsyncSession):
        """
        Initialize ticket service.
        
        Args:
            bot: Aiogram Bot instance
            session: Database session
        """
        self.bot = bot
        self.session = session
        self.notification = NotificationService(bot, session)
    
    async def create_ticket(
        self,
        tg_user_id: int,
        project_id: int,
        category: str,
        description: str,
        tg_username: Optional[str] = None,
        tg_name: Optional[str] = None,
        attachments: Optional[List[dict]] = None,
        priority: str = "normal"
    ) -> Tuple[Ticket, bool]:
        """
        Create a new ticket with full flow.
        
        1. Create ticket in database
        2. Create topic in support group
        3. Send ticket card to topic
        4. Send attachments to topic
        
        Args:
            tg_user_id: Client's Telegram user ID
            project_id: Project ID
            category: Ticket category
            description: Problem description
            tg_username: Client's @username
            tg_name: Client's display name
            attachments: List of attachment dicts
            priority: normal or urgent
        
        Returns:
            Tuple of (Ticket, success_flag)
        """
        attachments = attachments or []
        
        # Get project info for topic name
        project = await ops.get_project_with_client(self.session, project_id)
        
        if not project:
            logger.error(f"Project {project_id} not found")
            return None, False
        
        client_name = project.client.name if project.client else "Unknown"
        project_name = project.name
        
        # Create ticket in database
        ticket = await ops.create_ticket(
            self.session,
            project_id=project_id,
            tg_user_id=tg_user_id,
            category=category,
            support_chat_id=settings.support_chat_id,
            description=description,
            priority=priority
        )
        
        logger.info(f"Created ticket #{ticket.number} for user {tg_user_id}")
        
        # Save description as first message
        await ops.create_message(
            self.session,
            ticket_id=ticket.id,
            direction="client",
            tg_message_id=0,  # Will be updated when we have actual message
            msg_type="text",
            author_tg_user_id=tg_user_id,
            content=description
        )
        
        # Save attachments to database
        for att in attachments:
            await ops.create_message(
                self.session,
                ticket_id=ticket.id,
                direction="client",
                tg_message_id=att.get("message_id", 0),
                msg_type=att.get("type", "document"),
                author_tg_user_id=tg_user_id,
                file_id=att.get("file_id")
            )
        
        # Create topic in support group
        topic_id = await self.notification.create_topic_for_ticket(
            ticket, client_name, project_name
        )
        
        if topic_id:
            # Update ticket with topic ID
            await ops.update_ticket_topic(self.session, ticket.id, topic_id)
            ticket.topic_id = topic_id
            
            # Send ticket card
            await self.notification.send_ticket_card(
                ticket=ticket,
                description=description,
                client_username=tg_username,
                client_name=tg_name,
                client_company=client_name,
                project_name=project_name,
                attachments_count=len(attachments)
            )
            
            # Forward attachments
            if attachments:
                await self.notification.forward_attachments(ticket, attachments)
            
            return ticket, True
        else:
            logger.warning(f"Failed to create topic for ticket #{ticket.number}")
            return ticket, False
    
    async def take_ticket(
        self,
        ticket_id: int,
        operator_id: int,
        operator_username: Optional[str] = None
    ) -> Optional[Ticket]:
        """
        Take ticket in progress.
        
        Args:
            ticket_id: Ticket ID
            operator_id: Operator's Telegram user ID
            operator_username: Operator's @username
        
        Returns:
            Updated ticket or None if already taken
        """
        ticket = await ops.get_ticket_by_id(self.session, ticket_id)
        
        if not ticket:
            return None
        
        # Check if already in progress by another operator
        if ticket.status == "in_progress" and ticket.assigned_to_tg_user_id != operator_id:
            logger.info(f"Ticket #{ticket.number} already taken by {ticket.assigned_to_tg_user_id}")
            return None
        
        # Update status
        ticket = await ops.update_ticket_status(
            self.session, ticket_id, "in_progress", assigned_to=operator_id
        )
        
        if ticket:
            # Notify client
            await self.notification.notify_client_ticket_status(
                ticket.tg_user_id, ticket.number, "in_progress"
            )
        
        return ticket
    
    async def pause_ticket(
        self,
        ticket_id: int,
        operator_id: int,
        reason: str = ""
    ) -> Optional[Ticket]:
        """
        Pause ticket with reason.
        
        Args:
            ticket_id: Ticket ID
            operator_id: Operator's Telegram user ID
            reason: Pause reason
        
        Returns:
            Updated ticket or None
        """
        ticket = await ops.update_ticket_status(
            self.session, ticket_id, "on_hold"
        )
        
        if ticket:
            await self.notification.notify_client_ticket_paused(
                ticket.tg_user_id, ticket.number, reason
            )
        
        return ticket
    
    async def resume_ticket(
        self,
        ticket_id: int,
        operator_id: int
    ) -> Optional[Ticket]:
        """
        Resume paused ticket.
        
        Args:
            ticket_id: Ticket ID
            operator_id: Operator's Telegram user ID
        
        Returns:
            Updated ticket or None
        """
        ticket = await ops.update_ticket_status(
            self.session, ticket_id, "in_progress"
        )
        
        if ticket:
            await self.notification.notify_client_ticket_status(
                ticket.tg_user_id, ticket.number, "resumed"
            )
        
        return ticket
    
    async def close_ticket(
        self,
        ticket_id: int,
        operator_id: int
    ) -> Optional[Ticket]:
        """
        Close ticket successfully.
        
        Args:
            ticket_id: Ticket ID
            operator_id: Operator's Telegram user ID
        
        Returns:
            Updated ticket or None
        """
        ticket = await ops.update_ticket_status(
            self.session, ticket_id, "completed"
        )
        
        if ticket:
            # Notify client with CSAT prompt
            await self.notification.notify_client_ticket_status(
                ticket.tg_user_id, ticket.number, "closed"
            )
        
        return ticket
    
    async def cancel_ticket(
        self,
        ticket_id: int,
        operator_id: int,
        reason: str
    ) -> Optional[Ticket]:
        """
        Cancel ticket with reason.
        
        Args:
            ticket_id: Ticket ID
            operator_id: Operator's Telegram user ID
            reason: Cancellation reason
        
        Returns:
            Updated ticket or None
        """
        ticket = await ops.update_ticket_status(
            self.session, ticket_id, "cancelled"
        )
        
        if ticket:
            await self.notification.notify_client_ticket_cancelled(
                ticket.tg_user_id, ticket.number, reason
            )
        
        return ticket
    
    async def request_details(
        self,
        ticket_id: int
    ) -> bool:
        """
        Send request for details to client.
        
        Args:
            ticket_id: Ticket ID
        
        Returns:
            True if sent successfully
        """
        ticket = await ops.get_ticket_by_id(self.session, ticket_id)
        
        if not ticket:
            return False
        
        return await self.notification.send_request_details(ticket.tg_user_id)
    
    async def forward_operator_reply(
        self,
        ticket: Ticket,
        message,  # aiogram Message
        operator_id: int
    ) -> bool:
        """
        Forward operator's reply to client.
        
        Args:
            ticket: Ticket object
            message: Operator's message
            operator_id: Operator's Telegram user ID
        
        Returns:
            True if forwarded successfully
        """
        # Save message to database
        msg_type = "text"
        content = message.text
        file_id = None
        
        if message.photo:
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
            file_id = message.voice.file_id
        
        await ops.create_message(
            self.session,
            ticket_id=ticket.id,
            direction="operator",
            tg_message_id=message.message_id,
            msg_type=msg_type,
            author_tg_user_id=operator_id,
            content=content,
            file_id=file_id
        )
        
        # Forward to client
        return await self.notification.send_operator_reply_to_client(
            ticket.tg_user_id, message
        )
    
    async def save_feedback(
        self,
        ticket_id: int,
        csat: str,
        comment: Optional[str] = None
    ) -> bool:
        """
        Save CSAT feedback and notify support group.
        
        Args:
            ticket_id: Ticket ID
            csat: positive or negative
            comment: Optional comment
        
        Returns:
            True if saved successfully
        """
        ticket = await ops.get_ticket_by_id(self.session, ticket_id)
        
        if not ticket:
            return False
        
        # Save to database
        await ops.create_feedback(self.session, ticket_id, csat, comment)
        
        # Notify support group
        await self.notification.send_feedback_to_topic(ticket, csat, comment)
        
        return True
    
    def is_working_hours(self) -> bool:
        """Check if current time is within working hours."""
        return is_working_hours()
