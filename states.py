from aiogram.fsm.state import State, StatesGroup


class Form(StatesGroup):
    user_id=State()
    weight = State()
    height = State()
    age = State()
    activity_time = State()
    city = State()
    water_volume = State()
