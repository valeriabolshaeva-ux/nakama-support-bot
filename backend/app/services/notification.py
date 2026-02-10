"""
Notification service for Support Group communication.

Handles:
- Creating topics in support group
- Sending ticket cards
- Forwarding messages between clients and operators
"""

import logging
from datetime import datetime
from typing import Optional, List

from aiogram import Bot
from aiogram.types import Message
from aiogram.exceptions import TelegramAPIError
from sqlalchemy.ext.asyncio import AsyncSession

from app.bot.keyboards.operator import (
    get_ticket_actions_keyboard,
    get_ticket_inprogress_keyboard,
)
from app.config.categories import get_category_label
from app.config.settings import settings
from app.database import operations as ops
from app.database.models import Ticket
from app.services.timezone import get_current_time

logger = logging.getLogger(__name__)


class NotificationService:
    """Service for sending notifications to Support Group."""
    
    def __init__(self, bot: Bot, session: AsyncSession):
        """
        Initialize notification service.
        
        Args:
            bot: Aiogram Bot instance
            session: Database session
        """
        self.bot = bot
        self.session = session
        self.support_chat_id = settings.support_chat_id
    
    async def get_or_create_client_topic(
        self,
        client_id: int,
        client_name: str
    ) -> Optional[int]:
        """
        Get existing topic for client or create new one.
        
        One topic per client (company). All tickets from this client
        go to the same topic.
        
        Args:
            client_id: Client ID
            client_name: Client company name
        
        Returns:
            Topic (thread) ID
        """
        # Check if client already has a topic
        client = await ops.get_client_with_topic(self.session, client_id)
        
        if client and client.topic_id:
            logger.debug(f"Using existing topic {client.topic_id} for client {client_name}")
            return client.topic_id
        
        # Create new topic for client
        topic_name = f"🏢 {client_name}"
        
        # Truncate if too long
        if len(topic_name) > 120:
            topic_name = topic_name[:117] + "..."
        
        try:
            result = await self.bot.create_forum_topic(
                chat_id=self.support_chat_id,
                name=topic_name
            )
            
            topic_id = result.message_thread_id
            
            # Save topic to client
            await ops.update_client_topic(
                self.session,
                client_id=client_id,
                topic_id=topic_id,
                support_chat_id=self.support_chat_id
            )
            
            logger.info(f"Created topic {topic_id} for client {client_name}")
            return topic_id
            
        except TelegramAPIError as e:
            logger.error(f"Failed to create topic for client {client_name}: {e}")
            return None
    
    async def create_topic_for_ticket(
        self,
        ticket: Ticket,
        client_name: str,
        project_name: str
    ) -> Optional[int]:
        """
        DEPRECATED: Use get_or_create_client_topic instead.
        
        Create a new topic in Support Group for ticket.
        Now uses client-level topic (one per company).
        
        Args:
            ticket: Ticket object
            client_name: Client company name
            project_name: Project name
        
        Returns:
            Topic (thread) ID if created, None on error
        """
        # Get project with client to get client_id
        project = await ops.get_project_with_client(self.session, ticket.project_id)
        
        if project and project.client:
            return await self.get_or_create_client_topic(
                client_id=project.client.id,
                client_name=client_name
            )
        
        # Fallback: create ticket-specific topic (old behavior)
        category_label = get_category_label(ticket.category)
        topic_name = f"#{ticket.number} | {client_name} | {project_name} | {category_label}"
        
        if len(topic_name) > 120:
            topic_name = topic_name[:117] + "..."
        
        try:
            result = await self.bot.create_forum_topic(
                chat_id=self.support_chat_id,
                name=topic_name
            )
            
            logger.info(f"Created topic {result.message_thread_id} for ticket #{ticket.number}")
            return result.message_thread_id
            
        except TelegramAPIError as e:
            logger.error(f"Failed to create topic for ticket #{ticket.number}: {e}")
            return None
    
    async def send_ticket_card(
        self,
        ticket: Ticket,
        description: str,
        client_username: Optional[str] = None,
        client_name: Optional[str] = None,
        client_company: Optional[str] = None,
        project_name: Optional[str] = None,
        attachments_count: int = 0
    ) -> Optional[int]:
        """
        Send ticket card to topic.
        
        Args:
            ticket: Ticket object
            description: Problem description
            client_username: Client's Telegram @username
            client_name: Client's display name
            client_company: Client's company name
            project_name: Project name
            attachments_count: Number of attachments
        
        Returns:
            Message ID if sent, None on error
        """
        if not ticket.topic_id:
            logger.error(f"Ticket #{ticket.number} has no topic_id")
            return None
        
        # Format user info
        user_info = f"@{client_username}" if client_username else client_name or "Unknown"
        user_info += f" (id: {ticket.tg_user_id})"
        
        # Format time
        tz_time = get_current_time()
        time_str = tz_time.strftime("%Y-%m-%d %H:%M")
        
        # Format priority
        priority_emoji = "🚨" if ticket.priority == "urgent" else "📋"
        priority_text = "urgent" if ticket.priority == "urgent" else "normal"
        
        # Format attachments
        att_text = f"да ({attachments_count} шт.)" if attachments_count > 0 else "нет"
        
        # Build card
        card = f"""
{priority_emoji} <b>Ticket:</b> #{ticket.number}
👤 <b>Клиент/проект:</b> {client_company or 'Unknown'} / {project_name or 'Unknown'}
💬 <b>Пользователь:</b> {user_info}
📁 <b>Категория:</b> {get_category_label(ticket.category)}
🔥 <b>Приоритет:</b> {priority_text}
🕐 <b>Время:</b> {time_str}

📝 <b>Описание:</b>
{description}

📎 <b>Вложения:</b> {att_text}

📊 <b>Статус:</b> {ticket.status}
""".strip()
        
        try:
            message = await self.bot.send_message(
                chat_id=self.support_chat_id,
                message_thread_id=ticket.topic_id,
                text=card,
                reply_markup=get_ticket_actions_keyboard(ticket.id)
            )
            
            logger.info(f"Sent ticket card for #{ticket.number} to topic {ticket.topic_id}")
            return message.message_id
            
        except TelegramAPIError as e:
            logger.error(f"Failed to send ticket card for #{ticket.number}: {e}")
            return None
    
    async def forward_client_message(
        self,
        ticket: Ticket,
        message: Message
    ) -> bool:
        """
        Forward client message to ticket's topic with context header.
        
        Args:
            ticket: Ticket object
            message: Client's message to forward
        
        Returns:
            True if forwarded successfully
        """
        if not ticket.topic_id:
            logger.error(f"Ticket #{ticket.number} has no topic_id")
            return False
        
        try:
            # Get user info
            user = message.from_user
            user_name = user.full_name if user else "Клиент"
            username = f"@{user.username}" if user and user.username else ""
            
            # Send context header first
            header = (
                f"━━━━━━━━━━━━━━━━━━━━\n"
                f"📩 <b>Доп. сообщение к тикету #{ticket.number}</b>\n"
                f"👤 От: {user_name} {username}\n"
                f"━━━━━━━━━━━━━━━━━━━━"
            )
            
            await self.bot.send_message(
                chat_id=self.support_chat_id,
                message_thread_id=ticket.topic_id,
                text=header,
                parse_mode="HTML"
            )
            
            # Forward the original message
            await self.bot.forward_message(
                chat_id=self.support_chat_id,
                message_thread_id=ticket.topic_id,
                from_chat_id=message.chat.id,
                message_id=message.message_id
            )
            
            logger.debug(f"Forwarded message to topic {ticket.topic_id}")
            return True
            
        except TelegramAPIError as e:
            logger.error(f"Failed to forward message to topic {ticket.topic_id}: {e}")
            return False
    
    async def forward_attachments(
        self,
        ticket: Ticket,
        attachments: List[dict]
    ) -> int:
        """
        Forward attachments to ticket's topic.
        
        Args:
            ticket: Ticket object
            attachments: List of attachment dicts with file_id and type
        
        Returns:
            Number of successfully forwarded attachments
        """
        if not ticket.topic_id:
            return 0
        
        sent = 0
        
        for att in attachments:
            file_id = att.get("file_id")
            file_type = att.get("type", "document")
            
            if not file_id:
                continue
            
            try:
                if file_type == "photo":
                    await self.bot.send_photo(
                        chat_id=self.support_chat_id,
                        message_thread_id=ticket.topic_id,
                        photo=file_id
                    )
                elif file_type == "video":
                    await self.bot.send_video(
                        chat_id=self.support_chat_id,
                        message_thread_id=ticket.topic_id,
                        video=file_id
                    )
                elif file_type == "voice":
                    await self.bot.send_voice(
                        chat_id=self.support_chat_id,
                        message_thread_id=ticket.topic_id,
                        voice=file_id
                    )
                elif file_type == "audio":
                    await self.bot.send_audio(
                        chat_id=self.support_chat_id,
                        message_thread_id=ticket.topic_id,
                        audio=file_id
                    )
                else:  # document
                    await self.bot.send_document(
                        chat_id=self.support_chat_id,
                        message_thread_id=ticket.topic_id,
                        document=file_id
                    )
                
                sent += 1
                
            except TelegramAPIError as e:
                logger.error(f"Failed to send attachment to topic {ticket.topic_id}: {e}")
        
        return sent
    
    async def send_operator_reply_to_client(
        self,
        client_chat_id: int,
        message: Message
    ) -> bool:
        """
        Send operator's reply to client.
        
        Args:
            client_chat_id: Client's Telegram chat ID
            message: Operator's message
        
        Returns:
            True if sent successfully
        """
        try:
            # Handle different message types
            if message.text:
                from app.config.texts import Texts
                await self.bot.send_message(
                    chat_id=client_chat_id,
                    text=Texts.operator_reply(message.text)
                )
            elif message.photo:
                await self.bot.send_photo(
                    chat_id=client_chat_id,
                    photo=message.photo[-1].file_id,
                    caption=message.caption
                )
            elif message.video:
                await self.bot.send_video(
                    chat_id=client_chat_id,
                    video=message.video.file_id,
                    caption=message.caption
                )
            elif message.document:
                await self.bot.send_document(
                    chat_id=client_chat_id,
                    document=message.document.file_id,
                    caption=message.caption
                )
            elif message.voice:
                await self.bot.send_voice(
                    chat_id=client_chat_id,
                    voice=message.voice.file_id
                )
            else:
                logger.warning(f"Unsupported message type from operator")
                return False
            
            return True
            
        except TelegramAPIError as e:
            logger.error(f"Failed to send reply to client {client_chat_id}: {e}")
            return False
    
    async def update_ticket_card(
        self,
        ticket: Ticket,
        message_id: int,
        new_status: str,
        operator_username: Optional[str] = None
    ) -> bool:
        """
        Update ticket card with new status.
        
        Args:
            ticket: Ticket object
            message_id: Card message ID
            new_status: New status text
            operator_username: Assigned operator username
        
        Returns:
            True if updated successfully
        """
        if not ticket.topic_id:
            return False
        
        status_text = f"📊 <b>Статус обновлён:</b> {new_status}"
        if operator_username:
            status_text += f"\n👤 <b>Ответственный:</b> @{operator_username}"
        
        try:
            await self.bot.send_message(
                chat_id=self.support_chat_id,
                message_thread_id=ticket.topic_id,
                text=status_text
            )
            
            # Update keyboard based on status
            if new_status == "in_progress":
                keyboard = get_ticket_inprogress_keyboard(ticket.id)
            else:
                keyboard = None
            
            # Try to edit original card keyboard
            try:
                await self.bot.edit_message_reply_markup(
                    chat_id=self.support_chat_id,
                    message_id=message_id,
                    reply_markup=keyboard
                )
            except TelegramAPIError:
                pass  # Message might be too old to edit
            
            return True
            
        except TelegramAPIError as e:
            logger.error(f"Failed to update ticket card: {e}")
            return False
    
    async def send_feedback_to_topic(
        self,
        ticket: Ticket,
        csat: str,
        comment: Optional[str] = None
    ) -> bool:
        """
        Send CSAT feedback to ticket's topic.
        
        Args:
            ticket: Ticket object
            csat: positive or negative
            comment: Optional feedback comment
        
        Returns:
            True if sent successfully
        """
        if not ticket.topic_id:
            return False
        
        emoji = "👍" if csat == "positive" else "👎"
        text = f"📊 <b>Feedback по тикету #{ticket.number}:</b>\n{emoji} {csat}"
        
        if comment:
            text += f"\n\n💬 <b>Комментарий:</b>\n{comment}"
        
        try:
            await self.bot.send_message(
                chat_id=self.support_chat_id,
                message_thread_id=ticket.topic_id,
                text=text
            )
            return True
            
        except TelegramAPIError as e:
            logger.error(f"Failed to send feedback to topic: {e}")
            return False
    
    async def notify_client_ticket_status(
        self,
        client_chat_id: int,
        ticket_number: int,
        status: str
    ) -> bool:
        """
        Notify client about ticket status change.
        
        Args:
            client_chat_id: Client's chat ID
            ticket_number: Ticket number
            status: New status (in_progress, closed)
        
        Returns:
            True if notified successfully
        """
        from app.config.texts import Texts
        from app.bot.keyboards.csat import get_csat_keyboard
        from app.bot.keyboards.ticket import get_after_ticket_menu
        
        try:
            if status == "in_progress":
                await self.bot.send_message(
                    chat_id=client_chat_id,
                    text=Texts.ticket_in_progress(ticket_number),
                    reply_markup=get_after_ticket_menu(),
                    parse_mode="HTML"
                )
            elif status == "on_hold":
                await self.bot.send_message(
                    chat_id=client_chat_id,
                    text=Texts.ticket_paused(ticket_number),
                    reply_markup=get_after_ticket_menu(),
                    parse_mode="HTML"
                )
            elif status == "resumed":
                await self.bot.send_message(
                    chat_id=client_chat_id,
                    text=Texts.ticket_resumed(ticket_number),
                    reply_markup=get_after_ticket_menu(),
                    parse_mode="HTML"
                )
            elif status == "closed":
                # Get ticket for CSAT keyboard
                ticket = await ops.get_ticket_by_number(self.session, ticket_number)
                if ticket:
                    await self.bot.send_message(
                        chat_id=client_chat_id,
                        text=Texts.ticket_closed(ticket_number),
                        parse_mode="HTML"
                    )
                    await self.bot.send_message(
                        chat_id=client_chat_id,
                        text=Texts.CSAT_ASK,
                        reply_markup=get_csat_keyboard(ticket.id)
                    )
            
            return True
            
        except TelegramAPIError as e:
            logger.error(f"Failed to notify client {client_chat_id}: {e}")
            return False
    
    async def notify_client_ticket_paused(
        self,
        client_chat_id: int,
        ticket_number: int,
        reason: str
    ) -> bool:
        """
        Notify client that ticket was paused.
        
        Args:
            client_chat_id: Client's chat ID
            ticket_number: Ticket number
            reason: Pause reason
        
        Returns:
            True if notified successfully
        """
        from app.config.texts import Texts
        from app.bot.keyboards.ticket import get_after_ticket_menu
        
        try:
            await self.bot.send_message(
                chat_id=client_chat_id,
                text=Texts.ticket_paused_with_reason(ticket_number, reason),
                reply_markup=get_after_ticket_menu(),
                parse_mode="HTML"
            )
            return True
            
        except TelegramAPIError as e:
            logger.error(f"Failed to notify client {client_chat_id} about pause: {e}")
            return False
    
    async def notify_client_ticket_cancelled(
        self,
        client_chat_id: int,
        ticket_number: int,
        reason: str
    ) -> bool:
        """
        Notify client that ticket was cancelled.
        
        Args:
            client_chat_id: Client's chat ID
            ticket_number: Ticket number
            reason: Cancellation reason
        
        Returns:
            True if notified successfully
        """
        from app.config.texts import Texts
        from app.bot.keyboards.ticket import get_after_ticket_menu
        
        try:
            await self.bot.send_message(
                chat_id=client_chat_id,
                text=Texts.ticket_cancelled(ticket_number, reason),
                reply_markup=get_after_ticket_menu(),
                parse_mode="HTML"
            )
            return True
            
        except TelegramAPIError as e:
            logger.error(f"Failed to notify client {client_chat_id} about cancellation: {e}")
            return False
    
    async def send_request_details(
        self,
        client_chat_id: int
    ) -> bool:
        """
        Send 'request details' template to client.
        
        Args:
            client_chat_id: Client's chat ID
        
        Returns:
            True if sent successfully
        """
        from app.config.texts import Texts
        
        try:
            await self.bot.send_message(
                chat_id=client_chat_id,
                text=Texts.REQUEST_DETAILS
            )
            return True
            
        except TelegramAPIError as e:
            logger.error(f"Failed to send request details to {client_chat_id}: {e}")
            return False
