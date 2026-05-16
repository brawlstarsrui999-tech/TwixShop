"""
FSM состояния для всех диалогов бота.
"""

from aiogram.fsm.state import State, StatesGroup


class AddProductStates(StatesGroup):
    """Состояния для добавления нового товара."""
    waiting_name        = State()
    waiting_description = State()
    waiting_price       = State()
    waiting_tag         = State()
    waiting_photo       = State()
    waiting_lp_group    = State()
    confirm             = State()


class EditProductStates(StatesGroup):
    """Состояния для редактирования товара."""
    waiting_value = State()


class BuyStates(StatesGroup):
    """Состояния для процесса покупки."""
    waiting_nickname = State()
    waiting_confirm  = State()
