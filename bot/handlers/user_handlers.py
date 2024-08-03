import traceback

from aiogram import F, Router
from aiogram.filters import Command, CommandStart, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import default_state
from aiogram.types import CallbackQuery, Message

from bot.config import SOLANA_NODE_URL
from bot.keyboards import get_main_keyboard
from bot.states import FSMWallet
from bot.utils import get_translation, update_or_create_user
from bot.wallet_service import process_wallets_command
from logger_config import logger

user_router: Router = Router()


@user_router.message(CommandStart(), StateFilter(default_state))
async def process_start_command(message: Message, state: FSMContext) -> None:
    """
        Handler for the start bot command.

        Args:
            message (Message): The incoming message.
            state (FSMContext): The state of the finite state machine.

        Returns:
            None
    """
    try:
        user_data = {
            'username': '{}'.format(message.from_user.id),
            'telegram_language': message.from_user.language_code or 'en',
            'telegram_username': message.from_user.username[:64] if message.from_user.username else '',
            'first_name': message.from_user.first_name[:60] if message.from_user.first_name else '',
            'last_name': message.from_user.last_name[:60] if message.from_user.last_name else '',
            'is_bot': 'Yes' if message.from_user.is_bot else 'No',
            'raw_data': message.from_user.dict(),
        }

        user, created = await update_or_create_user(telegram_id=message.from_user.id, defaults=user_data)
        TRANSLATION = await get_translation(lang=message.from_user.language_code)

        await message.answer(
            TRANSLATION["/start"].format(first_name=message.from_user.first_name, node=SOLANA_NODE_URL),
            reply_markup=await get_main_keyboard(lang=message.from_user.language_code),
        )

    except Exception as e:
        detailed_send_message_error = traceback.format_exc()
        logger.error(f"Error in process_start_command: {e}\n{detailed_send_message_error}")


@user_router.message(Command(commands='help'), StateFilter(default_state))
async def process_help_command(message: Message, state: FSMContext) -> None:
    """
        Handler for the "/help" command.

        Args:
            message (Message): The incoming message.
            state (FSMContext): The state of the finite state machine.

        Returns:
            None
    """
    try:
        TRANSLATION = await get_translation(lang=message.from_user.language_code)
        await message.answer(TRANSLATION["/help"])
        await message.answer(
            TRANSLATION["back_to_main_menu"],
            reply_markup=await get_main_keyboard(lang=message.from_user.language_code)
        )
    except Exception as e:
        detailed_send_message_error = traceback.format_exc()
        logger.error(f"Error in process_create_wallet_command: {e}\n{detailed_send_message_error}")


@user_router.message(~CommandStart(), ~Command(commands='help'), StateFilter(default_state))
async def process_unexpected_input(message: Message) -> None:
    """
        Handler for unexpected messages in the default_state.

        Args:
            message (Message): Incoming message.

        Returns:
            None
    """
    try:
        TRANSLATION = await get_translation(lang=message.from_user.language_code)
        # Проверяем, может ли бот редактировать сообщения
        if message.chat.type == 'private':  # Проверяем, что чат является приватным
            if message.text:
                await message.answer(TRANSLATION["unexpected_input"])
            else:
                logger.warning("Received message without text. Cannot edit.")
        else:
            logger.warning("Received message in a non-private chat. Cannot edit.")
    except Exception as error:
        detailed_send_message_error = traceback.format_exc()
        logger.error(f"Error in process_unexpected_input: {error}\n{detailed_send_message_error}")


@user_router.callback_query(F.data == "callback_button_create_wallet", StateFilter(default_state))
async def process_create_wallet_command(callback: CallbackQuery, state: FSMContext) -> None:
    """
        Handler for selecting the "Create Wallet" option from the menu.

        Args:
            callback (CallbackQuery): The callback object.
            state (FSMContext): The state of the finite state machine.

        Returns:
            None
    """
    try:
        TRANSLATION = await get_translation(lang=callback.from_user.language_code)
        await callback.message.edit_text(TRANSLATION["create_name_wallet"])
        await state.set_state(FSMWallet.create_wallet_add_name)
        # Избегаем ощущения, что бот завис и избегаем исключение - если два раза подряд нажать на одну и ту же кнопку
        await callback.answer()
    except Exception as error:
        detailed_send_message_error = traceback.format_exc()
        logger.error(f"Error in process_create_wallet_command: {error}\n{detailed_send_message_error}")


@user_router.callback_query(F.data == "callback_button_create_wallet_from_seed", StateFilter(default_state))
async def process_create_wallet_from_seed_command(callback: CallbackQuery, state: FSMContext) -> None:
    """
        Handler for selecting the "Create Wallet From Seed" option from the menu.

        Args:
            callback (CallbackQuery): The callback object.
            state (FSMContext): The state of the finite state machine.

        Returns:
            None
    """
    try:
        TRANSLATION = await get_translation(lang=callback.from_user.language_code)
        await callback.message.edit_text(TRANSLATION["create_seed_wallet"])
        await state.set_state(FSMWallet.create_wallet_from_seed_add_seed)
        # Избегаем ощущения, что бот завис и избегаем исключение - если два раза подряд нажать на одну и ту же кнопку
        await callback.answer()
    except Exception as error:
        detailed_send_message_error = traceback.format_exc()
        logger.error(f"Error in process_create_wallet_from_seed_command: {error}\n{detailed_send_message_error}")


@user_router.callback_query(F.data == "callback_button_connect_wallet", StateFilter(default_state))
async def process_connect_wallet_command(callback: CallbackQuery, state: FSMContext) -> None:
    """
        Handler for selecting the "Connect Wallet" option from the menu.

        Args:
            callback (CallbackQuery): The callback object.
            state (FSMContext): The state of the finite state machine.

        Returns:
            None
    """
    try:
        TRANSLATION = await get_translation(lang=callback.from_user.language_code)
        await callback.message.edit_text(TRANSLATION["connect_wallet_address"])
        await state.set_state(FSMWallet.connect_wallet_add_address)
        # Избегаем ощущения, что бот завис и избегаем исключение - если два раза подряд нажать на одну и ту же кнопку
        await callback.answer()
    except Exception as error:
        detailed_send_message_error = traceback.format_exc()
        logger.error(f"Error in process_connect_wallet_command: {error}\n{detailed_send_message_error}")


@user_router.callback_query(F.data == "callback_button_transfer", StateFilter(default_state))
async def process_transfer_token_command(callback: CallbackQuery, state: FSMContext) -> None:
    """
        Handles the command for transferring tokens.

        Args:
            callback (CallbackQuery): CallbackQuery object containing information about the call.
            state (FSMContext): FSMContext object for working with chat states.

        Returns:
            None
    """
    await process_wallets_command(callback, state, "transfer")


@user_router.callback_query(F.data == "callback_button_balance", StateFilter(default_state))
async def process_balance_command(callback: CallbackQuery, state: FSMContext) -> None:
    """
    Обрабатывает команду для получения баланса кошелька.

    Args:
        callback (CallbackQuery): Объект CallbackQuery, содержащий информацию о вызове.
        state (FSMContext): Объект FSMContext для работы с состояниями чата.

    Returns:
        None
    """
    await process_wallets_command(callback, state, "balance")


@user_router.callback_query(F.data == "callback_button_transaction", StateFilter(default_state))
async def process_transactions_command(callback: CallbackQuery, state: FSMContext) -> None:
    """
        Handles the command for viewing transactions.

        Args:
            callback (CallbackQuery): CallbackQuery object containing information about the call.
            state (FSMContext): FSMContext object for working with chat states.

        Returns:
            None
    """
    await process_wallets_command(callback, state, "transactions")


@user_router.callback_query(F.data == "callback_button_delete_wallet", StateFilter(default_state))
async def process_delete_wallet(callback: CallbackQuery, state: FSMContext) -> None:
    """
        Handles the command for delete wallet.

        Args:
            callback (CallbackQuery): CallbackQuery object containing information about the call.
            state (FSMContext): FSMContext object for working with chat states.

        Returns:
            None
    """
    await process_wallets_command(callback, state, "delete")
