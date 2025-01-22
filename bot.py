import asyncio
from aiogram import Bot, Dispatcher, types
from config import TOKEN
from handlers import router
from middleware import LoggingMiddleware

bot = Bot(token=TOKEN)
dp = Dispatcher()
dp.include_router(router)
dp.message.middleware(LoggingMiddleware())


async def main():
    print(f'Bot is running...')
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())