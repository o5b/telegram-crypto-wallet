import traceback

from aiogram import F, Router
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import (CallbackQuery, InlineKeyboardButton,
                           InlineKeyboardMarkup, Message)

from bot.keyboards import get_main_keyboard
from bot.states import FSMWallet
from bot.utils import delete_wallet, get_translation, get_user
from logger_config import logger

delete_wallet_router: Router = Router()


@delete_wallet_router.callback_query(F.data.startswith("wallet_address:"),
                                   StateFilter(FSMWallet.delete_wallet))
async def process_confirmation_delete_wallet(callback: CallbackQuery, state: FSMContext) -> None:
    """
        Handles the button press to confirmation a wallet deleting.

        Args:
            callback (CallbackQuery): The callback query object.
            state (FSMContext): The state context of the finite state machine.

        Returns:
            None
    """
    try:
        TRANSLATION = await get_translation(lang=callback.from_user.language_code)
        wallet_address = callback.data.split(":")[1]

        delete_keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text=TRANSLATION["button_delete_confirmation"], callback_data=f"del_wallet:{wallet_address}")],
                [InlineKeyboardButton(text=TRANSLATION["button_back"], callback_data="callback_button_back")],
            ]
        )

        await callback.message.answer(TRANSLATION["delete_wallet_confirmation"], reply_markup=delete_keyboard)

    except Exception as e:
        detailed_error_traceback = traceback.format_exc()
        logger.error(f"Error in process_wallet_name: {e}\n{detailed_error_traceback}")


@delete_wallet_router.callback_query(F.data.startswith("del_wallet:"), StateFilter(FSMWallet.delete_wallet))
async def process_delete_wallet_end(callback: CallbackQuery, state: FSMContext) -> None:
    """
        Handles the button press to confirmation a wallet deleting.

        Args:
            callback (CallbackQuery): The callback query object.
            state (FSMContext): The state context of the finite state machine.

        Returns:
            None
    """
    try:
        TRANSLATION = await get_translation(lang=callback.from_user.language_code)
        wallet_address = callback.data.split(":")[1]
        user = await get_user(telegram_id=callback.from_user.id)
        number_objects_deleted = await delete_wallet(user=user, wallet_address=wallet_address)

        print(f'number_objects_deleted: {number_objects_deleted}')

        if number_objects_deleted[0] > 0:
            await callback.message.answer(TRANSLATION["delete_wallet_successful"].format(wallet_address=wallet_address))
        else:
            await callback.message.answer(TRANSLATION["delete_wallet_not_successful"].format(wallet_address=wallet_address))

        await callback.message.answer(
            TRANSLATION["back_to_main_menu"],
            reply_markup=await get_main_keyboard(lang=callback.from_user.language_code)
        )
        await state.clear()

    except Exception as e:
        detailed_error_traceback = traceback.format_exc()
        logger.error(f"Error in process_delete_wallet: {e}\n{detailed_error_traceback}")
