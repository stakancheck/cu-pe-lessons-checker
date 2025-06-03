import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

import db
from config import BOT_TOKEN
from handlers import router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

async def main():
    # Initialize bot and dispatcher
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher(storage=MemoryStorage())
    
    # Register handlers
    dp.include_router(router)
    
    # Initialize database
    await db.init_db()
    
    # Start polling
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main()) 