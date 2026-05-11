"""
Обработчики магазина: каталог, просмотр товаров, покупка, история заказов.
"""

import logging
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from bot import database as db
from bot.states import BuyStates
from bot.keyboards import (
    tags_kb,
    products_kb,
    product_detail_kb,
    product_detail_admin_kb,
    confirm_purchase_kb,
    cancel_kb,
    back_to_main_kb,
)
from bot.config import Config
from bot.rcon_client import grant_luckperms_group

logger = logging.getLogger(__name__)
router = Router()


# ─── КАТАЛОГ ──────────────────────────────────────────────────────────────────

@router.callback_query(F.data == "catalog")
async def cb_catalog(callback: CallbackQuery, config: Config):
    tags = await db.get_all_tags(config.db_path)
    products = await db.get_all_products(config.db_path, active_only=True)

    if not products:
        await callback.message.edit_text(
            "😔 В магазине пока нет доступных товаров.\nЗагляните позже!",
            reply_markup=back_to_main_kb(),
        )
        await callback.answer()
        return

    if tags:
        text = "🏷 <b>Выберите категорию:</b>"
        kb = tags_kb(tags)
    else:
        text = "🛒 <b>Все доступные товары:</b>"
        kb = products_kb(products)

    await callback.message.edit_text(text, reply_markup=kb, parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data.startswith("tag:"))
async def cb_tag(callback: CallbackQuery, config: Config):
    tag = callback.data.split(":", 1)[1]

    if tag == "__all__":
        products = await db.get_all_products(config.db_path, active_only=True)
        title = "📦 <b>Все товары:</b>"
    else:
        products = await db.get_products_by_tag(config.db_path, tag)
        title = f"🏷 <b>Категория: {tag}</b>"

    if not products:
        await callback.message.edit_text(
            "😔 В этой категории нет товаров.",
            reply_markup=back_to_main_kb(),
        )
        await callback.answer()
        return

    await callback.message.edit_text(
        title, reply_markup=products_kb(products, tag), parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data.startswith("product:"))
async def cb_product(callback: CallbackQuery, config: Config):
    product_id = int(callback.data.split(":")[1])
    product = await db.get_product_by_id(config.db_path, product_id)

    if not product:
        await callback.answer("❌ Товар не найден.", show_alert=True)
        return

    price_str = f"{product['price']:.0f}" if product['price'] == int(product['price']) else f"{product['price']:.2f}"

    text = (
        f"<b>{product['name']}</b>\n\n"
        f"📄 {product['description']}\n\n"
        f"🏷 Категория: <b>{product['tag'] or 'Без категории'}</b>\n"
        f"🔑 LP группа: <code>{product['lp_group']}</code>\n"
        f"💰 Цена: <b>{price_str}₽</b>"
    )

    is_admin = callback.from_user.id in config.bot.admin_ids
    kb = product_detail_admin_kb(product_id) if is_admin else product_detail_kb(product_id)

    if product.get("photo_id"):
        try:
            await callback.message.delete()
            await callback.message.answer_photo(
                photo=product["photo_id"],
                caption=text,
                reply_markup=kb,
                parse_mode="HTML",
            )
        except Exception:
            await callback.message.edit_text(text, reply_markup=kb, parse_mode="HTML")
    else:
        await callback.message.edit_text(text, reply_markup=kb, parse_mode="HTML")

    await callback.answer()


# ─── ПОКУПКА ──────────────────────────────────────────────────────────────────

@router.callback_query(F.data.startswith("buy:"))
async def cb_buy(callback: CallbackQuery, state: FSMContext, config: Config):
    product_id = int(callback.data.split(":")[1])
    product = await db.get_product_by_id(config.db_path, product_id)

    if not product or not product["is_active"]:
        await callback.answer("❌ Этот товар недоступен.", show_alert=True)
        return

    await state.set_state(BuyStates.waiting_nickname)
    await state.update_data(product_id=product_id)

    price_str = f"{product['price']:.0f}" if product['price'] == int(product['price']) else f"{product['price']:.2f}"

    text = (
        f"💳 <b>Покупка: {product['name']}</b>\n"
        f"💰 Цена: <b>{price_str}₽</b>\n\n"
        f"✏️ Введите ваш <b>ник в Minecraft</b> (точно, с учётом регистра):"
    )

    try:
        await callback.message.edit_text(text, reply_markup=cancel_kb(), parse_mode="HTML")
    except Exception:
        await callback.message.answer(text, reply_markup=cancel_kb(), parse_mode="HTML")

    await callback.answer()


@router.message(BuyStates.waiting_nickname)
async def process_nickname(message: Message, state: FSMContext, config: Config):
    nickname = message.text.strip()

    # Базовая валидация ника Minecraft (3-16 символов, буквы/цифры/подчёркивание)
    import re
    if not re.match(r'^[a-zA-Z0-9_]{3,16}$', nickname):
        await message.answer(
            "❌ Некорректный ник!\n"
            "Ник Minecraft должен содержать от 3 до 16 символов\n"
            "(буквы латиницы, цифры, подчёркивание).\n\n"
            "Попробуйте ещё раз:",
            reply_markup=cancel_kb(),
        )
        return

    data = await state.get_data()
    product_id = data.get("product_id")
    product = await db.get_product_by_id(config.db_path, product_id)

    if not product:
        await state.clear()
        await message.answer("❌ Товар не найден.", reply_markup=back_to_main_kb())
        return

    await state.update_data(nickname=nickname)
    await state.set_state(BuyStates.waiting_confirm)

    price_str = f"{product['price']:.0f}" if product['price'] == int(product['price']) else f"{product['price']:.2f}"

    text = (
        f"🧾 <b>Подтверждение заказа</b>\n\n"
        f"📦 Товар: <b>{product['name']}</b>\n"
        f"👤 Ник: <code>{nickname}</code>\n"
        f"💰 Сумма: <b>{price_str}₽</b>\n"
        f"🔑 Группа: <code>{product['lp_group']}</code>\n\n"
        f"⚠️ Убедитесь, что ник введён верно!\n"
        f"После подтверждения привилегия будет выдана автоматически."
    )

    await message.answer(
        text,
        reply_markup=confirm_purchase_kb(product_id),
        parse_mode="HTML",
    )


@router.callback_query(F.data.startswith("confirm_buy:"), BuyStates.waiting_confirm)
async def cb_confirm_buy(callback: CallbackQuery, state: FSMContext, config: Config):
    product_id = int(callback.data.split(":")[1])
    data = await state.get_data()
    nickname = data.get("nickname")

    if not nickname:
        await state.clear()
        await callback.answer("❌ Ошибка состояния. Начните заново.", show_alert=True)
        return

    product = await db.get_product_by_id(config.db_path, product_id)
    if not product or not product["is_active"]:
        await state.clear()
        await callback.answer("❌ Товар недоступен.", show_alert=True)
        return

    await state.clear()

    # Создаём заказ в БД
    username = callback.from_user.username or callback.from_user.full_name or "unknown"
    order_id = await db.create_order(
        config.db_path,
        user_id=callback.from_user.id,
        username=username,
        product_id=product_id,
        product_name=product["name"],
        mc_nickname=nickname,
        price=product["price"],
        lp_group=product["lp_group"],
    )

    # Сообщение о обработке
    processing_msg = await callback.message.edit_text(
        f"⏳ <b>Обрабатываем заказ #{order_id}...</b>\n"
        f"Выдаём привилегию <code>{product['lp_group']}</code> игроку <code>{nickname}</code>",
        parse_mode="HTML",
    )

    # Выдаём привилегию через RCON
    success, rcon_response = await grant_luckperms_group(
        host=config.rcon.host,
        port=config.rcon.port,
        password=config.rcon.password,
        mc_nickname=nickname,
        lp_group=product["lp_group"],
    )

    price_str = f"{product['price']:.0f}" if product['price'] == int(product['price']) else f"{product['price']:.2f}"

    if success:
        await db.complete_order(config.db_path, order_id)

        text = (
            f"✅ <b>Заказ #{order_id} выполнен!</b>\n\n"
            f"📦 Товар: <b>{product['name']}</b>\n"
            f"👤 Ник: <code>{nickname}</code>\n"
            f"💰 Оплачено: <b>{price_str}₽</b>\n"
            f"🔑 Группа выдана: <code>{product['lp_group']}</code>\n\n"
            f"🎮 Привилегия уже активна на сервере!\n"
            f"Зайдите в игру и наслаждайтесь новыми возможностями 🎉"
        )

        # Уведомляем администраторов
        for admin_id in config.bot.admin_ids:
            try:
                await callback.bot.send_message(
                    admin_id,
                    f"🔔 <b>Новый заказ #{order_id}</b>\n"
                    f"👤 Покупатель: @{username} (ID: {callback.from_user.id})\n"
                    f"📦 Товар: {product['name']}\n"
                    f"🎮 Ник: <code>{nickname}</code>\n"
                    f"🔑 LP группа: <code>{product['lp_group']}</code>\n"
                    f"💰 Сумма: {price_str}₽\n"
                    f"✅ RCON ответ: {rcon_response or 'OK'}",
                    parse_mode="HTML",
                )
            except Exception as e:
                logger.warning(f"Не удалось уведомить админа {admin_id}: {e}")
    else:
        await db.fail_order(config.db_path, order_id)

        text = (
            f"⚠️ <b>Заказ #{order_id} создан, но произошла ошибка выдачи!</b>\n\n"
            f"📦 Товар: <b>{product['name']}</b>\n"
            f"👤 Ник: <code>{nickname}</code>\n"
            f"🔑 Группа: <code>{product['lp_group']}</code>\n\n"
            f"❌ <i>Не удалось подключиться к серверу или выдать привилегию.</i>\n"
            f"Администраторы уже уведомлены и вскоре решат проблему.\n"
            f"Номер вашего заказа: <b>#{order_id}</b>"
        )

        # Уведомляем администраторов об ошибке
        for admin_id in config.bot.admin_ids:
            try:
                await callback.bot.send_message(
                    admin_id,
                    f"🚨 <b>ОШИБКА выдачи привилегии!</b>\n"
                    f"Заказ #{order_id}\n"
                    f"👤 @{username} (ID: {callback.from_user.id})\n"
                    f"📦 {product['name']}\n"
                    f"🎮 Ник: <code>{nickname}</code>\n"
                    f"🔑 LP: <code>{product['lp_group']}</code>\n"
                    f"❌ Ошибка RCON: {rcon_response}\n\n"
                    f"Выдайте вручную: <code>lp user {nickname} parent add {product['lp_group']}</code>",
                    parse_mode="HTML",
                )
            except Exception as e:
                logger.warning(f"Не удалось уведомить админа {admin_id}: {e}")

    await callback.message.edit_text(text, reply_markup=back_to_main_kb(), parse_mode="HTML")
    await callback.answer()


# ─── МОИ ЗАКАЗЫ ───────────────────────────────────────────────────────────────

async def show_my_orders(event, is_message: bool = False):
    """Универсальная функция показа заказов пользователя."""
    pass  # Реализована ниже через отдельные обработчики


@router.callback_query(F.data == "my_orders")
async def cb_my_orders(callback: CallbackQuery, config: Config):
    orders = await db.get_user_orders(config.db_path, callback.from_user.id)

    if not orders:
        await callback.message.edit_text(
            "📦 <b>Ваши заказы</b>\n\nУ вас пока нет заказов.\nПосетите каталог и купите первую привилегию!",
            reply_markup=back_to_main_kb(),
            parse_mode="HTML",
        )
        await callback.answer()
        return

    status_emoji = {"completed": "✅", "pending": "⏳", "failed": "❌"}
    lines = ["📦 <b>Ваши последние заказы:</b>\n"]

    for o in orders[:10]:
        emoji = status_emoji.get(o["status"], "❓")
        price_str = f"{o['price']:.0f}" if o['price'] == int(o['price']) else f"{o['price']:.2f}"
        lines.append(
            f"{emoji} <b>#{o['id']}</b> {o['product_name']}\n"
            f"   👤 Ник: <code>{o['mc_nickname']}</code> | 💰 {price_str}₽\n"
            f"   📅 {o['created_at'][:16]}"
        )

    await callback.message.edit_text(
        "\n".join(lines),
        reply_markup=back_to_main_kb(),
        parse_mode="HTML",
    )
    await callback.answer()


@router.message(Command("orders"))
async def cmd_my_orders(message: Message, config: Config):
    orders = await db.get_user_orders(config.db_path, message.from_user.id)

    if not orders:
        await message.answer(
            "📦 У вас пока нет заказов.",
            reply_markup=back_to_main_kb(),
        )
        return

    status_emoji = {"completed": "✅", "pending": "⏳", "failed": "❌"}
    lines = ["📦 <b>Ваши последние заказы:</b>\n"]

    for o in orders[:10]:
        emoji = status_emoji.get(o["status"], "❓")
        price_str = f"{o['price']:.0f}" if o['price'] == int(o['price']) else f"{o['price']:.2f}"
        lines.append(
            f"{emoji} <b>#{o['id']}</b> {o['product_name']}\n"
            f"   👤 <code>{o['mc_nickname']}</code> | 💰 {price_str}₽\n"
            f"   📅 {o['created_at'][:16]}"
        )

    await message.answer(
        "\n".join(lines),
        reply_markup=back_to_main_kb(),
        parse_mode="HTML",
    )
