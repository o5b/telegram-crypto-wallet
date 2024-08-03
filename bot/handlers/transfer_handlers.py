import asyncio
import traceback
from decimal import Decimal

import solana.rpc.core
from aiogram import F, Router
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from mnemonic import Mnemonic
from solders.keypair import Keypair

from bot.config import LAMPORT_TO_SOL_RATIO
from bot.keyboards import (get_back_keyboard, get_main_keyboard,
                           get_token_keyboard)
from bot.services import (get_sol_balance, get_spl_token_data,
                          get_wallet_address_from_private_key, http_client,
                          is_valid_amount, is_valid_private_key,
                          is_valid_wallet_address, transfer_sol_token,
                          transfer_spl_token)
from bot.states import FSMWallet
from bot.utils import get_token, get_translation, get_wallet, update_wallet
from bot.validators import is_valid_wallet_seed_phrase
from logger_config import logger

transfer_router: Router = Router()


@transfer_router.callback_query(F.data.startswith("wallet_address:"),
                                StateFilter(FSMWallet.transfer_choose_sender_wallet))
async def process_choose_sender_wallet(callback: CallbackQuery, state: FSMContext) -> None:
    """
        Handles the user's selection of the sender wallet for transfer.

        Args:
            callback (CallbackQuery): The callback query object containing data about the selected wallet.
            state (FSMContext): The state context for working with chat states.

        Returns:
            None
    """
    try:
        TRANSLATION = await get_translation(lang=callback.from_user.language_code)
        wallet_address = callback.data.split(":")[1]
        wallet = await get_wallet(wallet_address=wallet_address)

        await state.update_data(
            sender_address=wallet.wallet_address,
            derivation_path=wallet.derivation_path,
        )

        await callback.message.edit_text(
            TRANSLATION["transfer_sender_private_key_prompt"],
            reply_markup=await get_back_keyboard(lang=callback.from_user.language_code)
        )

        await state.set_state(FSMWallet.transfer_sender_private_key)

        # Избегаем ощущения, что бот завис, избегаем исключение - если два раза подряд нажать на одну и ту же кнопку
        await callback.answer()
    except Exception as e:
        detailed_error_traceback = traceback.format_exc()
        logger.error(f"Error in process_choose_sender_wallet: {e}\n{detailed_error_traceback}")


@transfer_router.message(StateFilter(FSMWallet.transfer_sender_private_key))
async def process_transfer_sender_private_key(message: Message, state: FSMContext) -> None:
    """
        Handles the user input of the sender's private key.

        Args:
            message (Message): The user message containing the sender's private key.
            state (FSMContext): The state context for managing chat states.

        Returns:
            None
    """
    try:
        private_key = ''
        seed_phrase = ''
        message_text = message.text.strip()
        data = await state.get_data()
        sender_address = data.get("sender_address")
        derivation_path = data.get("derivation_path")

        TRANSLATION = await get_translation(lang=message.from_user.language_code)

        if message_text:
            if len(message_text.split()) == 1:
                private_key = message_text
            elif len(message_text.split()) in [12, 24]:
                seed_phrase = message_text

        if seed_phrase:
            if is_valid_wallet_seed_phrase(seed_phrase):
                mnemo = Mnemonic("english")
                seed = mnemo.to_seed(seed_phrase, passphrase="")
                if derivation_path:
                    keypair = Keypair.from_seed_and_derivation_path(seed, derivation_path)
                    private_key = keypair.secret().hex()
                else:
                    for i in range(100):
                        derivation_path = f"m/44'/501'/0'/{i}'"
                        i += 1
                        keypair = Keypair.from_seed_and_derivation_path(seed, derivation_path)
                        address = str(keypair.pubkey())
                        if address == sender_address:
                            private_key = keypair.secret().hex()
                            await update_wallet(sender_address, derivation_path)
                            break

                    if not private_key:
                        logger.error("Could not get the private_key from this seed phrase")
                        return None

            else:
                sent_message = await message.answer(TRANSLATION["invalid_seed_phrase"], reply_markup=None)
                await asyncio.sleep(1)
                await message.delete()
                await sent_message.delete()
                await message.answer(
                    TRANSLATION["transfer_sender_private_key_prompt"],
                    reply_markup=await get_back_keyboard(lang=message.from_user.language_code)
                )

        if is_valid_private_key(private_key):
            sender_address_from_keypair = get_wallet_address_from_private_key(private_key)

            if sender_address == sender_address_from_keypair:
                await state.update_data(sender_private_key=private_key)
                await message.answer(
                    TRANSLATION["transfer_recipient_address_prompt"],
                    reply_markup=await get_back_keyboard(lang=message.from_user.language_code)
                )
                await state.set_state(FSMWallet.transfer_recipient_address)
            else:
                sent_message = await message.answer(TRANSLATION["invalid_private_key"], reply_markup=None)
                await asyncio.sleep(1)
                await message.delete()
                await sent_message.delete()
                await message.answer(
                    TRANSLATION["transfer_sender_private_key_prompt"],
                    reply_markup=await get_back_keyboard(lang=message.from_user.language_code)
                )
                # или
                # await message.answer(TRANSLATION["invalid_private_key"])
                # await message.answer(TRANSLATION["transfer_sender_private_key_prompt"], reply_markup=back_keyboard)
        else:
            sent_message = await message.answer(TRANSLATION["invalid_private_key"], reply_markup=None)
            await asyncio.sleep(1)
            await message.delete()
            await sent_message.delete()
            await message.answer(
                TRANSLATION["transfer_sender_private_key_prompt"],
                reply_markup=await get_back_keyboard(lang=message.from_user.language_code)
            )
            # или
            # await message.answer(TRANSLATION["invalid_private_key"])
            # await message.answer(TRANSLATION["transfer_sender_private_key_prompt"], reply_markup=back_keyboard)

    except Exception as e:
        detailed_error_traceback = traceback.format_exc()
        logger.error(f"Error in process_transfer_sender_private_key: {e}\n{detailed_error_traceback}")


@transfer_router.message(StateFilter(FSMWallet.transfer_recipient_address))
async def process_transfer_recipient_address(message: Message, state: FSMContext) -> None:
    """
        Handles the input of the recipient address for the transfer.

        Args:
            message (Message): The message object containing the recipient address entered by the user.
            state (FSMContext): The state context for working with chat states.

        Raises:
            Exception: If an error occurs while processing the request.

        Returns:
            None
    """
    try:
        recipient_address = message.text
        data = await state.get_data()
        sender_address = data.get("sender_address")

        TRANSLATION = await get_translation(lang=message.from_user.language_code)

        if is_valid_wallet_address(recipient_address):
            await state.update_data(recipient_address=recipient_address)
            await message.answer(
                TRANSLATION["list_sender_tokens"],
                reply_markup=await get_token_keyboard(sender_address, lang=message.from_user.language_code)
            )
            await state.set_state(FSMWallet.transfer_token)
        else:
            # Если адрес получателя невалиден, отправляем сообщение с просьбой ввести корректный адрес.
            sent_message = await message.answer(TRANSLATION["invalid_wallet_address"], reply_markup=None)
            await asyncio.sleep(1)
            await message.delete()
            await sent_message.delete()
            await message.answer(
                TRANSLATION["transfer_recipient_address_prompt"],
                reply_markup=await get_back_keyboard(lang=message.from_user.language_code)
            )

    except Exception as error:
        detailed_error_traceback = traceback.format_exc()
        logger.error(f"Error in process_transfer_recipient_address: {error}\n{detailed_error_traceback}")


@transfer_router.callback_query(F.data, StateFilter(FSMWallet.transfer_token))
async def process_choose_sender_token(callback: CallbackQuery, state: FSMContext) -> None:
    try:
        callback_data = callback.data.split("_")
        print(f'******* callback_data: {callback_data}')
        data = await state.get_data()

        TRANSLATION = await get_translation(lang=callback.from_user.language_code)

        print('******** process_transfer_token >> state data: ', data)
        await state.update_data(token_type=callback_data[0], sol_balance=callback_data[1])

        if callback_data[0] == 'spl' and len(callback_data) == 4:
            await state.update_data(spl_balance=callback_data[2], mint=callback_data[3])

        await callback.message.edit_text(
            TRANSLATION["transfer_amount_prompt"],
            reply_markup=await get_back_keyboard(lang=callback.from_user.language_code)
        )
        await state.set_state(FSMWallet.transfer_amount)

        # Избегаем ощущения, что бот завис, избегаем исключение - если два раза подряд нажать на одну и ту же кнопку
        await callback.answer()

    except Exception as error:
        detailed_error_traceback = traceback.format_exc()
        logger.error(f"Error in process_transfer_token: {error}\n{detailed_error_traceback}")


@transfer_router.message(StateFilter(FSMWallet.transfer_amount))
async def process_transfer_amount(message: Message, state: FSMContext) -> None:
    """
        Handles the user's input of the transfer amount in the transfer process.

        Args:
            message (Message): The message object containing the amount entered by the user.
            state (FSMContext): The state context for working with chat states.

        Raises:
            Exception: If an error occurs while processing the request.

        Returns:
            None
    """
    try:
        TRANSLATION = await get_translation(lang=message.from_user.language_code)
        # Преобразуем текст сообщения, содержащий сумму перевода, в строку, чтобы можно было заменить запятые на точки,
        # если они присутствуют.
        amount_text = str(message.text).replace(',', '.')
        if not is_valid_amount(amount_text):
            raise ValueError

        amount = float(amount_text)
        data = await state.get_data()
        print('********  process_transfer_amount >> data: ', data)
        sender_address = data.get("sender_address")
        sender_private_key = data.get("sender_private_key")
        recipient_address = data.get("recipient_address")
        token_type = data.get('token_type')
        sol_balance_text = data.get('sol_balance')

        if not sol_balance_text or not is_valid_amount(sol_balance_text):
            raise ValueError

        sol_balance = float(sol_balance_text)

        spl_balance = data.get('spl_balance')

        if spl_balance and is_valid_amount(spl_balance):
            spl_balance = float(spl_balance)

        mint = data.get('mint')

        try:
            # Запрашиваем минимальный баланс для освобождения от аренды.
            # Аргумент функции - размер данных в байтах, для которых требуется выделить место в памяти.
            min_sol_balance_resp = (await http_client.get_minimum_balance_for_rent_exemption(1)).value
            # Извлекаем значение минимального баланса из ответа. Min balance: 897840lamports/1000000000 = 0.00089784 Sol
            min_sol_balance = min_sol_balance_resp / LAMPORT_TO_SOL_RATIO
            logger.debug(f"Token type: {token_type}, SOL balance: {sol_balance}, Min balance: {min_sol_balance}, Spl balance: {spl_balance}, Amount: {amount}")

        except Exception as error:
            detailed_error_traceback = traceback.format_exc()
            logger.error(f"Error getting balance or minimum balance: {error}\n{detailed_error_traceback}")

            # Отправляем пользователю сообщение о недостаточном балансе и запрос на ввод суммы для перевода.
            sent_message = await message.answer(TRANSLATION["insufficient_balance"], reply_markup=None)
            await asyncio.sleep(1)
            await message.delete()
            await sent_message.delete()
            await message.answer(
                TRANSLATION["transfer_amount_prompt"],
                reply_markup=await get_back_keyboard(lang=message.from_user.language_code)
            )
            # или
            # await message.answer(TRANSLATION["insufficient_balance"])
            # await message.answer(TRANSLATION["transfer_amount_prompt"])

            # Возвращаемся из функции, чтобы предотвратить дальнейшее выполнение кода.
            return None

        print(f'**** balance={sol_balance}, amount={amount}, min_balance={min_sol_balance}')
        if token_type == 'sol':
            if sol_balance >= amount + min_sol_balance:
                result = await transfer_sol_token(
                    sender_address,
                    sender_private_key,
                    recipient_address,
                    mint,
                    amount,
                    http_client,
                )

                if result:
                    formatted_amount = '{:.6f}'.format(Decimal(str(amount)))
                    await message.answer(
                        TRANSLATION["transfer_successful"].format(amount=formatted_amount, recipient=recipient_address))
                else:
                    await message.answer(
                        TRANSLATION["transfer_not_successful"].format(amount=amount, recipient=recipient_address))

            else:
                # Отправляем пользователю сообщение о недостаточном балансе и запрос на ввод суммы для перевода.
                sent_message = await message.answer(TRANSLATION["insufficient_balance"], reply_markup=None)
                await asyncio.sleep(3)
                await message.delete()
                await sent_message.delete()
                await message.answer(
                    TRANSLATION["transfer_amount_prompt"],
                    reply_markup=await get_back_keyboard(lang=message.from_user.language_code)
                )
                # или
                # await message.answer(TRANSLATION["insufficient_balance"])
                # await message.answer(TRANSLATION["transfer_amount_prompt"])
                # Выходим из функции после вывода сообщений
                return

        elif token_type == 'spl':
            if (sol_balance >= min_sol_balance) and spl_balance and spl_balance >= amount:
                token = await get_token(mint_account=mint)
                if token:
                    result = await transfer_spl_token(
                        sender_address=sender_address,
                        sender_private_key=sender_private_key,
                        recipient_address=recipient_address,
                        mint=mint,
                        amount=amount,
                        decimals=token.decimals,
                    )
                    if result:
                        formatted_amount = '{:.6f}'.format(Decimal(str(amount)))
                        await message.answer(
                            TRANSLATION["transfer_successful"].format(amount=formatted_amount, recipient=recipient_address))
                    else:
                        await message.answer(
                            TRANSLATION["transfer_not_successful"].format(amount=amount, recipient=recipient_address))

            # Если баланс отправителя недостаточен для перевода (включая минимальный баланс).
            else:
                # Отправляем пользователю сообщение о недостаточном балансе и запрос на ввод суммы для перевода.
                sent_message = await message.answer(TRANSLATION["insufficient_balance"], reply_markup=None)
                await message.answer(
                    TRANSLATION["transfer_amount_prompt"],
                    reply_markup=await get_back_keyboard(lang=message.from_user.language_code)
                )
                # или
                # await message.answer(TRANSLATION["insufficient_balance"])
                # await message.answer(TRANSLATION["transfer_amount_prompt"])
                # Выходим из функции после вывода сообщений
                return

        # Очищаем состояние перед завершением.
        await state.clear()
        await message.answer(
            TRANSLATION["back_to_main_menu"],
            reply_markup=await get_main_keyboard(lang=message.from_user.language_code)
        )

    # Если возникает ошибка типа ValueError, когда пользователь вводит некорректную сумму.
    except ValueError:
        # Отправляем сообщение о неверной сумме и просим пользователя ввести сумму для перевода заново.
        sent_message = await message.answer(TRANSLATION["invalid_amount"], reply_markup=None)
        await asyncio.sleep(1)
        await message.delete()
        await sent_message.delete()
        await message.answer(TRANSLATION["transfer_amount_prompt"])
    except solana.rpc.core.RPCException as rpc_exception:
        # Проверяем, является ли ошибка связанной с недостаточным балансом для аренды.
        if "InsufficientFundsForRent" in str(rpc_exception):
            # Отправляем сообщение пользователю о нехватке баланса для аренды.
            sent_message = await message.answer(TRANSLATION["insufficient_balance_recipient"], reply_markup=None)
            await asyncio.sleep(1)
            await message.delete()
            await sent_message.delete()
            await message.answer(TRANSLATION["transfer_recipient_address_prompt"])
            # Устанавливаем состояние transfer_recipient_address для возврата к запросу адреса получателя.
            await state.set_state(FSMWallet.transfer_recipient_address)
        else:
            logger.error(f"Error during token transfer: {rpc_exception}")
            await message.answer("An error occurred during the token transfer. Please try again later.")
