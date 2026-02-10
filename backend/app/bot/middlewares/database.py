"""
Database session middleware.

Injects database session into handler data.
"""

from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject

from app.database.connection import get_session_factory


class DatabaseMiddleware(BaseMiddleware):
    """
    Middleware that provides database session to handlers.
    
    Usage in handler:
        async def handler(message: Message, session: AsyncSession):
            # use session
    """
    
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        """Inject database session into handler data."""
        factory = get_session_factory()
        
        async with factory() as session:
            data["session"] = session
            return await handler(event, data)
