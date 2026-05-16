"""
Общие обработчики: /start, /help, главное меню.
"""

import logging
from aiogram import Router, F
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from bot.keyboards import main_menu_kb, admin_main_menu_kb, back_to_main_kb
from bot.config import Config

logger = logging.getLogger(__name__)
router = Router()


def get_menu_kb(user_id: int, config: Config):
    if user_id in config.bot.admin_ids:
        return admin_main_menu_kb()
    return main_menu_kb()


WELCOME_TEXT = (
    "⛏ <b>Добро пожаловать в магазин привилегий!</b>\n\n"
    "Здесь вы можете купить привилегию для нашего Minecraft сервера.\n"
    "После покупки привилегия будет автоматически выдана вашему персонажу через LuckPerms.\n\n"
    "Выберите действие:"
)

HELP_TEXT = (
    "❓ <b>Помощь</b>\n\n"
    "<b>Как купить привилегию?</b>\n"
    "1. Нажмите <b>🛒 Каталог товаров</b>\n"
    "2. Выберите нужную привилегию\n"
    "3. Нажмите <b>💳 Купить</b>\n"
    "4. Введите ваш ник в Minecraft\n"
    "5. Подтвердите покупку\n"
    "6. Привилегия выдаётся мгновенно!\n\n"
    "<b>Команды:</b>\n"
    "/start — главное меню\n"
    "/help — эта справка\n"
    "/orders — мои заказы\n\n"
    "По вопросам обращайтесь к администраторам сервера."
)


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext, config: Config):
    await state.clear()
    await message.answer(
        WELCOME_TEXT,
        reply_markup=get_menu_kb(message.from_user.id, config),
        parse_mode="HTML",
    )


@router.message(Command("help"))
async def cmd_help(message: Message, config: Config):
    await message.answer(
        HELP_TEXT,
        reply_markup=get_menu_kb(message.from_user.id, config),
        parse_mode="HTML",
    )


@router.message(Command("orders"))
async def cmd_orders(message: Message):
    from aiogram.types import CallbackQuery as CQ
    # Переиспользуем логику через callback
    from bot.handlers.shop import show_my_orders
    await show_my_orders(message, is_message=True)


@router.callback_query(F.data == "main_menu")
async def cb_main_menu(callback: CallbackQuery, state: FSMContext, config: Config):
    await state.clear()
    await callback.message.edit_text(
        WELCOME_TEXT,
        reply_markup=get_menu_kb(callback.from_user.id, config),
        parse_mode="HTML",
    )
    await callback.answer()


@router.callback_query(F.data == "help")
async def cb_help(callback: CallbackQuery, config: Config):
    await callback.message.edit_text(
        HELP_TEXT,
        reply_markup=get_menu_kb(callback.from_user.id, config),
        parse_mode="HTML",
    )
    await callback.answer()
