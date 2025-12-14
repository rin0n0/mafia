import asyncio
import logging
import os

from aiogram import Bot, Dispatcher
from aiogram.filters import CommandStart
from aiogram.types import Message, WebAppInfo
from aiogram.utils.keyboard import InlineKeyboardBuilder

logging.basicConfig(level=logging.INFO)

BOT_TOKEN = os.environ.get("BOT_TOKEN")

PUBLIC_URL = os.environ.get("PUBLIC_URL") 

if not BOT_TOKEN or not PUBLIC_URL:
    raise ValueError("BOT_TOKEN and PUBLIC_URL environment variables must be set!")

async def main():
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()

    @dp.message(CommandStart())
    async def command_start_handler(message: Message) -> None:
        builder = InlineKeyboardBuilder()
        builder.button(
            text="🎲 Начать игру",
            web_app=WebAppInfo(url=PUBLIC_URL)
        )
        
        await message.answer(
            "Добро пожаловать в Мафию! Нажмите кнопку ниже, чтобы запустить игру.",
            reply_markup=builder.as_markup()
        )

    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())