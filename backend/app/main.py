"""
Telegram Support Bot — Entry Point.

Run with: python -m app.main
"""

import asyncio
import logging
import sys

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from app.bot.handlers import (
    client_message_router,
    common_router,
    csat_router,
    operator_commands_router,
    operator_router,
    start_router,
    ticket_router,
)
from app.bot.middlewares.database import DatabaseMiddleware
from app.config.settings import settings
from app.database.connection import close_db, init_db

# Configure logging
logging.basicConfig(
    level=settings.log_level.upper(),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    stream=sys.stdout
)
logger = logging.getLogger(__name__)


async def on_startup(bot: Bot) -> None:
    """Actions to perform on bot startup."""
    logger.info("Initializing database...")
    await init_db()
    
    # Log bot info
    bot_info = await bot.get_me()
    logger.info(f"Bot started: @{bot_info.username} (id: {bot_info.id})")


async def on_shutdown(bot: Bot) -> None:
    """Actions to perform on bot shutdown."""
    logger.info("Shutting down...")
    await close_db()
    logger.info("Shutdown complete")


async def main() -> None:
    """Initialize and start the bot."""
    logger.info("=" * 50)
    logger.info("Starting Telegram Support Bot")
    logger.info("=" * 50)
    
    # Log configuration
    logger.info(f"Bot token: {settings.bot_token[:10]}...{settings.bot_token[-5:]}")
    logger.info(f"Support chat ID: {settings.support_chat_id}")
    logger.info(f"Operators: {settings.operators}")
    logger.info(f"Timezone: {settings.timezone}")
    logger.info(f"Working hours: {settings.work_hours_start}:00 - {settings.work_hours_end}:00")
    logger.info(f"Database: {settings.db_path}")
    
    # Create bot instance
    bot = Bot(
        token=settings.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    
    # Create dispatcher
    dp = Dispatcher()
    
    # Register startup/shutdown handlers
    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)
    
    # Setup middlewares
    dp.message.middleware(DatabaseMiddleware())
    dp.callback_query.middleware(DatabaseMiddleware())
    
    # Include routers (order matters!)
    # 1. Start handler (processes /start with deep links first)
    dp.include_router(start_router)
    
    # 2. Operator commands (private chat)
    dp.include_router(operator_commands_router)
    
    # 3. Ticket creation flow
    dp.include_router(ticket_router)
    
    # 4. Common commands (/help, /project)
    dp.include_router(common_router)
    
    # 5. CSAT feedback
    dp.include_router(csat_router)
    
    # 6. Client messages (catch-all for private messages)
    dp.include_router(client_message_router)
    
    # 7. Operator handlers (for support group)
    dp.include_router(operator_router)
    
    # Start polling
    logger.info("Starting polling...")
    try:
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    finally:
        await bot.session.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.exception(f"Fatal error: {e}")
        sys.exit(1)
