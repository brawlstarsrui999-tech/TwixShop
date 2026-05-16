"""
Точка входа в бот.
Запуск: python main.py
"""

import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

from bot.config import load_config
from bot.database import init_db
from bot.middlewares import ConfigMiddleware
from bot.handlers import common, shop, admin

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)


async def main():
    config = load_config()

    # Инициализация БД
    logger.info(f"Инициализация БД: {config.db_path}")
    await init_db(config.db_path)

    # Создание бота и диспетчера
    bot = Bot(
        token=config.bot.token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)

    # Middleware
    dp.message.middleware(ConfigMiddleware(config))
    dp.callback_query.middleware(ConfigMiddleware(config))

    # Роутеры (порядок важен: admin до shop из-за фильтров)
    dp.include_router(common.router)
    dp.include_router(admin.router)
    dp.include_router(shop.router)

    # Запуск
    logger.info("Бот запускается...")
    logger.info(f"Администраторы: {config.bot.admin_ids}")
    logger.info(f"RCON: {config.rcon.host}:{config.rcon.port}")

    try:
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    finally:
        await bot.session.close()
        logger.info("Бот остановлен.")


if __name__ == "__main__":
    asyncio.run(main())
