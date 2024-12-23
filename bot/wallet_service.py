import traceback
from decimal import Decimal
from typing import Dict, List, Optional, Tuple

from aiogram.enums import ParseMode
from aiogram.fsm.context import FSMContext
from aiogram.types import (BufferedInputFile, CallbackQuery, FSInputFile,
                           URLInputFile)
from django.contrib.auth.models import AbstractUser
from PIL import Image
from spl.token.constants import TOKEN_2022_PROGRAM_ID

from bot.config import LAMPORT_TO_SOL_RATIO
from bot.keyboards import get_main_keyboard, get_wallet_keyboard
from bot.services import get_sol_balance, get_spl_token_data
from bot.states import FSMWallet
from bot.utils import get_translation, get_user
from logger_config import logger
from web.applications.wallet.models import Wallet


async def retrieve_user_wallets(callback: CallbackQuery) -> Tuple[Optional[AbstractUser], List[Wallet]]:
    """
        Retrieves user and user wallets from the database.

        Args:
            callback (CallbackQuery): CallbackQuery object containing information about the call.

        Returns:
            Tuple[Optional[User], List[Wallet]]: User object and list of user's Wallet objects.
    """
    # user = None
    user_wallets = []

    user = await get_user(telegram_id=callback.from_user.id)

    if user:
        async for w in Wallet.objects.filter(user=user):
            user_wallets.append(w)

    return user, user_wallets


async def handle_no_user_or_wallets(callback: CallbackQuery) -> None:
    """
        Handles the case when no user or wallets are found.

        Args:
            callback (CallbackQuery): CallbackQuery object containing information about the call.

        Returns:
            None
    """
    TRANSLATION = await get_translation(lang=callback.from_user.language_code)
    await callback.message.answer(TRANSLATION["no_registered_wallet"])
    await callback.message.answer(
        TRANSLATION["back_to_main_menu"],
        reply_markup=await get_main_keyboard(lang=callback.from_user.language_code)
    )
    # Отвечаем на запрос пользователя, чтобы избежать ощущения зависания
    await callback.answer()


async def process_wallets_command(callback: CallbackQuery, state: FSMContext, action: str) -> None:
    """
        Handles the command related to wallets.

        Args:
            callback (CallbackQuery): CallbackQuery object containing information about the call.
            state (FSMContext): FSMContext object for working with chat states.
            action (str): Action to perform (balance, transfer, transactions).

        Returns:
            None
    """
    try:
        user, user_wallets = await retrieve_user_wallets(callback)

        TRANSLATION = await get_translation(lang=callback.from_user.language_code)

        await callback.message.edit_text(TRANSLATION['list_sender_wallets'])

        if user and user_wallets:
            if action == "balance":

                for i, wallet in enumerate(user_wallets, start=1):
                    balance = await get_sol_balance(wallet.wallet_address)

                    message_text = TRANSLATION['wallet_info_template'].format(
                        number=i,
                        name=wallet.name,
                        address=wallet.wallet_address,
                        balance=balance
                    )

                    spl_tokens_data = await get_spl_token_data(wallet.wallet_address, program_id=TOKEN_2022_PROGRAM_ID)

                    if spl_tokens_data:
                        for token in spl_tokens_data:
                            """ Example data:
                            {'is_native': False, 'state': 'initialized', 'amount': {'amount': '26000000000', 'decimals': 9, 'uiAmount': 26.0, 'uiAmountString': '26'}, 'mint': 'EXw3CfR3am8VqUncm4jyEAMr3EkLSRypDytQUj6wdn5H', 'metadata': {'name': 'MyTestToken1', 'symbol': 'MTT1', 'uri': 'https://raw.githubusercontent.com/o5b/telegram-crypto-wallet-presentation/master/docs/my_test_token_1.json', 'raw': {'name': 'MyTestToken1', 'symbol': 'MTT1', 'description': 'My Test Token 1', 'image': 'https://raw.githubusercontent.com/o5b/telegram-crypto-wallet-presentation/master/docs/imeges/MyTestToken1.png', 'attributes': [{'trait_type': 'Item', 'value': 'Developer Portal'}]}, 'description': 'My Test Token 1', 'image': 'https://raw.githubusercontent.com/o5b/telegram-crypto-wallet-presentation/master/docs/imeges/MyTestToken1.png'}}
                            """
                            name, symbol, amount = '', '', ''
                            if token:
                                if 'metadata' in token:
                                    if 'name' in token['metadata']:
                                        name = token['metadata']['name']
                                    if 'symbol' in token['metadata']:
                                        symbol = token['metadata']['symbol']
                                    # if 'logo' in token['metadata'] and token['metadata']['logo']:
                                    #     logo = token['metadata']['logo']
                                        # with Image.open(token['metadata']['logo']) as img:
                                        #     logo = img.load()
                                         # Отправка файла из файловой системы
                                        # image_from_pc = FSInputFile("image_from_pc.jpg")
                                        # result = await message.answer_photo(
                                        #     image_from_pc,
                                        #     caption="Изображение из файла на компьютере"
                                        # )
                                        # file_ids.append(result.photo[-1].file_id)

                                if 'amount' in token:
                                    if 'uiAmount' in token['amount']:
                                        amount = token['amount']['uiAmount']

                                message_text += TRANSLATION["wallet_info_spl_token_template"].format(
                                    name=name,
                                    # logo=logo,
                                    symbol=symbol,
                                    amount=amount
                                )

                    # await callback.message.answer(message_text, parse_mode=ParseMode.HTML)
                    await callback.message.answer(message_text)

                await callback.message.answer(text=TRANSLATION["back_to_main_menu"], reply_markup=callback.message.reply_markup)
            else:
                # отображаем клавиатуру с выбором кошелька
                wallet_keyboard = await get_wallet_keyboard(user_wallets, lang=user.telegram_language)
                await callback.message.edit_text(TRANSLATION["list_sender_wallets"], reply_markup=wallet_keyboard)
                if action == "transfer":
                    await state.set_state(FSMWallet.transfer_choose_sender_wallet)
                elif action == "transactions":
                    await state.set_state(FSMWallet.choose_transaction_wallet)
                elif action == "delete":
                    await state.set_state(FSMWallet.delete_wallet)
        else:
            await handle_no_user_or_wallets(callback)

        # Отвечаем на callback запрос, чтобы избежать зависания и исключений
        await callback.answer()

    except Exception as error:
        detailed_error_traceback = traceback.format_exc()
        logger.error(f"Error in process_{action}_command: {error}\n{detailed_error_traceback}")


async def format_transaction_message(transaction: Dict) -> str:
    """
       Formats the transaction message.

       Args:
           transaction (dict): Transaction data.

       Returns:
           str: Formatted transaction message.
    """
    amount_in_sol = (transaction.transaction.meta.pre_balances[0] -
                     transaction.transaction.meta.post_balances[0]) / LAMPORT_TO_SOL_RATIO

    # Форматирование суммы в SOL с десятичными знаками
    formatted_amount = '{:.6f}'.format(Decimal(str(amount_in_sol)))

    TRANSLATION = await get_translation(lang='en')

    transaction_message = TRANSLATION["transaction_info"].format(
        transaction_id='{}...{}'.format(
            str(transaction.transaction.transaction.signatures[0])[:4],
            str(transaction.transaction.transaction.signatures[0])[-4:]
        ),

        sender='{}...{}'.format(
            str(transaction.transaction.transaction.message.account_keys[0])[:4],
            str(transaction.transaction.transaction.message.account_keys[0])[-4:]
        ),

        recipient='{}...{}'.format(
            str(transaction.transaction.transaction.message.account_keys[1])[:4],
            str(transaction.transaction.transaction.message.account_keys[1])[-4:]
        ),

        amount_in_sol=formatted_amount
    )

    return transaction_message


async def format_transaction_from_db_message(transaction: Dict) -> str:
    """
       Formats the transaction message.

       Args:
           transaction (dict): Transaction data.

       Returns:
           str: Formatted transaction message.
    """
    amount_in_sol = (transaction.pre_balances - transaction.post_balances) / LAMPORT_TO_SOL_RATIO
    formatted_amount = '{:.6f}'.format(Decimal(str(amount_in_sol)))

    TRANSLATION = await get_translation(lang='en')

    tr_message = TRANSLATION["transaction_info"].format(
        transaction_id='{}...{}'.format(transaction.transaction_id[:4], transaction.transaction_id[-4:]),
        sender='{}...{}'.format(transaction.sender[:4], transaction.sender[-4:]),
        recipient='{}...{}'.format(transaction.recipient[:4], transaction.recipient[-4:]),
        amount_in_sol=formatted_amount
    )

    return tr_message
