import asyncio
import logging
from aiogram import Bot, Dispatcher
from config import BOT_TOKEN
from handlers import auth, subjects, files

async def main():
    if not BOT_TOKEN:
        raise RuntimeError("BOT_TOKEN is not set")
    logging.basicConfig(level=logging.INFO)
    bot = Bot(BOT_TOKEN)
    dp = Dispatcher()
    dp.include_router(auth.router)
    dp.include_router(subjects.router)
    dp.include_router(files.router)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
