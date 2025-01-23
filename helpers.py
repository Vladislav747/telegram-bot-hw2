import aiohttp
import math

url = "https://world.openfoodfacts.org/cgi/search.pl"


async def fetch_product_data(food_item):
    try:
        async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=False)) as session:
            params = {
                "action": "process",
                "search_terms": food_item,
                "json": 'true',
            }
            async with session.get(url, params=params) as response:
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

    return int(weight)*30 + int(is_weather_hot_bonus)
