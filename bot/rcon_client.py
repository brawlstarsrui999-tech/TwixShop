"""
RCON клиент для отправки команд на Minecraft сервер.
Использует библиотеку mcrcon.
LuckPerms команда для выдачи группы:
  lp user <ник> parent add <группа>
"""

import asyncio
import logging

logger = logging.getLogger(__name__)


def _send_sync(host: str, port: int, password: str, command: str, timeout: int) -> str:
    """Синхронная отправка RCON команды."""
    try:
        from mcrcon import MCRcon, MCRconException
        with MCRcon(host, password, port=port, timeout=timeout) as mcr:
            response = mcr.command(command)
            return response
    except Exception:
        raise


async def send_rcon_command(
    host: str,
    port: int,
    password: str,
    command: str,
    timeout: int = 10,
) -> tuple:
    """
    Отправляет команду на сервер через RCON.
    Возвращает (успех, ответ_сервера).
    """
    try:
        from mcrcon import MCRconException
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None,
            _send_sync,
            host, port, password, command, timeout
        )
        return True, result
    except Exception as e:
        err_name = type(e).__name__
        if "MCRconException" in err_name:
            logger.error(f"RCON ошибка аутентификации: {e}")
            return False, f"Ошибка аутентификации: {e}"
        elif isinstance(e, ConnectionRefusedError):
            logger.error("RCON: Соединение отклонено. Сервер выключен или RCON не включён.")
            return False, "Соединение отклонено"
        elif isinstance(e, (TimeoutError, OSError)):
            logger.error(f"RCON: Ошибка соединения: {e}")
            return False, f"Ошибка соединения: {e}"
        else:
            logger.error(f"RCON неизвестная ошибка: {e}")
            return False, str(e)


async def grant_luckperms_group(
    host: str,
    port: int,
    password: str,
    mc_nickname: str,
    lp_group: str,
) -> tuple:
    """
    Выдаёт игроку группу через LuckPerms.
    Команда: lp user <ник> parent add <группа>
    """
    command = f"lp user {mc_nickname} parent add {lp_group}"
    logger.info(f"Выдаём группу '{lp_group}' игроку '{mc_nickname}' через RCON...")
    success, response = await send_rcon_command(host, port, password, command)
    if success:
        logger.info(f"Группа выдана. Ответ сервера: {response}")
    else:
        logger.error(f"Не удалось выдать группу. Ошибка: {response}")
    return success, response


async def check_player_online(
    host: str,
    port: int,
    password: str,
    mc_nickname: str,
) -> bool:
    """Проверяет, онлайн ли игрок."""
    success, response = await send_rcon_command(
        host, port, password, "list"
    )
    if not success:
        return False
    return mc_nickname.lower() in response.lower()
