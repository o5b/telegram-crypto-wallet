import asyncio
import json
import traceback
from decimal import Decimal

from aiogram import F, Router
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import default_state
from aiogram.types import CallbackQuery

from bot.config import LAMPORT_TO_SOL_RATIO, SOLANA_NODE_URL
from bot.keyboards import get_main_keyboard
from bot.services import get_solana_transaction_history
from bot.states import FSMWallet
from bot.utils import (get_transaction_history_from_db, get_translation,
                       save_transaction)
from bot.wallet_service import (format_transaction_from_db_message,
                                format_transaction_message)
from logger_config import logger

transaction_router: Router = Router()


@transaction_router.callback_query(F.data.startswith("wallet_address:"),
                                   StateFilter(FSMWallet.choose_transaction_wallet))
async def process_choose_transaction_wallet(callback: CallbackQuery, state: FSMContext) -> None:
    """
        Handles the button press to select a wallet address for fetching transaction history.

        Args:
            callback (CallbackQuery): The callback query object.
            state (FSMContext): The state context of the finite state machine.

        Returns:
            None
    """
    try:
        transaction_history = []
        tr_from_db_tasks = []
        transaction_id_before = None
        transaction_limit = 5
        transaction_max_limit = 100

        TRANSLATION = await get_translation(lang=callback.from_user.language_code)

        # Извлекаем адрес кошелька из callback_data
        wallet_address = callback.data.split(":")[1]

        tr_history_from_db = await get_transaction_history_from_db(wallet_address)
        tr_from_db_time_list = [tr.transaction_time async for tr in tr_history_from_db]

        if not tr_from_db_time_list:
            # если в бд нет трансакций то запросим из блокчейна 100 последних
            transaction_limit = transaction_max_limit

        while transaction_max_limit > 0:
            transaction_max_limit -= transaction_limit

            # api.devnet.solana.com выдает ошибку при попытке получить историю трансакций
            if "api.devnet.solana.com" not in SOLANA_NODE_URL:
                # Получаем историю транзакций кошелька по его адресу.
                transaction_history += await get_solana_transaction_history(wallet_address, transaction_id_before, transaction_limit)

            if transaction_history:

                if transaction_history[-1].block_time in tr_from_db_time_list:
                    el_index = tr_from_db_time_list.index(transaction_history[-1].block_time)
                    if (el_index + 1) < len(tr_history_from_db):
                        tr_from_db_tasks = [format_transaction_from_db_message(tr) for tr in tr_history_from_db[el_index + 1:]]
                    break

                else:
                    transaction_id_before = transaction_history[-1].transaction.transaction.signatures[0]

        if transaction_history:
            for tr in transaction_history:
                await save_transaction(tr)

        if transaction_history or tr_from_db_tasks:
            transaction_tasks = [format_transaction_message(transaction) for transaction in transaction_history]
            transaction_tasks += tr_from_db_tasks
            # Используем asyncio.gather для параллельной обработки транзакций
            transaction_messages = await asyncio.gather(*transaction_tasks)
            # Объединяем все сообщения в одну строку с разделителем '\n\n'
            combined_message = '\n\n'.join(transaction_messages)
            await callback.message.answer(combined_message)

        else:
            await callback.answer(TRANSLATION["empty_history"], show_alert=True, reply_markup=None)

        # Очищаем состояние перед завершением
        await state.clear()
        await callback.message.answer(
            TRANSLATION["back_to_main_menu"],
            reply_markup=await get_main_keyboard(lang=callback.from_user.language_code)
        )
        # Отвечаем на callback запрос, чтобы избежать ощущения зависания и исключений
        # await callback.answer()
    except Exception as e:
        detailed_error_traceback = traceback.format_exc()
        logger.error(f"Error in choose_transaction_wallet: {e}\n{detailed_error_traceback}")
        await callback.answer(TRANSLATION["server_unavailable"], show_alert=True, reply_markup=None)
        # Возвращаем пользователя в главное меню
        # await callback.message.delete()
        await callback.message.answer(
            TRANSLATION["back_to_main_menu"],
            reply_markup=await get_main_keyboard(lang=callback.from_user.language_code)
        )
        await state.set_state(default_state)

        await callback.answer()
