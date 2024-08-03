import traceback

from aiogram import Router
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from bot.keyboards import get_back_keyboard, get_main_keyboard
from bot.services import is_valid_wallet_address
from bot.states import FSMWallet
from bot.utils import connect_wallet, get_translation, get_user
from bot.validators import is_valid_wallet_description, is_valid_wallet_name
from logger_config import logger
from web.applications.wallet.models import Wallet

connect_wallet_router: Router = Router()


@connect_wallet_router.message(StateFilter(FSMWallet.connect_wallet_add_address))
async def process_connect_wallet_address(message: Message, state: FSMContext) -> None:
    """
        Handler for entering the wallet address for connection.

        Args:
            message (Message): The incoming message.
            state (FSMContext): The state of the finite state machine.

        Returns:
            None
    """
    try:
        wallet_address = message.text

        TRANSLATION = await get_translation(lang=message.from_user.language_code)

        if is_valid_wallet_address(wallet_address):
            user = await get_user(telegram_id=message.from_user.id)
            user_wallets = []

            async for w in Wallet.objects.filter(user=user):
                user_wallets.append(w.wallet_address)

            if wallet_address in user_wallets:
                await message.answer(TRANSLATION["this_wallet_already_exists"].format(wallet_address=wallet_address))
                await message.answer(
                    TRANSLATION["connect_wallet_address"],
                    reply_markup=await get_back_keyboard(lang=message.from_user.language_code)
                )
            else:
                await state.update_data(wallet_address=wallet_address)
                await message.answer(
                    TRANSLATION["connect_wallet_add_name"],
                    reply_markup=await get_back_keyboard(lang=message.from_user.language_code)
                )
                await state.set_state(FSMWallet.connect_wallet_add_name)

        else:
            await message.answer(TRANSLATION["invalid_wallet_address"])
            await message.answer(
                TRANSLATION["connect_wallet_address"],
                reply_markup=await get_back_keyboard(lang=message.from_user.language_code)
            )

    except Exception as e:
        detailed_error_traceback = traceback.format_exc()
        logger.error(f"Error in process_connect_wallet_address: {e}\n{detailed_error_traceback}")


@connect_wallet_router.message(StateFilter(FSMWallet.connect_wallet_add_name),
                               lambda message: is_valid_wallet_name(message.text))
async def process_connect_wallet_name(message: Message, state: FSMContext) -> None:
    """
        Handler for entering the wallet name.

        Args:
            message (Message): The incoming message.
            state (FSMContext): The state of the finite state machine.

        Returns:
            None
    """
    try:
        await state.update_data(wallet_name=message.text)

        data = await state.get_data()
        name = data.get("wallet_name")

        TRANSLATION = await get_translation(lang=message.from_user.language_code)

        await message.answer(text=TRANSLATION["wallet_name_confirmation"].format(wallet_name=name))
        await message.answer(
            text=TRANSLATION["connect_wallet_add_description"],
            reply_markup=await get_back_keyboard(lang=message.from_user.language_code)
        )
        await state.set_state(FSMWallet.connect_wallet_add_description)
    except Exception as e:
        detailed_error_traceback = traceback.format_exc()
        logger.error(f"Error in process_connect_wallet_name: {e}\n{detailed_error_traceback}")


@connect_wallet_router.message(StateFilter(FSMWallet.connect_wallet_add_name))
async def process_invalid_connect_wallet_name(message: Message, state: FSMContext) -> None:
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
        await message.answer(text=TRANSLATION["invalid_wallet_name"])
        await message.answer(text=TRANSLATION["wallet_name_prompt"])
    except Exception as e:
        detailed_error_traceback = traceback.format_exc()
        logger.error(f"Error in process_invalid_wallet_name: {e}\n{detailed_error_traceback}")


@connect_wallet_router.message(StateFilter(FSMWallet.connect_wallet_add_description),
                               lambda message: is_valid_wallet_description(message.text))
async def process_connect_wallet_description(message: Message, state: FSMContext) -> None:
    """
        Handles the user input of the wallet description during connection.

        Args:
            message (Message): The user message containing the wallet description.
            state (FSMContext): The state context for managing chat states.

        Returns:
            None
    """
    try:
        await state.update_data(description=message.text)
        data = await state.get_data()
        name = data.get("wallet_name")
        description = data.get("description")
        wallet_address = data.get("wallet_address")

        user = await get_user(telegram_id=message.from_user.id)

        user_language = message.from_user.language_code

        TRANSLATION = await get_translation(lang=user_language)

        wallet = await connect_wallet(
            user=user,
            wallet_address=wallet_address,
            name=name,
            description=description,
        )

        if wallet:
            await message.answer(TRANSLATION["wallet_connected_successfully"].format(wallet_address=wallet.wallet_address))

        await state.clear()
        print
        await message.answer(
            TRANSLATION["back_to_main_menu"],
            reply_markup=await get_main_keyboard(lang=user_language)
        )

    except Exception as e:
        detailed_error_traceback = traceback.format_exc()
        logger.error(f"Error in process_connect_wallet_description: {e}\n{detailed_error_traceback}")


@connect_wallet_router.message(StateFilter(FSMWallet.connect_wallet_add_description))
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
        await message.answer(text=TRANSLATION["invalid_wallet_description"])
        await message.answer(text=TRANSLATION["wallet_description_prompt"])
    except Exception as e:
        detailed_error_traceback = traceback.format_exc()
        logger.error(f"Error in process_invalid_wallet_description: {e}\n{detailed_error_traceback}")
