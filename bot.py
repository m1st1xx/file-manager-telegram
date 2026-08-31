import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.client.session.aiohttp import AiohttpSession
from config import BOT_TOKEN,PROXY_URL
from handlers import auth, subjects, files

async def main():
    if not BOT_TOKEN:
        raise RuntimeError("BOT_TOKEN is not set")

    if PROXY_URL:
        session = AiohttpSession(proxy=PROXY_URL)
        bot = Bot(BOT_TOKEN, session=session)
    else:
        bot = Bot(BOT_TOKEN)

    dp = Dispatcher()
    dp.include_router(auth.router)
    dp.include_router(subjects.router)
    dp.include_router(files.router)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
