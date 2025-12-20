# backend/app/services/__init__.py
# Экспортируем сервисы для удобного импорта
from .style_service import style_service, StyleService

__all__ = ["style_service", "StyleService"]
