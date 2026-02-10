"""
CSAT (Customer Satisfaction) handlers.

Handles:
- Positive/negative feedback buttons
- Negative feedback comments
- Detailed CSAT ratings (speed, quality, politeness)
"""

import logging

from aiogram import Bot, F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from app.bot.keyboards.ticket import get_after_ticket_menu
from app.bot.keyboards.csat import get_detailed_csat_keyboard, get_skip_detailed_csat_keyboard
from app.bot.states.ticket import FeedbackFlow
from app.config.texts import Texts
from app.database import operations as ops
from app.services.ticket import TicketService

logger = logging.getLogger(__name__)

router = Router(name="csat")


@router.callback_query(F.data.startswith("csat:positive:"))
async def callback_csat_positive(
    callback: CallbackQuery,
    session: AsyncSession,
    bot: Bot,
    state: FSMContext
) -> None:
    """Handle positive CSAT button - ask for detailed rating."""
    await callback.answer()
    
    ticket_id = int(callback.data.split(":")[2])
    
    # Save basic feedback first
    service = TicketService(bot, session)
    await service.save_feedback(ticket_id, "positive")
    
    # Ask for detailed feedback (optional)
    await state.update_data(
        feedback_ticket_id=ticket_id,
        feedback_speed=None,
        feedback_quality=None,
        feedback_politeness=None
    )
    await state.set_state(FeedbackFlow.rating_speed)
    
    await callback.message.edit_text(Texts.CSAT_THANKS_POSITIVE)
    
    # Ask detailed rating
    await callback.message.answer(
        Texts.CSAT_ASK_DETAILED + "\n\n" + Texts.CSAT_ASK_SPEED,
        reply_markup=get_detailed_csat_keyboard(ticket_id, "speed"),
        parse_mode="HTML"
    )
    await callback.message.answer(
        "Или пропустите детальную оценку:",
        reply_markup=get_skip_detailed_csat_keyboard(ticket_id)
    )
    
    logger.info(f"Positive feedback for ticket {ticket_id}, asking detailed")


@router.callback_query(F.data.startswith("csat:skip_detailed:"))
async def callback_skip_detailed_csat(
    callback: CallbackQuery,
    state: FSMContext
) -> None:
    """Skip detailed CSAT and show menu."""
    await callback.answer()
    await state.clear()
    
    await callback.message.edit_text("Спасибо! 🙏")
    await callback.message.answer(
        Texts.AFTER_TICKET_MENU,
        reply_markup=get_after_ticket_menu()
    )


@router.callback_query(F.data.startswith("csat_detail:speed:"))
async def callback_csat_detail_speed(
    callback: CallbackQuery,
    state: FSMContext
) -> None:
    """Handle speed rating."""
    await callback.answer()
    
    parts = callback.data.split(":")
    rating = int(parts[2])
    ticket_id = int(parts[3])
    
    await state.update_data(feedback_speed=rating)
    await state.set_state(FeedbackFlow.rating_quality)
    
    await callback.message.edit_text(
        f"⚡ Скорость: {'⭐' * rating}\n\n" + Texts.CSAT_ASK_QUALITY,
        reply_markup=get_detailed_csat_keyboard(ticket_id, "quality"),
        parse_mode="HTML"
    )


@router.callback_query(F.data.startswith("csat_detail:quality:"))
async def callback_csat_detail_quality(
    callback: CallbackQuery,
    state: FSMContext
) -> None:
    """Handle quality rating."""
    await callback.answer()
    
    parts = callback.data.split(":")
    rating = int(parts[2])
    ticket_id = int(parts[3])
    
    data = await state.get_data()
    speed_rating = data.get("feedback_speed", 0)
    
    await state.update_data(feedback_quality=rating)
    await state.set_state(FeedbackFlow.rating_politeness)
    
    await callback.message.edit_text(
        f"⚡ Скорость: {'⭐' * speed_rating}\n"
        f"✨ Качество: {'⭐' * rating}\n\n" + Texts.CSAT_ASK_POLITENESS,
        reply_markup=get_detailed_csat_keyboard(ticket_id, "politeness"),
        parse_mode="HTML"
    )


@router.callback_query(F.data.startswith("csat_detail:politeness:"))
async def callback_csat_detail_politeness(
    callback: CallbackQuery,
    state: FSMContext,
    session: AsyncSession
) -> None:
    """Handle politeness rating - final step."""
    await callback.answer()
    
    parts = callback.data.split(":")
    rating = int(parts[2])
    ticket_id = int(parts[3])
    
    data = await state.get_data()
    speed_rating = data.get("feedback_speed", 0)
    quality_rating = data.get("feedback_quality", 0)
    
    # Save detailed ratings to database
    feedback = await ops.get_feedback_by_ticket(session, ticket_id)
    if feedback:
        feedback.speed_rating = speed_rating
        feedback.quality_rating = quality_rating
        feedback.politeness_rating = rating
        await session.commit()
    
    await state.clear()
    
    # Show summary
    await callback.message.edit_text(
        f"📊 Ваша оценка:\n\n"
        f"⚡ Скорость: {'⭐' * speed_rating}\n"
        f"✨ Качество: {'⭐' * quality_rating}\n"
        f"💬 Вежливость: {'⭐' * rating}\n\n"
        + Texts.CSAT_DETAILED_THANKS
    )
    
    await callback.message.answer(
        Texts.AFTER_TICKET_MENU,
        reply_markup=get_after_ticket_menu()
    )
    
    logger.info(f"Detailed feedback for ticket {ticket_id}: speed={speed_rating}, quality={quality_rating}, politeness={rating}")


@router.callback_query(F.data.startswith("csat:negative:"))
async def callback_csat_negative(
    callback: CallbackQuery,
    state: FSMContext
) -> None:
    """Handle negative CSAT button - ask for comment."""
    await callback.answer()
    
    ticket_id = int(callback.data.split(":")[2])
    
    # Save ticket ID for comment
    await state.update_data(feedback_ticket_id=ticket_id)
    await state.set_state(FeedbackFlow.waiting_comment)
    
    await callback.message.edit_text(Texts.CSAT_ASK_COMMENT)


@router.message(FeedbackFlow.waiting_comment, F.text)
async def handle_feedback_comment(
    message: Message,
    state: FSMContext,
    session: AsyncSession,
    bot: Bot
) -> None:
    """Handle negative feedback comment."""
    data = await state.get_data()
    ticket_id = data.get("feedback_ticket_id")
    comment = message.text.strip()
    
    if not ticket_id:
        await message.answer(Texts.ERROR_GENERIC)
        await state.clear()
        return
    
    service = TicketService(bot, session)
    success = await service.save_feedback(ticket_id, "negative", comment)
    
    await state.clear()
    
    if success:
        await message.answer(Texts.CSAT_THANKS_NEGATIVE)
        # Show menu after feedback
        await message.answer(
            Texts.AFTER_TICKET_MENU,
            reply_markup=get_after_ticket_menu()
        )
        logger.info(f"Negative feedback with comment for ticket {ticket_id}")
    else:
        await message.answer(Texts.ERROR_GENERIC)
