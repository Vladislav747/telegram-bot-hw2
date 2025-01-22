import aiohttp

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
