import random

# для считывания данных и построения графиков
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt

from aiogram import Router
from aiogram.types import Message, FSInputFile
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from states import Form
import re
from helpers import (
    get_food_info,
    calc_calories,
    calc_water_goal,
    get_current_temperature,
    check_user, calc_calories_burned
)

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
                        "/set_profile - Установить данные о себе\n"
                        "/log_water 30 - Записать информацию о потреблении воды\n"
                        "/log_food banana - Записать информацию о потреблении еды\n"
                        "/log_workout бег 30 - Записать информацию о занятиях\n"
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

    temperature = await get_current_temperature(data["city"])
    print(f"Temperature in {data['city']}: {temperature}")

    users[user_id] = {
        "weight": data["weight"],
        "height": data["height"],
        "age": data["age"],
        "activity": data["activity_time"],
        "city": data["city"],
        "water_goal": calc_water_goal(data["weight"], temperature),
        "calorie_goal": calc_calories(data["weight"], data["height"], data["age"]),
        "logged_water": 0,
        "logged_calories": 0,
        "burned_calories": 0,
    }
    print(f"Saved users {users}")
    await message.reply("Ваши данные успешно сохранены!")
    await state.clear()


# Обработчик команды /log_water
@router.message(Command("log_water"))
async def start_form_log_water(message: Message):
    user_id = await check_user(message, users)
    if user_id is None:
        return None
    try:
        text = message.text
        user_data = users[user_id]
        water_volume = text.split(maxsplit=1)[1]

        logged_water = user_data["logged_water"] + int(water_volume)
        water_goal = user_data["water_goal"]
        calculated_water = water_goal - logged_water
        if logged_water > water_goal or calculated_water < 0:
            await message.reply("Вы выполнили норму потребления воды!")
            return None
        users[user_id]["logged_water"] = water_goal if logged_water >= water_goal else logged_water
        await message.reply(f"Нужно выпить еще до нормы: {calculated_water} мл")
    except Exception as e:
        print(f"Ошибка при добавлении воды: {e}")
        await message.reply("Произошла ошибка при добавлении воды")
    return None


# Обработчик команды /log_food
@router.message(Command("log_food"))
async def start_form_log_food(message: Message):
    text = message.text
    user_id = await check_user(message, users)
    if user_id is None:
        return None
    try:
        food_item = text.split(maxsplit=1)[1]
        print(food_item, "food_item log_food")  # Debugging line

        # Проверяем, содержит ли ввод только английские символы
        if not re.match(r'^[a-zA-Z\s]+$', food_item):
            await message.reply("Название продукта "
                                "должно содержать только "
                                "английские буквы! Пример: /log_food banana"
                                )
            return None
    except IndexError:
        await message.reply("Вы не указали продукт! Пример: /log_food banana")
        return None

    try:
        product = await get_food_info(food_item)
        if product:
            product_name = product.get('product_name', 'Неизвестно')
            energy_kcal = product.get('nutriments', {}).get('energy-kcal_100g', 'Неизвестно')

            response_text = (
                f"Продукт: {product_name}\n"
                f"Калории: {energy_kcal}"
            )
            users[user_id]["logged_calories"] = users[user_id]["logged_calories"] + energy_kcal
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
    user_id = await check_user(message, users)
    if user_id is None:
        return None
    text = message.text
    parts = text.split(maxsplit=2)

    try:
        duration = int(parts[2])
    except ValueError:
        await message.reply("Время занятия должно быть числом! Пример: /log_workout бег 30")
        return None
    activity = parts[1]
    if type(activity) is not str:
        await message.reply("Спортивная активная должна быть строкой! Пример: /log_workout бег 30")
        return None

    calories_burned_total = calc_calories_burned(duration)
    needed_water_volume = random.randint(100, 200)

    print(f"log_workout длительность-{duration}, activity-{activity} - Сожжено {calories_burned_total} ккал")  # Debugging line
    progress_text = (
        f"🏃‍♂️ {activity} {duration} минут — {calories_burned_total} ккал. Дополнительно: выпейте {needed_water_volume} мл воды."
    )

    users[user_id]["burned_calories"] = users[user_id]["burned_calories"] + calories_burned_total

    await message.reply(progress_text, parse_mode="Markdown")


# Обработчик команды /check_progress
@router.message(Command("check_progress"))
async def start_form_check_progress(message: Message, state: FSMContext):
    user_id = await check_user(message, users)
    if user_id is None:
        return None
    user_data = users[user_id]

    is_enough_water = "Норма воды выполнена" if user_data['logged_water'] > user_data['water_goal'] else f"Осталось: {user_data['water_goal'] - user_data['logged_water']} мл."

    progress_text = (
        "📊 *Прогресс:*\n"
        "*Вода:*\n"
        f"- Выпито: {user_data['logged_water']} мл из {user_data['water_goal']} мл.\n"
        f"- {is_enough_water} \n\n"
        "*Калории:*\n"
        f"- Потреблено: {user_data['logged_calories']} ккал из {user_data['calorie_goal']} ккал.\n"
        f"- Сожжено: {user_data['burned_calories']} ккал.\n"
        f"- Баланс: {user_data['logged_calories'] - user_data['burned_calories']} ккал."
    )

    await message.reply(progress_text, parse_mode="Markdown")
    chart_filepath = send_progress_chart(user_data['logged_calories'], user_data['burned_calories'])
    await message.reply_photo(photo=FSInputFile(chart_filepath), caption="Ваш прогресс по калориям 📊")


def send_progress_chart(logged_calories, burned_calories):

    # Данные для графика
    data = {
        'labels': ['Потреблено калорий', 'Сожжено калорий'],
        'values': [int(logged_calories), int(burned_calories)],  # Пример значений
    }
    df = pd.DataFrame(data)

    plt.figure()
    sns.set(rc={'figure.figsize': (8, 6)})  # Размер графика
    sns.barplot(x='labels', y='values', data=df, palette="viridis")

    # Настройки для отображения
    plt.title("График калорий")
    plt.xlabel("Категории", fontsize=12)
    plt.ylabel("Значения (ккал)", fontsize=12)
    plt.xticks(rotation=0, fontsize=10)
    plt.tight_layout()

    plt.savefig('plot_name.png', dpi=300)
    filename = 'plot_name.png'
    return filename
