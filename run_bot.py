import asyncio
import os
import traceback
from pathlib import Path

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from dotenv import load_dotenv

####### django #####
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'web.settings.settings')
django.setup()
####################

from bot.handlers import (back_button_handler, connect_wallet_handlers,
                          create_wallet_from_seed_handlers,
                          create_wallet_handlers, delete_wallet_handlers,
                          other_handlers, transaction_handlers,
                          transfer_handlers, user_handlers)
from logger_config import logger

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(os.path.join(BASE_DIR, '.env'))


async def main() -> None:
    """
        Function to configure and run the bot.

        Initializes the bot and dispatcher, registers routers, skips accumulated updates,
        and starts polling.

        Returns:
            None
    """
    logger.info("Initializing bot...")
    # Инициализируем бот и диспетчер
    bot: Bot = Bot(token=os.getenv('BOT_TOKEN', ''), default=DefaultBotProperties(parse_mode='HTML'))
    dp: Dispatcher = Dispatcher()
    logger.info("Bot initialized successfully.")

    dp.include_router(user_handlers.user_router)
    dp.include_router(create_wallet_handlers.create_wallet_router)
    dp.include_router(create_wallet_from_seed_handlers.create_wallet_from_seed_router)
    dp.include_router(connect_wallet_handlers.connect_wallet_router)
    dp.include_router(transfer_handlers.transfer_router)
    dp.include_router(transaction_handlers.transaction_router)
    dp.include_router(other_handlers.other_router)
    dp.include_router(back_button_handler.back_button_router)
    dp.include_router(delete_wallet_handlers.delete_wallet_router)

    # Пропускаем накопившиеся апдейты и запускаем polling
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.warning("Application terminated by the user")
    except Exception as error:
        detailed_send_message_error = traceback.format_exc()
        logger.error(f"Unexpected error in the application: {error}\n{detailed_send_message_error}")
