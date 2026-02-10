"""
Timezone and working hours utilities.
"""

from datetime import datetime
from typing import Optional

import pytz

from app.config.settings import settings


def get_current_time(timezone: Optional[str] = None) -> datetime:
    """
    Get current time in specified timezone.
    
    Args:
        timezone: Timezone name (e.g., 'Europe/Madrid'). 
                  Uses settings.timezone if not provided.
    
    Returns:
        Current datetime in the specified timezone
    """
    tz_name = timezone or settings.timezone
    tz = pytz.timezone(tz_name)
    return datetime.now(tz)


def is_working_hours(
    dt: Optional[datetime] = None,
    timezone: Optional[str] = None
) -> bool:
    """
    Check if given time is within working hours.
    
    Args:
        dt: Datetime to check. Uses current time if not provided.
        timezone: Timezone name. Uses settings.timezone if not provided.
    
    Returns:
        True if within working hours, False otherwise
    
    Working hours are defined in settings:
        - work_hours_start: Start hour (default 10)
        - work_hours_end: End hour (default 19)
        - work_days: List of weekdays (1=Monday, 7=Sunday)
    """
    if dt is None:
        dt = get_current_time(timezone)
    elif dt.tzinfo is None:
        # Localize naive datetime
        tz_name = timezone or settings.timezone
        tz = pytz.timezone(tz_name)
        dt = tz.localize(dt)
    
    # Check day of week (1=Monday, 7=Sunday in our config)
    # Python's weekday() returns 0=Monday, 6=Sunday
    weekday = dt.weekday() + 1  # Convert to 1-based
    
    if weekday not in settings.work_days:
        return False
    
    # Check hour
    hour = dt.hour
    
    return settings.work_hours_start <= hour < settings.work_hours_end


def get_sla_message(is_urgent: bool = False) -> str:
    """
    Get SLA message based on current time and urgency.
    
    Args:
        is_urgent: Whether the ticket is urgent
    
    Returns:
        Appropriate SLA message
    """
    if is_working_hours():
        if is_urgent:
            return "Стараемся ответить за 30–60 минут."
        return "Обычно отвечаем за 2–4 часа."
    else:
        return "Сейчас нерабочее время. Ответим в следующий рабочий день."


def format_working_hours() -> str:
    """
    Format working hours for display.
    
    Returns:
        Formatted string like "Пн–Пт 10:00–19:00 (Europe/Madrid)"
    """
    days_map = {
        1: "Пн", 2: "Вт", 3: "Ср", 4: "Чт", 
        5: "Пт", 6: "Сб", 7: "Вс"
    }
    
    work_days = sorted(settings.work_days)
    
    # Format days range
    if work_days == [1, 2, 3, 4, 5]:
        days_str = "Пн–Пт"
    elif work_days == [1, 2, 3, 4, 5, 6]:
        days_str = "Пн–Сб"
    elif work_days == [1, 2, 3, 4, 5, 6, 7]:
        days_str = "Пн–Вс"
    else:
        days_str = ", ".join(days_map[d] for d in work_days)
    
    start = f"{settings.work_hours_start:02d}:00"
    end = f"{settings.work_hours_end:02d}:00"
    
    return f"{days_str} {start}–{end} ({settings.timezone})"
