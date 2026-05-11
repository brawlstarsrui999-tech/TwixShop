# ⛏️ MC Shop Bot — Telegram магазин привилегий для Minecraft

Полноценный Telegram-бот для продажи привилегий на Minecraft сервере.
После покупки привилегия выдаётся игроку **автоматически** через RCON/LuckPerms.

---

## 🚀 Быстрый старт

```bash
# 1. Установка зависимостей
pip install -r requirements.txt

# 2. Настройка конфигурации
cp .env.example .env
# Отредактируйте .env — вставьте токен, ID adminов, данные RCON

# 3. Запуск
python main.py
```

---

## ⚙️ Настройка .env

| Переменная | Описание |
|---|---|
| `BOT_TOKEN` | Токен от @BotFather |
| `ADMIN_IDS` | Telegram ID администраторов через запятую |
| `RCON_HOST` | IP/хост Minecraft сервера |
| `RCON_PORT` | RCON порт (по умолчанию 25575) |
| `RCON_PASSWORD` | Пароль RCON из server.properties |
| `DB_PATH` | Путь к SQLite файлу (по умолчанию shop.db) |

---

## 🎮 server.properties

```properties
enable-rcon=true
rcon.port=25575
rcon.password=ВАШИЙ_ПАРОЛЬ
broadcast-rcon-to-ops=false
```

---

## 👤 Функции для покупателей

- Просмотр каталога с категориями (тегами)
- Карточки товаров с фото, описанием, ценой
- Покупка: ввод ника → подтверждение → мгновенная выдача
- История заказов (`/orders`)

## 🛠️ Функции для администраторов

- Добавление товаров через FSM диалог (название, описание, цена, тег, фото, LP группа)
- Редактирование любого поля товара
- Мягкое удаление (скрытие) товаров
- Просмотр всех заказов со статусами
- Уведомления о каждом заказе (в т.ч. при ошибках RCON)
- Статистика `/stats`

---

## 🔑 LuckPerms

Бот выполняет команду через RCON:
```
lp user <ник> parent add <lp_group>
```

Пример: при покупке товара с `lp_group = vip` игроку `Steve`:
```
lp user Steve parent add vip
```

При ошибке RCON — заказ сохраняется как `failed`, админы получают уведомление с командой для ручной выдачи.

---

## 📁 Структура

```
mc-shop-bot/
├── main.py                 # Точка входа
├── requirements.txt
├── .env
└── bot/
    ├── config.py           # Загрузка конфигурации
    ├── database.py         # SQLite операции
    ├── rcon_client.py      # RCON + LuckPerms
    ├── keyboards.py        # Все клавиатуры
    ├── states.py           # FSM состояния
    ├── filters.py          # AdminFilter
    ├── middlewares.py      # ConfigMiddleware
    └── handlers/
        ├── common.py       # /start, /help
        ├── shop.py         # Каталог, покупка
        └── admin.py        # Управление товарами
```

---

## 💳 Оплата

> ⚠️ Бот **не включает платёжную систему**. Текущая реализация выдаёт привилегию сразу после подтверждения (удобно для тестирования).
>
> Для добавления реальной оплаты — интегрируйте ЮKassa / Robokassa / Telegram Stars в хендлер `confirm_buy` файла `bot/handlers/shop.py` и вызывайте `grant_luckperms_group()` только после успешного платежа.

---

## 📦 Зависимости

```
aiogram==3.13.1      # Telegram Bot API фреймворк
aiosqlite==0.20.0    # Async SQLite
mcrcon==0.7.0        # RCON клиент для Minecraft
python-dotenv==1.0.1 # Загрузка .env
```
