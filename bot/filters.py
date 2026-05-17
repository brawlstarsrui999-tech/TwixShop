"""
Кастомные фильтры aiogram.
"""

from aiogram.filters import BaseFilter
from aiogram.types import Message, CallbackQuery
from bot.config import Config


class AdminFilter(BaseFilter):
    """Пропускает только сообщения/коллбэки от администраторов."""

    async def __call__(self, event, config: Config) -> bool:
        if isinstance(event, Message):
            return event.from_user.id in config.bot.admin_ids
        elif isinstance(event, CallbackQuery):
            return event.from_user.id in config.bot.admin_ids
        return False
