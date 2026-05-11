"""
Конфигурация бота.
Все чувствительные данные берутся из переменных окружения или .env файла.
"""

import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()


@dataclass
class BotConfig:
    token: str
    admin_ids: list[int]


@dataclass
class RconConfig:
    host: str
    port: int
    password: str


@dataclass
class Config:
    bot: BotConfig
    rcon: RconConfig
    db_path: str


def load_config() -> Config:
    token = os.getenv("BOT_TOKEN")
    if not token:
        raise ValueError("BOT_TOKEN не задан в .env файле!")

    admin_ids_raw = os.getenv("ADMIN_IDS", "")
    admin_ids = [int(x.strip()) for x in admin_ids_raw.split(",") if x.strip()]
    if not admin_ids:
        raise ValueError("ADMIN_IDS не задан в .env файле!")

    rcon_host = os.getenv("RCON_HOST", "localhost")
    rcon_port = int(os.getenv("RCON_PORT", "25575"))
    rcon_password = os.getenv("RCON_PASSWORD", "")

    db_path = os.getenv("DB_PATH", "shop.db")

    return Config(
        bot=BotConfig(token=token, admin_ids=admin_ids),
        rcon=RconConfig(host=rcon_host, port=rcon_port, password=rcon_password),
        db_path=db_path,
    )
