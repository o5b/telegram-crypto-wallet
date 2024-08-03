import traceback

from aiogram import F, Router
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import default_state
from aiogram.types import CallbackQuery

from bot.keyboards import (get_back_keyboard, get_main_keyboard,
                           get_wallet_keyboard)
from bot.states import FSMWallet
from bot.utils import get_translation
from bot.wallet_service import retrieve_user_wallets
from logger_config import logger

back_button_router = Router()


@back_button_router.callback_query(F.data == "callback_button_back", StateFilter(FSMWallet))
async def process_back_button(callback: CallbackQuery, state: FSMContext) -> None:
    """
        Handles the "Back" button press during interaction with the bot.

        Arguments:
        callback (CallbackQuery): The callback query object.
        state (FSMContext): The state context of the finite state machine.

        Returns:
        None
    """
    try:
        current_state = await state.get_state()
        TRANSLATION = await get_translation(lang=callback.from_user.language_code)

        if current_state == FSMWallet.create_wallet_add_name:
            await state.set_state(default_state)
            await callback.message.edit_text(TRANSLATION["back_to_main_menu"])
            await callback.message.edit_reply_markup(reply_markup=await get_main_keyboard(lang=callback.from_user.language_code))

        elif current_state == FSMWallet.create_wallet_add_description:
            await state.set_state(FSMWallet.create_wallet_add_name)
            await callback.message.edit_text(
                TRANSLATION["create_new_name_wallet"], reply_markup=await get_back_keyboard(lang=callback.from_user.language_code))

        ############################################################################################################
        elif current_state == FSMWallet.create_wallet_from_seed_add_seed:
            await state.set_state(default_state)
            await callback.message.edit_text(TRANSLATION["back_to_main_menu"])
            await callback.message.edit_reply_markup(reply_markup=await get_main_keyboard(lang=callback.from_user.language_code))

        elif current_state == FSMWallet.create_wallet_from_seed_add_name:
            await state.set_state(FSMWallet.create_wallet_from_seed_add_seed)
            await callback.message.edit_text(
                TRANSLATION["create_seed_wallet"], reply_markup=await get_back_keyboard(lang=callback.from_user.language_code))

        elif current_state == FSMWallet.create_wallet_from_seed_add_description:
            await state.set_state(FSMWallet.create_wallet_from_seed_add_name)
            await callback.message.edit_text(
                TRANSLATION["create_new_name_wallet"], reply_markup=await get_back_keyboard(lang=callback.from_user.language_code))

        #############################################################################################################
        elif current_state == FSMWallet.connect_wallet_add_address:
            await state.set_state(default_state)
            await callback.message.edit_text(TRANSLATION["back_to_main_menu"])
            await callback.message.edit_reply_markup(reply_markup=await get_main_keyboard(lang=callback.from_user.language_code))

        elif current_state == FSMWallet.connect_wallet_add_name:
            await state.set_state(FSMWallet.connect_wallet_add_address)
            await callback.message.edit_text(TRANSLATION["connect_wallet_address"])
            await callback.message.edit_reply_markup(reply_markup=await get_back_keyboard(lang=callback.from_user.language_code))

        elif current_state == FSMWallet.connect_wallet_add_description:
            await state.set_state(FSMWallet.connect_wallet_add_name)
            await callback.message.edit_text(
                TRANSLATION["connect_wallet_add_name"], reply_markup=await get_back_keyboard(lang=callback.from_user.language_code))
        #############################################################################################################
        elif current_state == FSMWallet.transfer_choose_sender_wallet:
            await state.set_state(default_state)
            await callback.message.edit_text(TRANSLATION["back_to_main_menu"])
            await callback.message.edit_reply_markup(reply_markup=await get_main_keyboard(lang=callback.from_user.language_code))

        elif current_state == FSMWallet.transfer_sender_private_key:
            await state.set_state(FSMWallet.transfer_choose_sender_wallet)
            await callback.message.edit_text(TRANSLATION["list_sender_wallets"])
            _, user_wallets = await retrieve_user_wallets(callback)
            wallet_keyboard = await get_wallet_keyboard(user_wallets, lang=callback.from_user.language_code)
            await callback.message.edit_reply_markup(reply_markup=wallet_keyboard)

        elif current_state == FSMWallet.transfer_recipient_address:
            await state.set_state(FSMWallet.transfer_sender_private_key)
            await callback.message.edit_text(TRANSLATION["transfer_sender_private_key_prompt"])
            await callback.message.edit_reply_markup(reply_markup=await get_back_keyboard(lang=callback.from_user.language_code))

        elif current_state == FSMWallet.transfer_token:
            await state.set_state(FSMWallet.transfer_recipient_address)
            await callback.message.edit_text(TRANSLATION["transfer_recipient_address_prompt"])
            await callback.message.edit_reply_markup(reply_markup=await get_back_keyboard(lang=callback.from_user.language_code))

        elif current_state == FSMWallet.transfer_amount:
            # await state.set_state(FSMWallet.transfer_token)
            # await callback.message.edit_text(TRANSLATION["transfer_recipient_address_prompt"])
            # await callback.message.edit_reply_markup(reply_markup=back_keyboard)
            await state.set_state(default_state)
            await callback.message.edit_text(TRANSLATION["back_to_main_menu"])
            await callback.message.edit_reply_markup(reply_markup=await get_main_keyboard(lang=callback.from_user.language_code))

        #############################################################################################################
        elif current_state == FSMWallet.choose_transaction_wallet:
            await state.set_state(default_state)
            await callback.message.edit_text(TRANSLATION["back_to_main_menu"])
            await callback.message.edit_reply_markup(reply_markup=await get_main_keyboard(lang=callback.from_user.language_code))

        #############################################################################################################
        elif current_state == FSMWallet.delete_wallet:
            await state.set_state(default_state)
            await callback.message.edit_text(TRANSLATION["back_to_main_menu"])
            await callback.message.edit_reply_markup(reply_markup=await get_main_keyboard(lang=callback.from_user.language_code))

        # Отправляем ответ на запрос обратного вызова для подтверждения обработки
        await callback.answer()
    except Exception as e:
        detailed_error_traceback = traceback.format_exc()
        logger.error(f"Error in process_back_button: {e}\n{detailed_error_traceback}")
