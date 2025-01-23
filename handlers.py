from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from states import Form
import re
from helpers import fetch_product_data, calc_calories, calc_water_goal

router = Router()

# Словарь для хранения информации о пользователях
users = {}


# Обработчик команды /start
@router.message(Command("start"))
async def start_command(message: Message):
    await message.reply("Добро пожаловать! Это простой бот")


# Обработчик команды /help
@router.message(Command("help"))
async def help_command(message: Message):
    await message.reply("Доступные команды:\n"
                        "/start - начать работу с ботом\n"
                        "/set_profile - Установить данные о себе\n"
                        "/log_water - Записать информацию о потреблении воды\n"
                        "/log_food - Записать информацию о потреблении еды\n"
                        "/log_workout - Записать информацию о занятиях\n"
                        "/check_progress - Узнать прогресс\n"
                        )


# Обработчик команды /set_profile
@router.message(Command("set_profile"))
async def start_form(message: Message, state: FSMContext):
    await state.update_data(user_id=message.from_user.id)
    await message.reply("Введите ваш вес (в кг):")
    await state.set_state(Form.weight)


@router.message(Form.weight)
async def process_weight(message: Message, state: FSMContext):
    await message.reply("Введите ваш рост (в см):")
    await state.set_state(Form.height)
    await state.update_data(weight=message.text)


@router.message(Form.height)
async def process_height(message: Message, state: FSMContext):
    await message.reply("Введите ваш возраст:")
    await state.set_state(Form.age)
    await state.update_data(height=message.text)


@router.message(Form.age)
async def process_age(message: Message, state: FSMContext):
    await message.reply("Сколько минут активности у вас в день?")
    await state.set_state(Form.activity_time)
    await state.update_data(age=message.text)


@router.message(Form.activity_time)
async def process_activity(message: Message, state: FSMContext):
    await message.reply("В каком городе вы находитесь?")
    await state.set_state(Form.city)
    await state.update_data(activity_time=message.text)


@router.message(Form.city)
async def process_city(message: Message, state: FSMContext):
    await state.update_data(city=message.text)
    data = await state.get_data()
    user_id = data["user_id"]

    users[user_id] = {
        "weight": data["weight"],
        "height": data["height"],
        "age": data["age"],
        "activity": data["activity_time"],
        "city": data["city"],
        "water_goal": calc_water_goal(data["weight"], 1500),
        "calorie_goal": calc_calories(data["weight"], data["height"], data["age"]),
        "logged_water": 0,
        "logged_calories": 0,
        "burned_calories": 0,
    }
    print(f"Saved users {users}")# Debugging line
    await message.reply("Ваши данные успешно сохранены!")
    await state.clear()


# Обработчик команды /log_water
@router.message(Command("log_water"))
async def start_form_log_water(message: Message, state: FSMContext):
    await message.reply("Введите сколько вы выпили воды за день?(мл):")
    await state.set_state(Form.water_volume)


@router.message(Form.water_volume)
async def start_form_log_water(message: Message, state: FSMContext):
    data = await state.get_data()
    water_volume = data.get("water_volume")
    calc_water = int(water_volume) * 0.001
    await message.reply(f"Выпито воды: {calc_water} мл")


# Обработчик команды /log_food
@router.message(Command("log_food"))
async def start_form_log_food(message: Message):
    text = message.text
    try:
        food_item = text.split(maxsplit=1)[1]
        print(food_item, "food_item log_food")  # Debugging line

        # Проверяем, содержит ли ввод только английские символы
        if not re.match(r'^[a-zA-Z\s]+$', food_item):
            await message.reply("Название продукта должно содержать только английские буквы! Пример: /log_food banana")
            return None
    except IndexError:
        await message.reply("Вы не указали продукт! Пример: /log_food banana")
        return None

    try:
        product = await fetch_product_data(food_item)
        if product:
            product_name = product.get('product_name', 'Неизвестно')
            energy_kcal = product.get('nutriments', {}).get('energy-kcal_100g', 'Неизвестно')

            response_text = (
                f"Продукт: {product_name}\n"
                f"Калории: {energy_kcal}"
            )
            await message.reply(f"Твой продукт {response_text}")
        else:
            await message.reply("Продукт не найден.")
        return None
    except Exception as e:
        print(e, "error log_food")
        await message.reply("Ошибка при получении данных о продукте")
        return None


# Обработчик команды /log_workout
@router.message(Command("log_workout"))
async def start_form_log_workout(message: Message, state: FSMContext):
    text = message.text
    parts = text.split(maxsplit=2)

    try:
        duration = int(parts[2])
    except ValueError:
        await message.reply("Время занятия должно быть числом! Пример: /log_workout бег 30")
        return None
    activity = parts[1]
    if type(activity) is str:
        await message.reply("Спортивная активная должна быть строкой! Пример: /log_workout бег 30")
        return None

    print(f"log_workout длительность-{duration}, activity-{activity}")  # Debugging line
    progress_text = (
        f"🏃‍♂️ {activity} {duration} минут — 300 ккал. Дополнительно: выпейте 200 мл воды."
    )

    await message.reply(progress_text, parse_mode="Markdown")


# Обработчик команды /check_progress
@router.message(Command("check_progress"))
async def start_form_check_progress(message: Message, state: FSMContext):
    progress_text = (
        "📊 *Прогресс:*\n"
        "*Вода:*\n"
        f"- Выпито: {1500} мл из {2400} мл.\n"
        f"- Осталось: {2400 - 1500} мл.\n\n"
        "*Калории:*\n"
        f"- Потреблено: {1800} ккал из {2500} ккал.\n"
        f"- Сожжено: {400} ккал.\n"
        f"- Баланс: {1800 - 400} ккал."
    )

    await message.reply(progress_text, parse_mode="Markdown")
