"""
Tests for service layer functions.
"""

import pytest
from datetime import datetime
import pytz

from app.services.timezone import (
    get_current_time,
    is_working_hours,
    get_sla_message,
    format_working_hours,
)


class TestTimezoneUtils:
    """Tests for timezone and working hours utilities."""
    
    def test_get_current_time_default_timezone(self):
        """Test getting current time with default timezone."""
        now = get_current_time()
        assert now is not None
        assert now.tzinfo is not None
    
    def test_get_current_time_custom_timezone(self):
        """Test getting current time with custom timezone."""
        now = get_current_time("UTC")
        assert now is not None
        assert "UTC" in str(now.tzinfo)
    
    def test_is_working_hours_weekday_within_hours(self):
        """Test working hours check on weekday during work time."""
        # Create a Monday at 14:00 (within 10-19)
        tz = pytz.timezone("Europe/Madrid")
        dt = datetime(2025, 2, 3, 14, 0)  # Monday
        dt = tz.localize(dt)
        
        result = is_working_hours(dt)
        assert result is True
    
    def test_is_working_hours_weekday_before_hours(self):
        """Test working hours check before work time."""
        tz = pytz.timezone("Europe/Madrid")
        dt = datetime(2025, 2, 3, 8, 0)  # Monday 8:00
        dt = tz.localize(dt)
        
        result = is_working_hours(dt)
        assert result is False
    
    def test_is_working_hours_weekday_after_hours(self):
        """Test working hours check after work time."""
        tz = pytz.timezone("Europe/Madrid")
        dt = datetime(2025, 2, 3, 20, 0)  # Monday 20:00
        dt = tz.localize(dt)
        
        result = is_working_hours(dt)
        assert result is False
    
    def test_is_working_hours_weekend(self):
        """Test working hours check on weekend."""
        tz = pytz.timezone("Europe/Madrid")
        dt = datetime(2025, 2, 8, 14, 0)  # Saturday
        dt = tz.localize(dt)
        
        result = is_working_hours(dt)
        assert result is False
    
    def test_get_sla_message_urgent(self):
        """Test SLA message for urgent ticket."""
        # This will use current time, just test the message format
        message = get_sla_message(is_urgent=True)
        assert isinstance(message, str)
        assert len(message) > 0
    
    def test_get_sla_message_normal(self):
        """Test SLA message for normal ticket."""
        message = get_sla_message(is_urgent=False)
        assert isinstance(message, str)
        assert len(message) > 0
    
    def test_format_working_hours(self):
        """Test working hours formatting."""
        formatted = format_working_hours()
        
        assert "10:00" in formatted
        assert "19:00" in formatted
        assert "Europe/Madrid" in formatted


class TestTexts:
    """Tests for text templates."""
    
    def test_ticket_created_normal(self):
        """Test normal ticket created message."""
        from app.config.texts import Texts
        
        message = Texts.ticket_created(123)
        assert "#123" in message
        assert "🚨" not in message
    
    def test_ticket_created_urgent(self):
        """Test urgent ticket created message."""
        from app.config.texts import Texts
        
        message = Texts.ticket_created(123, urgent=True)
        assert "#123" in message
        assert "🚨" in message
    
    def test_ticket_created_off_hours(self):
        """Test off-hours ticket created message."""
        from app.config.texts import Texts
        
        message = Texts.ticket_created(123, off_hours=True)
        assert "#123" in message
        assert "нерабочее время" in message
    
    def test_ticket_in_progress(self):
        """Test ticket in progress message."""
        from app.config.texts import Texts
        
        message = Texts.ticket_in_progress(123)
        assert "#123" in message
        assert "в работу" in message
    
    def test_ticket_closed(self):
        """Test ticket closed message."""
        from app.config.texts import Texts
        
        message = Texts.ticket_closed(123)
        assert "#123" in message
        assert "закрыто" in message
    
    def test_active_ticket_exists(self):
        """Test active ticket exists message."""
        from app.config.texts import Texts
        
        message = Texts.active_ticket_exists(456)
        assert "#456" in message
    
    def test_operator_reply(self):
        """Test operator reply formatting."""
        from app.config.texts import Texts
        
        message = Texts.operator_reply("Test reply message")
        assert "Test reply message" in message
        assert "Ответ поддержки" in message
    
    def test_code_accepted(self):
        """Test code accepted message."""
        from app.config.texts import Texts
        
        message = Texts.code_accepted("My Project")
        assert "My Project" in message
    
    def test_project_switched(self):
        """Test project switched message."""
        from app.config.texts import Texts
        
        message = Texts.project_switched("Another Project")
        assert "Another Project" in message


class TestCategories:
    """Tests for ticket categories."""
    
    def test_categories_exist(self):
        """Test that categories are defined."""
        from app.config.categories import CATEGORIES
        
        assert len(CATEGORIES) > 0
    
    def test_category_has_required_fields(self):
        """Test that categories have required fields."""
        from app.config.categories import CATEGORIES
        
        for cat in CATEGORIES:
            assert hasattr(cat, "id")
            assert hasattr(cat, "label")
            assert hasattr(cat, "emoji")
    
    def test_get_category_label(self):
        """Test getting category label by ID."""
        from app.config.categories import get_category_label, CATEGORIES
        
        # Test with first category
        cat_id = CATEGORIES[0].id
        expected_label = CATEGORIES[0].label
        expected_emoji = CATEGORIES[0].emoji
        
        label = get_category_label(cat_id)
        # get_category_label returns emoji + label
        assert expected_label in label
        assert expected_emoji in label
    
    def test_get_category_label_unknown(self):
        """Test getting label for unknown category."""
        from app.config.categories import get_category_label
        
        label = get_category_label("unknown_category")
        assert label == "unknown_category"  # Returns ID as fallback


class TestTicketSummary:
    """Tests for ticket summary formatting."""
    
    def test_ticket_summary_basic(self):
        """Test basic ticket summary formatting."""
        from app.config.texts import Texts
        
        summary = Texts.ticket_summary(
            category="🐛 Не работает / ошибка",
            description="Кнопка не работает",
            attachments_count=0
        )
        
        assert "Превью вашего обращения" in summary
        assert "🐛 Не работает / ошибка" in summary
        assert "Кнопка не работает" in summary
        assert "нет" in summary  # No attachments
        assert "Всё верно?" in summary
    
    def test_ticket_summary_with_attachments(self):
        """Test ticket summary with attachments."""
        from app.config.texts import Texts
        
        summary = Texts.ticket_summary(
            category="📋 Вопрос",
            description="Test description",
            attachments_count=3
        )
        
        assert "3 файл(ов)" in summary
    
    def test_ticket_summary_truncates_long_description(self):
        """Test that long descriptions are truncated."""
        from app.config.texts import Texts
        
        long_desc = "x" * 600
        summary = Texts.ticket_summary(
            category="📋 Вопрос",
            description=long_desc,
            attachments_count=0
        )
        
        # Should be truncated with ...
        assert "..." in summary
        # Should not contain full 600 chars
        assert "x" * 600 not in summary
