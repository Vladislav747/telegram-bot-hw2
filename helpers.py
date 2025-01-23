import aiohttp
import math
import random

from aiogram.types import Message

from config import WEATHER_API_KEY

food_api_url = "https://world.openfoodfacts.org/cgi/search.pl"
weather_api_url = "http://api.openweathermap.org/data/2.5/weather"


async def get_food_info(food_item):
    try:
        async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=False)) as session:
            params = {
                "action": "process",
                "search_terms": food_item,
                "json": 'true',
            }
            async with session.get(food_api_url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    if data.get('products'):
                        return data['products'][0]
                    return None
    except Exception as e:
        print(f"Ошибка при запросе к API OpenFoodFacts: {e}")
        return None


def calc_calories(weight, height, age):
    return math.ceil(10 * int(weight) + 6.25 * int(height) - 5 * int(age))


def calc_water_goal(weight, weather_temp):
    # +500−1000мл  за жаркую погоду (> 25°C).
    is_weather_hot_bonus = 500 if weather_temp > 25 else 0

    return int(weight) * 30 + int(is_weather_hot_bonus)


async def get_current_temperature(city):
    """
    Получение текущей температуры для указанного города через OpenWeatherMap API.
    """
    params = {
        'q': city,
        'appid': WEATHER_API_KEY,
        'units': 'metric',
    }

    try:
        async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=False)) as session:
            async with session.get(weather_api_url, params=params) as response:
                data = await response.json()
                temperature = data['main']['temp']
                return temperature

    except Exception as e:
        print(f"Ошибка при запросе к API OpenWeatherApi: {e}")
        return None


async def check_user(message: Message, users: dict) -> int or None:
    user_id = message.from_user.id
    if user_id not in users:
        await message.reply("Вы не установили свои данные! Пожалуйста, введите /set_profile")
        return None
    return user_id


def calc_calories_burned(duration):
    """
    Подсчет потраченных калорий в зависимости от активности и веса.
    """
    calories_burned_activity = random.randint(200, 500)
    convert_minutes = duration / 60
    return math.ceil(calories_burned_activity * convert_minutes)
