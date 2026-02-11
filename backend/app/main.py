"""
Telegram Support Bot — Entry Point.

Run with: python -m app.main
"""

import asyncio
import logging
import os
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
from app.database.connection import DatabaseSessionManager, close_db, init_db
from app.database import operations as ops
from app.health import run_healthcheck_server

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
    async with DatabaseSessionManager() as session:
        await ops.ensure_default_project(session)
    
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
    if not settings.operators:
        logger.warning(
            "OPERATORS is empty! Buttons 'Взять в работу' won't work. "
            "In Railway Variables set OPERATORS=your_telegram_id (e.g. OPERATORS=373126255)"
        )
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
    
    # Start HTTP healthcheck server if PORT is set (e.g. Railway)
    # Read PORT from env directly so healthcheck works even if Settings alias differs per platform
    health_server = None
    port_str = os.environ.get("PORT")
    if port_str and port_str.isdigit():
        health_server = await run_healthcheck_server(int(port_str))
    
    # Start polling
    logger.info("Starting polling...")
    try:
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    finally:
        if health_server is not None:
            health_server.close()
            await health_server.wait_closed()
        await bot.session.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.exception(f"Fatal error: {e}")
        sys.exit(1)
