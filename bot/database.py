"""
Работа с базой данных SQLite через aiosqlite.
Таблицы:
  - products  — товары магазина
  - orders    — история заказов
"""

import aiosqlite
from typing import Optional


DB_PATH: str = "shop.db"


async def init_db(db_path: str = DB_PATH):
    """Создаёт таблицы если их нет."""
    async with aiosqlite.connect(db_path) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS products (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                name        TEXT    NOT NULL,
                description TEXT    NOT NULL DEFAULT '',
                price       REAL    NOT NULL,
                tag         TEXT    NOT NULL DEFAULT '',
                photo_id    TEXT    NOT NULL DEFAULT '',
                lp_group    TEXT    NOT NULL,
                is_active   INTEGER NOT NULL DEFAULT 1,
                created_at  TEXT    NOT NULL DEFAULT (datetime('now'))
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS orders (
                id           INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id      INTEGER NOT NULL,
                username     TEXT    NOT NULL DEFAULT '',
                product_id   INTEGER NOT NULL,
                product_name TEXT    NOT NULL,
                mc_nickname  TEXT    NOT NULL,
                price        REAL    NOT NULL,
                status       TEXT    NOT NULL DEFAULT 'pending',
                lp_group     TEXT    NOT NULL,
                created_at   TEXT    NOT NULL DEFAULT (datetime('now')),
                completed_at TEXT
            )
        """)
        await db.commit()


# ─── PRODUCTS ────────────────────────────────────────────────────────────────

async def add_product(
    db_path: str,
    name: str,
    description: str,
    price: float,
    tag: str,
    photo_id: str,
    lp_group: str,
) -> int:
    async with aiosqlite.connect(db_path) as db:
        cursor = await db.execute(
            """
            INSERT INTO products (name, description, price, tag, photo_id, lp_group)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (name, description, price, tag, photo_id, lp_group),
        )
        await db.commit()
        return cursor.lastrowid


async def get_all_products(db_path: str, active_only: bool = True) -> list:
    async with aiosqlite.connect(db_path) as db:
        db.row_factory = aiosqlite.Row
        query = "SELECT * FROM products"
        if active_only:
            query += " WHERE is_active = 1"
        query += " ORDER BY tag, name"
        async with db.execute(query) as cursor:
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]


async def get_product_by_id(db_path: str, product_id: int) -> Optional[dict]:
    async with aiosqlite.connect(db_path) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM products WHERE id = ?", (product_id,)
        ) as cursor:
            row = await cursor.fetchone()
            return dict(row) if row else None


async def get_products_by_tag(db_path: str, tag: str) -> list:
    async with aiosqlite.connect(db_path) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM products WHERE tag = ? AND is_active = 1 ORDER BY price",
            (tag,),
        ) as cursor:
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]


async def get_all_tags(db_path: str) -> list:
    async with aiosqlite.connect(db_path) as db:
        async with db.execute(
            "SELECT DISTINCT tag FROM products WHERE is_active = 1 AND tag != '' ORDER BY tag"
        ) as cursor:
            rows = await cursor.fetchall()
            return [row[0] for row in rows]


async def update_product(db_path: str, product_id: int, **kwargs):
    """Обновляет указанные поля товара."""
    allowed = {"name", "description", "price", "tag", "photo_id", "lp_group", "is_active"}
    fields = {k: v for k, v in kwargs.items() if k in allowed}
    if not fields:
        return
    set_clause = ", ".join(f"{k} = ?" for k in fields)
    values = list(fields.values()) + [product_id]
    async with aiosqlite.connect(db_path) as db:
        await db.execute(
            f"UPDATE products SET {set_clause} WHERE id = ?", values
        )
        await db.commit()


async def delete_product(db_path: str, product_id: int):
    """Мягкое удаление — скрываем товар."""
    await update_product(db_path, product_id, is_active=0)


async def hard_delete_product(db_path: str, product_id: int):
    async with aiosqlite.connect(db_path) as db:
        await db.execute("DELETE FROM products WHERE id = ?", (product_id,))
        await db.commit()


# ─── ORDERS ──────────────────────────────────────────────────────────────────

async def create_order(
    db_path: str,
    user_id: int,
    username: str,
    product_id: int,
    product_name: str,
    mc_nickname: str,
    price: float,
    lp_group: str,
) -> int:
    async with aiosqlite.connect(db_path) as db:
        cursor = await db.execute(
            """
            INSERT INTO orders
              (user_id, username, product_id, product_name, mc_nickname, price, lp_group)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (user_id, username, product_id, product_name, mc_nickname, price, lp_group),
        )
        await db.commit()
        return cursor.lastrowid


async def complete_order(db_path: str, order_id: int):
    async with aiosqlite.connect(db_path) as db:
        await db.execute(
            """
            UPDATE orders
            SET status = 'completed', completed_at = datetime('now')
            WHERE id = ?
            """,
            (order_id,),
        )
        await db.commit()


async def fail_order(db_path: str, order_id: int):
    async with aiosqlite.connect(db_path) as db:
        await db.execute(
            "UPDATE orders SET status = 'failed' WHERE id = ?", (order_id,)
        )
        await db.commit()


async def get_order(db_path: str, order_id: int) -> Optional[dict]:
    async with aiosqlite.connect(db_path) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM orders WHERE id = ?", (order_id,)
        ) as cursor:
            row = await cursor.fetchone()
            return dict(row) if row else None


async def get_user_orders(db_path: str, user_id: int) -> list:
    async with aiosqlite.connect(db_path) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM orders WHERE user_id = ? ORDER BY created_at DESC LIMIT 20",
            (user_id,),
        ) as cursor:
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]


async def get_all_orders(db_path: str, limit: int = 50) -> list:
    async with aiosqlite.connect(db_path) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM orders ORDER BY created_at DESC LIMIT ?", (limit,)
        ) as cursor:
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]
