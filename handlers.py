from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
import aiohttp
from states import Form
import ssl
import certifi

ssl_context = ssl.create_default_context(cafile=certifi.where())

router = Router()


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
                        )


# Обработчик команды /set_profile
@router.message(Command("set_profile"))
async def start_form(message: Message, state: FSMContext):
    await message.reply("Введите ваш вес (в кг):")
    await state.set_state(Form.weight)


@router.message(Form.weight)
async def process_weight(message: Message, state: FSMContext):
    await state.update_data(name=message.text)
    await message.reply("Введите ваш рост (в см):")
    await state.set_state(Form.height)


@router.message(Form.height)
async def process_height(message: Message, state: FSMContext):
    await message.reply("Введите ваш возраст:")
    await state.set_state(Form.age)


@router.message(Form.age)
async def process_age(message: Message, state: FSMContext):
    await message.reply("Сколько минут активности у вас в день?")
    await state.set_state(Form.activity_time)


@router.message(Form.activity_time)
async def process_activity(message: Message, state: FSMContext):
    await message.reply("В каком городе вы находитесь?")
    await state.set_state(Form.city)


@router.message(Form.activity_time)
async def process_activity(message: Message, state: FSMContext):
    await message.reply("В каком городе вы находитесь?")
    await state.set_state(Form.city)


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
async def start_form_log_food(message: Message, state: FSMContext):
    text = message.text
    try:
        food_item = text.split(maxsplit=1)[1]
    except IndexError:
        await message.reply("Вы не указали продукт! Пример: /log_food banan")
        return

    try:
        async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=False)) as session:
            async with session.get(f"https://world.openfoodfacts.org/cgi/search.pl?action=process&search_terms={food_item}&json=true") as response:
                if response.status == 200:
                    data = await response.json()
                    if data.get('products'):
                        product = data['products'][0]
                        product_name = product.get('product_name', 'Неизвестно')
                        nutrition_grades = product.get('nutrition_grades', 'Неизвестно')
                        energy_kcal = product.get('nutriments', {}).get('energy-kcal_100g', 'Неизвестно')

                        # Формируем ответ
                        response_text = (
                            f"Продукт: {product_name}\n"
                            f"Класс питания: {nutrition_grades}\n"
                            f"Калории: {energy_kcal}"
                        )
                        await message.reply(f"Твой продукт {response_text}")
                    else:
                        await message.reply("Продукт не найден.")
                else:
                    await message.reply("Ошибка при получении данных о продукте")
    except Exception as e:
        print(e, "error log_food")
        await message.reply("Ошибка при получении данных о продукте")
