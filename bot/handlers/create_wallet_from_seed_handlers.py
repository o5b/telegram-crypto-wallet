import traceback

import mnemonic
from aiogram import Router
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from solders.keypair import Keypair

from bot.keyboards import get_back_keyboard, get_main_keyboard
from bot.states import FSMWallet
from bot.utils import create_wallet_from_seed, get_translation, get_user
from bot.validators import (is_valid_wallet_description, is_valid_wallet_name,
                            is_valid_wallet_seed_phrase)
from logger_config import logger
from web.applications.wallet.models import Wallet

create_wallet_from_seed_router: Router = Router()


@create_wallet_from_seed_router.message(StateFilter(FSMWallet.create_wallet_from_seed_add_seed),
                                        lambda message: message.text and is_valid_wallet_seed_phrase(message.text))
async def process_wallet_seed(message: Message, state: FSMContext) -> None:
    """
        Handler for entering the wallet seed phrase.

        Args:
            message (Message): The incoming message.
            state (FSMContext): The state of the finite state machine.

        Returns:
            None
    """
    try:
        seed_phrase = message.text
        await state.update_data(seed_phrase=seed_phrase)
        data = await state.get_data()
        seed_phrase = data.get("seed_phrase")

        TRANSLATION = await get_translation(lang=message.from_user.language_code)

        await message.answer(text=TRANSLATION["wallet_seed_confirmation"].format(seed_phrase=seed_phrase))
        await message.answer(
            text=TRANSLATION["create_name_wallet"],
            reply_markup=await get_back_keyboard(lang=message.from_user.language_code)
        )
        await state.set_state(FSMWallet.create_wallet_from_seed_add_name)
    except Exception as e:
        detailed_error_traceback = traceback.format_exc()
        logger.error(f"Error in process_wallet_seed: {e}\n{detailed_error_traceback}")


@create_wallet_from_seed_router.message(StateFilter(FSMWallet.create_wallet_from_seed_add_seed))
async def process_invalid_wallet_seed(message: Message, state: FSMContext) -> None:
    """
        Handler for incorrect wallet seed input.

        Args:
            message (Message): The incoming message.
            state (FSMContext): The state of the finite state machine.

        Returns:
            None
    """
    try:
        TRANSLATION = await get_translation(lang=message.from_user.language_code)
        await message.answer(text=TRANSLATION["invalid_wallet_seed"])
        # Запрашиваем ввод имени кошелька заново
        await message.answer(
            text=TRANSLATION["create_seed_wallet"],
            reply_markup=await get_back_keyboard(lang=message.from_user.language_code)
        )
    except Exception as e:
        detailed_error_traceback = traceback.format_exc()
        logger.error(f"Error in process_invalid_wallet_seed: {e}\n{detailed_error_traceback}")


@create_wallet_from_seed_router.message(StateFilter(FSMWallet.create_wallet_from_seed_add_name),
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
        await state.update_data(wallet_name=message.text)
        data = await state.get_data()
        name = data.get("wallet_name")
        TRANSLATION = await get_translation(lang=message.from_user.language_code)
        await message.answer(text=TRANSLATION["wallet_name_confirmation"].format(wallet_name=name))
        await message.answer(
            text=TRANSLATION["create_description_wallet"],
            reply_markup=await get_back_keyboard(lang=message.from_user.language_code)
        )
        await state.set_state(FSMWallet.create_wallet_from_seed_add_description)
    except Exception as e:
        detailed_error_traceback = traceback.format_exc()
        logger.error(f"Error in process_wallet_name: {e}\n{detailed_error_traceback}")


@create_wallet_from_seed_router.message(StateFilter(FSMWallet.create_wallet_from_seed_add_name))
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
        await message.answer(text=TRANSLATION["invalid_wallet_name"])
        await message.answer(
            text=TRANSLATION["create_name_wallet"],
            reply_markup=await get_back_keyboard(lang=message.from_user.language_code)
        )
    except Exception as e:
        detailed_error_traceback = traceback.format_exc()
        logger.error(f"Error in process_invalid_wallet_name: {e}\n{detailed_error_traceback}")


@create_wallet_from_seed_router.message(StateFilter(FSMWallet.create_wallet_from_seed_add_description),
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
        await state.update_data(description=message.text)
        data = await state.get_data()
        seed_phrase = data.get("seed_phrase")
        name = data.get("wallet_name")
        description = data.get("description")
        index = 0

        user = await get_user(telegram_id=message.from_user.id)

        TRANSLATION = await get_translation(lang=message.from_user.language_code)

        user_wallets = []

        async for w in Wallet.objects.filter(user=user):
            user_wallets.append(w.wallet_address)

        if user.last_solana_derivation_path:
            derivation_path = user.last_solana_derivation_path
            list_from_derivation_path = derivation_path.split('/')
            last_el = list_from_derivation_path[-1]
            index = int(last_el[0]) + 1

        while True:
            derivation_path = f"m/44'/501'/0'/{index}'"

            mnemo = mnemonic.Mnemonic("english")
            seed = mnemo.to_seed(seed_phrase, passphrase="")
            keypair = Keypair.from_seed_and_derivation_path(seed, derivation_path)
            wallet_address = str(keypair.pubkey())
            private_key = keypair.secret().hex()

            if wallet_address not in user_wallets:
                break
            else:
                index += 1

        wallet = await create_wallet_from_seed(
            user=user,
            name=name,
            description=description,
            wallet_address=wallet_address,
            derivation_path=derivation_path,
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
        await message.answer(
            TRANSLATION["back_to_main_menu"],
            reply_markup=await get_main_keyboard(lang=message.from_user.language_code)
        )
    except Exception as e:
        detailed_error_traceback = traceback.format_exc()
        logger.error(f"Error in process_wallet_description: {e}\n{detailed_error_traceback}")


@create_wallet_from_seed_router.message(StateFilter(FSMWallet.create_wallet_from_seed_add_description))
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
        await message.answer(
            text=TRANSLATION["create_description_wallet"],
            reply_markup=await get_back_keyboard(lang=message.from_user.language_code)
        )
    except Exception as e:
        detailed_error_traceback = traceback.format_exc()
        logger.error(f"Error in process_invalid_wallet_description: {e}\n{detailed_error_traceback}")
