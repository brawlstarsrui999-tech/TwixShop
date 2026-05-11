"""
Middleware для передачи config в хендлеры.
"""

from typing import Any, Callable, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject
from bot.config import Config


class ConfigMiddleware(BaseMiddleware):
    """Добавляет объект Config в данные хендлеров."""

    def __init__(self, config: Config):
        self.config = config

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        data["config"] = self.config
        return await handler(event, data)
