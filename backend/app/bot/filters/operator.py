"""
Operator-related filters.
"""

from aiogram.filters import Filter
from aiogram.types import Message, CallbackQuery
from typing import Union

from app.config.settings import settings


class IsOperator(Filter):
    """
    Filter that checks if user is an operator.
    
    Usage:
        @router.message(IsOperator())
        async def handler(message: Message):
            ...
    """
    
    async def __call__(self, event: Union[Message, CallbackQuery]) -> bool:
        """Check if user is in operators list."""
        user_id = event.from_user.id if event.from_user else None
        return user_id in settings.operators


class IsSupportGroup(Filter):
    """
    Filter that checks if message is from support group.
    
    Usage:
        @router.message(IsSupportGroup())
        async def handler(message: Message):
            ...
    """
    
    async def __call__(self, event: Union[Message, CallbackQuery]) -> bool:
        """Check if event is from support group."""
        if isinstance(event, Message):
            chat_id = event.chat.id
        elif isinstance(event, CallbackQuery) and event.message:
            chat_id = event.message.chat.id
        else:
            return False
        
        return chat_id == settings.support_chat_id
