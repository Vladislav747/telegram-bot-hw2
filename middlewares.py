from aiogram import BaseMiddleware
from aiogram.types import Message


class LoggingMiddleware(BaseMiddleware):
    async def __call__(self, handler, event: Message, data: dict):
        print(f"Received message: {event.text}")
        handler_name = handler.__name__
        print(f"Handler triggered: {handler_name}")
        return await handler(event, data)
