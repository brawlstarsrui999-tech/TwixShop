"""
Административные обработчики:
- Добавление товаров (FSM)
- Редактирование товаров
- Удаление товаров
- Просмотр всех заказов
"""

import logging
import re
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from bot import database as db
from bot.states import AddProductStates, EditProductStates
from bot.keyboards import (
    admin_product_list_kb,
    admin_edit_product_kb,
    admin_confirm_delete_kb,
    admin_orders_kb,
    back_to_main_kb,
    cancel_kb,
)
from bot.config import Config
from bot.filters import AdminFilter

logger = logging.getLogger(__name__)
router = Router()
router.message.filter(AdminFilter())
router.callback_query.filter(AdminFilter())


# ─── СПИСОК ТОВАРОВ ───────────────────────────────────────────────────────────

@router.callback_query(F.data == "admin_list_products")
async def cb_admin_list(callback: CallbackQuery, config: Config):
    products = await db.get_all_products(config.db_path, active_only=False)

    if not products:
        try:
            await callback.message.edit_text(
                "📋 Товары отсутствуют.\nДобавьте первый товар!",
                reply_markup=back_to_main_kb(),
                parse_mode="HTML",
            )
        except Exception:
            await callback.message.answer(
                "📋 Товары отсутствуют.\nДобавьте первый товар!",
                reply_markup=back_to_main_kb(),
                parse_mode="HTML",
            )
        await callback.answer()
        return

    try:
        await callback.message.edit_text(
            f"📋 <b>Все товары ({len(products)}):</b>",
            reply_markup=admin_product_list_kb(products),
            parse_mode="HTML",
        )
    except Exception:
        await callback.message.answer(
            f"📋 <b>Все товары ({len(products)}):</b>",
            reply_markup=admin_product_list_kb(products),
            parse_mode="HTML",
        )
    await callback.answer()


@router.callback_query(F.data.startswith("admin_product:"))
async def cb_admin_product(callback: CallbackQuery, config: Config):
    product_id = int(callback.data.split(":")[1])
    product = await db.get_product_by_id(config.db_path, product_id)

    if not product:
        await callback.answer("❌ Товар не найден.", show_alert=True)
        return

    status = "✅ Активен" if product["is_active"] else "❌ Скрыт"
    price_str = f"{product['price']:.2f}₽"
    text = (
        f"📦 <b>{product['name']}</b>\n"
        f"ID: {product['id']} | {status}\n\n"
        f"📄 Описание: {product['description'] or '—'}\n"
        f"🏷 Тег: {product['tag'] or '—'}\n"
        f"🔑 LP группа: <code>{product['lp_group']}</code>\n"
        f"💰 Цена: {price_str}\n"
        f"🖼 Фото: {'есть' if product['photo_id'] else 'нет'}\n"
        f"📅 Добавлен: {product['created_at'][:16]}"
    )

    try:
        await callback.message.edit_text(
            text,
            reply_markup=admin_edit_product_kb(product_id),
            parse_mode="HTML",
        )
    except Exception:
        await callback.message.answer(
            text,
            reply_markup=admin_edit_product_kb(product_id),
            parse_mode="HTML",
        )
    await callback.answer()


# ─── ДОБАВЛЕНИЕ ТОВАРА ────────────────────────────────────────────────────────

@router.callback_query(F.data == "admin_add_product")
async def cb_add_product_start(callback: CallbackQuery, state: FSMContext):
    await state.set_state(AddProductStates.waiting_name)
    try:
        await callback.message.edit_text(
            "➕ <b>Добавление нового товара</b>\n\n"
            "Шаг 1/6 — Введите название товара:\n"
            "   (Например: VIP, PREMIUM, God Mode)",
            reply_markup=cancel_kb(),
            parse_mode="HTML",
        )
    except Exception:
        await callback.message.answer(
            "➕ <b>Добавление нового товара</b>\n\n"
            "Шаг 1/6 — Введите название товара:\n"
            "   (Например: VIP, PREMIUM, God Mode)",
            reply_markup=cancel_kb(),
            parse_mode="HTML",
        )
    await callback.answer()


@router.message(Command("addproduct"))
async def cmd_add_product(message: Message, state: FSMContext):
    await state.set_state(AddProductStates.waiting_name)
    await message.answer(
        "➕ <b>Добавление нового товара</b>\n\n"
        "Шаг 1/6 — Введите название товара:\n"
        "   (Например: VIP, PREMIUM, God Mode)",
        reply_markup=cancel_kb(),
        parse_mode="HTML",
    )


@router.message(AddProductStates.waiting_name)
async def process_product_name(message: Message, state: FSMContext):
    name = message.text.strip()
    if len(name) < 2 or len(name) > 64:
        await message.answer("❌ Название должно быть от 2 до 64 символов. Попробуйте ещё раз:")
        return

    await state.update_data(name=name)
    await state.set_state(AddProductStates.waiting_description)
    await message.answer(
        f"✅ Название: <b>{name}</b>\n\n"
        f"Шаг 2/6 — Введите описание товара:\n"
        f"   (Что входит в привилегию, какие плюшки получит игрок)",
        reply_markup=cancel_kb(),
        parse_mode="HTML",
    )


@router.message(AddProductStates.waiting_description)
async def process_product_description(message: Message, state: FSMContext):
    description = message.text.strip()
    if len(description) > 1024:
        await message.answer("❌ Описание слишком длинное (макс. 1024 символа). Сократите:")
        return

    await state.update_data(description=description)
    await state.set_state(AddProductStates.waiting_price)
    await message.answer(
        f"✅ Описание сохранено.\n\n"
        f"Шаг 3/6 — Введите цену в рублях:\n"
        f"   (Только число, например: 149 или 99.5)",
        reply_markup=cancel_kb(),
        parse_mode="HTML",
    )


@router.message(AddProductStates.waiting_price)
async def process_product_price(message: Message, state: FSMContext):
    try:
        price = float(message.text.strip().replace(",", "."))
        if price <= 0 or price > 999999:
            raise ValueError("Цена вне диапазона")
    except ValueError:
        await message.answer(
            "❌ Некорректная цена!\n"
            "Введите положительное число (например: 149 или 99.5):",
            reply_markup=cancel_kb(),
        )
        return

    await state.update_data(price=price)
    await state.set_state(AddProductStates.waiting_tag)
    await message.answer(
        f"✅ Цена: <b>{price}₽</b>\n\n"
        f"Шаг 4/6 — Введите тег/категорию товара:\n"
        f"   (Например: VIP, Донат, Сезонные. Отправьте '-' чтобы пропустить)",
        reply_markup=cancel_kb(),
        parse_mode="HTML",
    )


@router.message(AddProductStates.waiting_tag)
async def process_product_tag(message: Message, state: FSMContext):
    tag = message.text.strip()
    if tag == "-":
        tag = ""
    elif len(tag) > 32:
        await message.answer("❌ Тег слишком длинный (макс. 32 символа):")
        return

    await state.update_data(tag=tag)
    await state.set_state(AddProductStates.waiting_photo)
    await message.answer(
        f"✅ Тег: <b>{tag or 'без тега'}</b>\n\n"
        f"Шаг 5/6 — Отправьте фотографию товара:\n"
        f"   (Отправьте изображение или '-' чтобы пропустить)",
        reply_markup=cancel_kb(),
        parse_mode="HTML",
    )


@router.message(AddProductStates.waiting_photo, F.photo)
async def process_product_photo(message: Message, state: FSMContext):
    photo_id = message.photo[-1].file_id  # Берём самое большое фото
    await state.update_data(photo_id=photo_id)
    await state.set_state(AddProductStates.waiting_lp_group)
    await message.answer(
        f"✅ Фото сохранено.\n\n"
        f"Шаг 6/6 — Введите название группы LuckPerms:\n"
        f"   (Именно то имя группы, которое используется в /lp group list)\n"
        f"Например: vip, premium, elite, god",
        reply_markup=cancel_kb(),
        parse_mode="HTML",
    )


@router.message(AddProductStates.waiting_photo, F.text)
async def process_product_photo_skip(message: Message, state: FSMContext):
    if message.text.strip() == "-":
        await state.update_data(photo_id="")
        await state.set_state(AddProductStates.waiting_lp_group)
        await message.answer(
            f"✅ Фото пропущено.\n\n"
            f"Шаг 6/6 — Введите название группы LuckPerms:\n"
            f"   (Например: vip, premium, elite, god)",
            reply_markup=cancel_kb(),
            parse_mode="HTML",
        )
    else:
        await message.answer("❌ Отправьте фото или '-' чтобы пропустить:")


@router.message(AddProductStates.waiting_lp_group)
async def process_product_lp_group(message: Message, state: FSMContext, config: Config):
    lp_group = message.text.strip().lower()

    if not re.match(r'^[a-z0-9_-]{1,32}$', lp_group):
        await message.answer(
            "❌ Некорректное имя группы!\n"
            "Допустимы только: строчные буквы, цифры, '-', '_'\n"
            "Пример: vip, premium_plus, god-mode\n\nПопробуйте ещё раз:"
        )
        return

    data = await state.get_data()
    await state.clear()

    price_str = f"{data['price']:.2f}₽"
    text = (
        f"📋 <b>Проверьте данные нового товара:</b>\n\n"
        f"📝 Название: <b>{data['name']}</b>\n"
        f"📄 Описание: {data['description']}\n"
        f"💰 Цена: {price_str}\n"
        f"🏷 Тег: {data.get('tag') or '—'}\n"
        f"🖼 Фото: {'есть' if data.get('photo_id') else 'нет'}\n"
        f"🔑 LP группа: <code>{lp_group}</code>"
    )

    product_id = await db.add_product(
        config.db_path,
        name=data["name"],
        description=data["description"],
        price=data["price"],
        tag=data.get("tag", ""),
        photo_id=data.get("photo_id", ""),
        lp_group=lp_group,
    )

    await message.answer(
        f"✅ <b>Товар успешно добавлен! (ID: {product_id})</b>\n\n" + text,
        reply_markup=back_to_main_kb(),
        parse_mode="HTML",
    )

    # Если есть фото — показываем превью
    if data.get("photo_id"):
        await message.answer_photo(
            photo=data["photo_id"],
            caption=f"🖼 Фото товара: {data['name']}",
        )


# ─── РЕДАКТИРОВАНИЕ ТОВАРА ────────────────────────────────────────────────────

# Обработчик кнопки "Редактировать" из product_detail_admin_kb
@router.callback_query(F.data.startswith("admin_edit:"))
async def cb_admin_edit(callback: CallbackQuery, config: Config):
    product_id = int(callback.data.split(":")[1])
    product = await db.get_product_by_id(config.db_path, product_id)

    if not product:
        await callback.answer("❌ Товар не найден.", show_alert=True)
        return

    try:
        await callback.message.edit_text(
            f"✏️ <b>Редактирование товара #{product_id}: {product['name']}</b>\n\n"
            f"Выберите поле для изменения:",
            reply_markup=admin_edit_product_kb(product_id),
            parse_mode="HTML",
        )
    except Exception:
        await callback.message.answer(
            f"✏️ <b>Редактирование товара #{product_id}: {product['name']}</b>\n\n"
            f"Выберите поле для изменения:",
            reply_markup=admin_edit_product_kb(product_id),
            parse_mode="HTML",
        )
    await callback.answer()


FIELD_NAMES = {
    "name": "название",
    "description": "описание",
    "price": "цену (число)",
    "tag": "тег/категорию",
    "photo": "новое фото (или '-' пропустить)",
    "lp_group": "LP группу",
}


@router.callback_query(F.data.startswith("edit_field:"))
async def cb_edit_field(callback: CallbackQuery, state: FSMContext):
    parts = callback.data.split(":")
    product_id = int(parts[1])
    field = parts[2]

    await state.set_state(EditProductStates.waiting_value)
    await state.update_data(product_id=product_id, field=field)

    field_label = FIELD_NAMES.get(field, field)

    try:
        await callback.message.edit_text(
            f"✏️ <b>Редактирование товара #{product_id}</b>\n\n"
            f"Введите новое {field_label}:",
            reply_markup=cancel_kb(),
            parse_mode="HTML",
        )
    except Exception:
        await callback.message.answer(
            f"✏️ <b>Редактирование товара #{product_id}</b>\n\n"
            f"Введите новое {field_label}:",
            reply_markup=cancel_kb(),
            parse_mode="HTML",
        )
    await callback.answer()


@router.message(EditProductStates.waiting_value, F.photo)
async def process_edit_photo(message: Message, state: FSMContext, config: Config):
    data = await state.get_data()
    field = data.get("field")
    product_id = data.get("product_id")

    if field != "photo":
        await message.answer("❌ Ожидается текст, а не фото.")
        return

    photo_id = message.photo[-1].file_id
    await db.update_product(config.db_path, product_id, photo_id=photo_id)
    await state.clear()
    await message.answer(
        "✅ Фото товара обновлено!",
        reply_markup=back_to_main_kb(),
    )


@router.message(EditProductStates.waiting_value, F.text)
async def process_edit_value(message: Message, state: FSMContext, config: Config):
    data = await state.get_data()
    field = data.get("field")
    product_id = data.get("product_id")
    value = message.text.strip()

    if field == "photo":
        if value == "-":
            await db.update_product(config.db_path, product_id, photo_id="")
        else:
            await message.answer("❌ Отправьте фото или '-' для удаления:")
            return

    elif field == "price":
        try:
            price = float(value.replace(",", "."))
            if price <= 0 or price > 999999:
                raise ValueError()
            await db.update_product(config.db_path, product_id, price=price)
        except ValueError:
            await message.answer("❌ Некорректная цена. Введите положительное число:")
            return

    elif field == "lp_group":
        lp_group = value.lower()
        if not re.match(r'^[a-z0-9_-]{1,32}$', lp_group):
            await message.answer(
                "❌ Некорректное имя группы!\n"
                "Допустимы: строчные буквы, цифры, '-', '_'\n"
                "Попробуйте ещё раз:"
            )
            return
        await db.update_product(config.db_path, product_id, lp_group=lp_group)

    elif field == "name":
        if len(value) < 2 or len(value) > 64:
            await message.answer("❌ Название: от 2 до 64 символов:")
            return
        await db.update_product(config.db_path, product_id, name=value)

    elif field == "description":
        if len(value) > 1024:
            await message.answer("❌ Описание слишком длинное (макс. 1024 символа):")
            return
        await db.update_product(config.db_path, product_id, description=value)

    elif field == "tag":
        tag = "" if value == "-" else value[:32]
        await db.update_product(config.db_path, product_id, tag=tag)

    await state.clear()
    await message.answer(
        f"✅ Поле <b>{FIELD_NAMES.get(field, field)}</b> обновлено!",
        reply_markup=back_to_main_kb(),
        parse_mode="HTML",
    )


# ─── УДАЛЕНИЕ ТОВАРА ──────────────────────────────────────────────────────────

@router.callback_query(F.data.startswith("admin_delete:"))
async def cb_admin_delete(callback: CallbackQuery, config: Config):
    product_id = int(callback.data.split(":")[1])
    product = await db.get_product_by_id(config.db_path, product_id)

    if not product:
        await callback.answer("❌ Товар не найден.", show_alert=True)
        return

    try:
        await callback.message.edit_text(
            f"🗑 <b>Удаление товара</b>\n\n"
            f"Вы уверены, что хотите удалить товар:\n"
            f"<b>{product['name']}</b> (ID: {product_id})?\n\n"
            f"⚠️ Товар будет скрыт из каталога (мягкое удаление).",
            reply_markup=admin_confirm_delete_kb(product_id),
            parse_mode="HTML",
        )
    except Exception:
        await callback.message.answer(
            f"🗑 <b>Удаление товара</b>\n\n"
            f"Вы уверены, что хотите удалить товар:\n"
            f"<b>{product['name']}</b> (ID: {product_id})?\n\n"
            f"⚠️ Товар будет скрыт из каталога (мягкое удаление).",
            reply_markup=admin_confirm_delete_kb(product_id),
            parse_mode="HTML",
        )
    await callback.answer()


@router.callback_query(F.data.startswith("confirm_delete:"))
async def cb_confirm_delete(callback: CallbackQuery, config: Config):
    product_id = int(callback.data.split(":")[1])
    await db.delete_product(config.db_path, product_id)

    try:
        await callback.message.edit_text(
            f"✅ Товар #{product_id} скрыт из каталога.",
            reply_markup=back_to_main_kb(),
        )
    except Exception:
        await callback.message.answer(
            f"✅ Товар #{product_id} скрыт из каталога.",
            reply_markup=back_to_main_kb(),
        )
    await callback.answer("Товар удалён!")


# ─── ВСЕ ЗАКАЗЫ ───────────────────────────────────────────────────────────────

@router.callback_query(F.data == "admin_all_orders")
async def cb_admin_orders(callback: CallbackQuery, config: Config):
    orders = await db.get_all_orders(config.db_path, limit=30)

    if not orders:
        try:
            await callback.message.edit_text(
                "📊 <b>Заказы</b>\n\nЗаказов пока нет.",
                reply_markup=back_to_main_kb(),
                parse_mode="HTML",
            )
        except Exception:
            await callback.message.answer(
                "📊 <b>Заказы</b>\n\nЗаказов пока нет.",
                reply_markup=back_to_main_kb(),
                parse_mode="HTML",
            )
        await callback.answer()
        return

    status_emoji = {"completed": "✅", "pending": "⏳", "failed": "❌"}
    completed = sum(1 for o in orders if o["status"] == "completed")
    failed = sum(1 for o in orders if o["status"] == "failed")
    total_sum = sum(o["price"] for o in orders if o["status"] == "completed")

    lines = [
        f"📊 <b>Последние {len(orders)} заказов</b>\n",
        f"✅ Выполнено: {completed} | ❌ Ошибок: {failed}",
        f"💰 Сумма выполненных: {total_sum:.2f}₽\n",
    ]

    for o in orders[:20]:
        emoji = status_emoji.get(o["status"], "❓")
        price_str = f"{o['price']:.0f}₽"
        lines.append(
            f"{emoji} #{o['id']} <b>{o['product_name']}</b>\n"
            f"   👤 <code>{o['mc_nickname']}</code> | @{o['username']} | {price_str}\n"
            f"   📅 {o['created_at'][:16]}"
        )

    try:
        await callback.message.edit_text(
            "\n".join(lines),
            reply_markup=admin_orders_kb(),
            parse_mode="HTML",
        )
    except Exception:
        await callback.message.answer(
            "\n".join(lines),
            reply_markup=admin_orders_kb(),
            parse_mode="HTML",
        )
    await callback.answer()


@router.message(Command("stats"))
async def cmd_stats(message: Message, config: Config):
    orders = await db.get_all_orders(config.db_path, limit=1000)
    products = await db.get_all_products(config.db_path, active_only=False)

    completed = [o for o in orders if o["status"] == "completed"]
    failed = [o for o in orders if o["status"] == "failed"]
    total_sum = sum(o["price"] for o in completed)

    await message.answer(
        f"📊 <b>Статистика магазина</b>\n\n"
        f"📦 Всего товаров: {len(products)}\n"
        f"✅ Активных: {sum(1 for p in products if p['is_active'])}\n\n"
        f"🛒 Всего заказов: {len(orders)}\n"
        f"✅ Выполнено: {len(completed)}\n"
        f"❌ Ошибок: {len(failed)}\n"
        f"💰 Общая выручка: {total_sum:.2f}₽",
        parse_mode="HTML",
        reply_markup=back_to_main_kb(),
    )
