"""
Все клавиатуры бота.
"""

from aiogram.types import (
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    ReplyKeyboardRemove,
)
from aiogram.utils.keyboard import InlineKeyboardBuilder


# ─── ГЛАВНОЕ МЕНЮ ─────────────────────────────────────────────────────────────

def main_menu_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="🛒 Каталог товаров", callback_data="catalog"))
    builder.row(InlineKeyboardButton(text="📦 Мои заказы", callback_data="my_orders"))
    builder.row(InlineKeyboardButton(text="ℹ️ Помощь", callback_data="help"))
    return builder.as_markup()


def admin_main_menu_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="🛒 Каталог товаров", callback_data="catalog"))
    builder.row(InlineKeyboardButton(text="📦 Мои заказы", callback_data="my_orders"))
    builder.row(
        InlineKeyboardButton(text="➕ Добавить товар", callback_data="admin_add_product"),
        InlineKeyboardButton(text="📋 Все товары", callback_data="admin_list_products"),
    )
    builder.row(
        InlineKeyboardButton(text="📊 Все заказы", callback_data="admin_all_orders"),
    )
    builder.row(InlineKeyboardButton(text="ℹ️ Помощь", callback_data="help"))
    return builder.as_markup()


# ─── КАТАЛОГ ──────────────────────────────────────────────────────────────────

def tags_kb(tags: list) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for tag in tags:
        builder.row(InlineKeyboardButton(text=f"🏷 {tag}", callback_data=f"tag:{tag}"))
    builder.row(InlineKeyboardButton(text="📦 Все товары", callback_data="tag:__all__"))
    builder.row(InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu"))
    return builder.as_markup()


def products_kb(products: list, tag: str = "") -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for p in products:
        price_str = f"{p['price']:.0f}" if p['price'] == int(p['price']) else f"{p['price']:.2f}"
        builder.row(
            InlineKeyboardButton(
                text=f"{p['name']} — {price_str}₽",
                callback_data=f"product:{p['id']}",
            )
        )
    builder.row(InlineKeyboardButton(text="◀️ Назад", callback_data="catalog"))
    return builder.as_markup()


def product_detail_kb(product_id: int, tag: str = "") -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="💳 Купить", callback_data=f"buy:{product_id}")
    )
    builder.row(InlineKeyboardButton(text="◀️ Назад к каталогу", callback_data="catalog"))
    builder.row(InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu"))
    return builder.as_markup()


def product_detail_admin_kb(product_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="💳 Купить", callback_data=f"buy:{product_id}")
    )
    builder.row(
        InlineKeyboardButton(text="✏️ Редактировать", callback_data=f"admin_edit:{product_id}"),
        InlineKeyboardButton(text="🗑 Удалить", callback_data=f"admin_delete:{product_id}"),
    )
    builder.row(InlineKeyboardButton(text="◀️ Назад к каталогу", callback_data="catalog"))
    builder.row(InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu"))
    return builder.as_markup()


# ─── ПОКУПКА ──────────────────────────────────────────────────────────────────

def confirm_purchase_kb(product_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="✅ Подтвердить", callback_data=f"confirm_buy:{product_id}"),
        InlineKeyboardButton(text="❌ Отмена", callback_data=f"product:{product_id}"),
    )
    return builder.as_markup()


def cancel_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="❌ Отмена", callback_data="main_menu"))
    return builder.as_markup()


def back_to_main_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu"))
    return builder.as_markup()


# ─── АДМИНИСТРАТИВНЫЕ ─────────────────────────────────────────────────────────

def admin_product_list_kb(products: list) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for p in products:
        status = "✅" if p["is_active"] else "❌"
        price_str = f"{p['price']:.0f}" if p['price'] == int(p['price']) else f"{p['price']:.2f}"
        builder.row(
            InlineKeyboardButton(
                text=f"{status} {p['name']} [{p['tag']}] — {price_str}₽",
                callback_data=f"admin_product:{p['id']}",
            )
        )
    builder.row(InlineKeyboardButton(text="➕ Добавить товар", callback_data="admin_add_product"))
    builder.row(InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu"))
    return builder.as_markup()


def admin_edit_product_kb(product_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="📝 Название", callback_data=f"edit_field:{product_id}:name"),
        InlineKeyboardButton(text="📄 Описание", callback_data=f"edit_field:{product_id}:description"),
    )
    builder.row(
        InlineKeyboardButton(text="💰 Цена", callback_data=f"edit_field:{product_id}:price"),
        InlineKeyboardButton(text="🏷 Тег", callback_data=f"edit_field:{product_id}:tag"),
    )
    builder.row(
        InlineKeyboardButton(text="🖼 Фото", callback_data=f"edit_field:{product_id}:photo"),
        InlineKeyboardButton(text="🔑 LP Группа", callback_data=f"edit_field:{product_id}:lp_group"),
    )
    builder.row(
        InlineKeyboardButton(text="🗑 Удалить товар", callback_data=f"admin_delete:{product_id}"),
    )
    builder.row(InlineKeyboardButton(text="◀️ Назад", callback_data="admin_list_products"))
    return builder.as_markup()


def admin_confirm_delete_kb(product_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="✅ Да, удалить", callback_data=f"confirm_delete:{product_id}"),
        InlineKeyboardButton(text="❌ Отмена", callback_data=f"admin_product:{product_id}"),
    )
    return builder.as_markup()


def admin_orders_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu"))
    return builder.as_markup()


def remove_kb() -> ReplyKeyboardRemove:
    return ReplyKeyboardRemove()
