"""Ticket categories configuration."""

from dataclasses import dataclass
from typing import List, Optional


@dataclass(frozen=True)
class Category:
    """Ticket category definition."""
    
    id: str
    label: str
    emoji: str


# Ticket categories
CATEGORIES: List[Category] = [
    Category(id="report", label="Проблема с отчетом", emoji="📊"),
    Category(id="rating", label="Некорректная оценка", emoji="⭐"),
    Category(id="widget", label="Виджет и интеграции", emoji="🔗"),
    Category(id="access", label="Доступы и роли", emoji="🔐"),
    Category(id="howto", label="Настройка и использование отчета", emoji="💡"),
    Category(id="billing", label="Оплата и документы", emoji="💳"),
    Category(id="feature", label="Запрос на улучшение", emoji="✨"),
    Category(id="other", label="Другое", emoji="📝"),
]

# SLA times by category
CATEGORY_SLA: dict = {
    "report": "6–12 часов",
    "rating": "4–8 часов",
    "widget": "1–2 рабочих дня",
    "access": "1–3 часа",
    "howto": "1–3 рабочих дня",
    "billing": "1–2 рабочих дня",
    "feature": None,  # Special message
    "other": None,    # Special message
}


def get_sla_time(category_id: str) -> Optional[str]:
    """Get SLA time for category."""
    return CATEGORY_SLA.get(category_id)


def get_category_by_id(category_id: str) -> Optional[Category]:
    """Get category by ID."""
    for cat in CATEGORIES:
        if cat.id == category_id:
            return cat
    return None


def get_category_label(category_id: str) -> str:
    """Get category label with emoji."""
    cat = get_category_by_id(category_id)
    if cat:
        return f"{cat.emoji} {cat.label}"
    return category_id
