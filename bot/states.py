"""
FSM состояния для диалогов бота.
"""

from aiogram.fsm.state import State, StatesGroup


class BuyStates(StatesGroup):
    """Состояния покупки товара."""
    waiting_nickname = State()
    waiting_confirm = State()


class AddProductStates(StatesGroup):
    """Состояния добавления товара (для администраторов)."""
    waiting_name = State()
    waiting_description = State()
    waiting_price = State()
    waiting_tag = State()
    waiting_photo = State()
    waiting_lp_group = State()


class EditProductStates(StatesGroup):
    """Состояния редактирования товара (для администраторов)."""
    waiting_value = State()
