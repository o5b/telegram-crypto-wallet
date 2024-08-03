import traceback

from aiogram import Router
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from bot.keyboards import get_back_keyboard, get_main_keyboard
from bot.services import create_solana_wallet, is_valid_wallet_address
from bot.states import FSMWallet
from bot.utils import create_wallet, get_translation, get_user
from bot.validators import is_valid_wallet_description, is_valid_wallet_name
from logger_config import logger
from web.applications.wallet.models import HDWallet, Wallet

create_wallet_router: Router = Router()


@create_wallet_router.message(StateFilter(FSMWallet.create_wallet_add_name),
                              lambda message: message.text and is_valid_wallet_name(message.text))
async def process_wallet_name(message: Message, state: FSMContext) -> None:
    """
        Handler for entering the wallet name.

        Args:
            message (Message): The incoming message.
            state (FSMContext): The state of the finite state machine.

        Returns:
            None
    """
    try:
        # Сохраняем введенное имя кошелька в состояние
        await state.update_data(wallet_name=message.text)

        # Получаем данные из состояния
        data = await state.get_data()

        # Извлекаем имя кошелька из данных
        name = data.get("wallet_name")

        TRANSLATION = await get_translation(lang=message.from_user.language_code)
        # Отправляем подтверждение с введенным именем кошелька
        await message.answer(text=TRANSLATION["wallet_name_confirmation"].format(wallet_name=name))

        # Запрашиваем ввод описания кошелька
        await message.answer(
            text=TRANSLATION["create_description_wallet"],
            reply_markup=await get_back_keyboard(lang=message.from_user.language_code)
        )

        # Переходим к добавлению описания кошелька
        await state.set_state(FSMWallet.create_wallet_add_description)
    except Exception as e:
        detailed_error_traceback = traceback.format_exc()
        logger.error(f"Error in process_wallet_name: {e}\n{detailed_error_traceback}")


@create_wallet_router.message(StateFilter(FSMWallet.create_wallet_add_name))
async def process_invalid_wallet_name(message: Message, state: FSMContext) -> None:
    """
        Handler for incorrect wallet name input.

        Args:
            message (Message): The incoming message.
            state (FSMContext): The state of the finite state machine.

        Returns:
            None
    """
    try:
        TRANSLATION = await get_translation(lang=message.from_user.language_code)
        # Отправляем сообщение о некорректном имени кошелька
        await message.answer(text=TRANSLATION["invalid_wallet_name"])

        # Запрашиваем ввод имени кошелька заново
        await message.answer(
            text=TRANSLATION["create_name_wallet"],
            reply_markup=await get_back_keyboard(lang=message.from_user.language_code)
        )
    except Exception as e:
        detailed_error_traceback = traceback.format_exc()
        logger.error(f"Error in process_invalid_wallet_name: {e}\n{detailed_error_traceback}")


@create_wallet_router.message(StateFilter(FSMWallet.create_wallet_add_description),
                              lambda message: message.text and is_valid_wallet_description(message.text))
async def process_wallet_description(message: Message, state: FSMContext) -> None:
    """
        Handles the user input of the wallet description during creation.

        Args:
            message (Message): The user message containing the wallet description.
            state (FSMContext): The state context for managing chat states.

        Returns:
            None
    """
    try:
        # Обновляем данные состояния, добавляя введенное описание
        await state.update_data(description=message.text)
        # Получаем данные из состояния
        data = await state.get_data()
        # Извлекаем имя кошелька из данных
        name = data.get("wallet_name")
        # Извлекаем описание кошелька из данных
        description = data.get("description")

        user = await get_user(telegram_id=message.from_user.id)

        TRANSLATION = await get_translation(lang=message.from_user.language_code)

        wallet = None

        wallet_address, private_key, seed_phrase = await create_solana_wallet()

        wallet = await create_wallet(
            user=user,
            wallet_address=wallet_address,
            name=name,
            description=description,
            derivation_path = "m/44'/501'/0'/0'",
        )

        if wallet:
            await state.update_data(sender_address=wallet.wallet_address, sender_private_key=private_key)

        # Если адреса кошелька нет, выводим сообщение об успешном создании и возвращаемся в главное меню
        await message.answer(
            TRANSLATION["wallet_created_successfully"].format(wallet_name=wallet.name,
                                                          wallet_description=wallet.description,
                                                          wallet_address=wallet.wallet_address,
                                                          private_key=private_key,
                                                          seed_phrase=seed_phrase))
        # Очищаем состояние после добавления кошелька
        await state.clear()
        # Отправляем сообщение с предложением продолжить и клавиатурой основного меню
        await message.answer(
            TRANSLATION["back_to_main_menu"],
            reply_markup=await get_main_keyboard(lang=message.from_user.language_code)
        )
    except Exception as e:
        detailed_error_traceback = traceback.format_exc()
        logger.error(f"Error in process_wallet_description: {e}\n{detailed_error_traceback}")


@create_wallet_router.message(StateFilter(FSMWallet.create_wallet_add_description))
async def process_invalid_wallet_description(message: Message, state: FSMContext) -> None:
    """
        Handler for invalid wallet description input.

        Args:
            message (Message): The incoming message.
            state (FSMContext): The state of the finite state machine.

        Returns:
            None
    """
    try:
        TRANSLATION = await get_translation(lang=message.from_user.language_code)
        # Отправляем сообщение о недопустимом описании кошелька
        await message.answer(text=TRANSLATION["invalid_wallet_description"])
        # Запрашиваем ввод описания кошелька еще раз
        await message.answer(
            text=TRANSLATION["create_description_wallet"],
            reply_markup=await get_back_keyboard(lang=message.from_user.language_code))
    except Exception as e:
        detailed_error_traceback = traceback.format_exc()
        logger.error(f"Error in process_invalid_wallet_description: {e}\n{detailed_error_traceback}")
