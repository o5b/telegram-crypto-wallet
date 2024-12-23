import json
import time
import traceback
from typing import Dict, List

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from spl.token.constants import TOKEN_2022_PROGRAM_ID

from bot.services import get_sol_balance, get_spl_token_data, is_valid_wallet_address
from bot.utils import get_translation, update_or_create_token
from logger_config import logger
from web.applications.wallet.models import Wallet


async def get_main_keyboard(lang: str) -> InlineKeyboardMarkup:
    TRANSLATION = await get_translation(lang=lang)
    buttons = []

    button_data = [
        (TRANSLATION["create_wallet"], "callback_button_create_wallet"),
        (TRANSLATION["create_wallet_from_seed"], "callback_button_create_wallet_from_seed"),
        (TRANSLATION["connect_wallet"], "callback_button_connect_wallet"),
        (TRANSLATION["balance"], "callback_button_balance"),
        (TRANSLATION["token_transfer"], "callback_button_transfer"),
        (TRANSLATION["transaction"], "callback_button_transaction"),
        (TRANSLATION["delete_wallet"], "callback_button_delete_wallet"),
    ]

    for text, callback_data in button_data:
        button = InlineKeyboardButton(text=text, callback_data=callback_data)
        buttons.append([button])

    main_keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)

    return main_keyboard


async def get_back_keyboard(lang: str) -> InlineKeyboardMarkup:
    TRANSLATION = await get_translation(lang=lang)
    back_keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=TRANSLATION["button_back"], callback_data="callback_button_back")]
        ]
    )
    return back_keyboard


async def get_wallet_keyboard(user_wallets: List[Wallet], lang: str) -> InlineKeyboardMarkup:
    """
        Function for creating a keyboard with user wallets.

        Args:
            user_wallets (List[Wallet]): The list of user wallets.

        Returns:
            InlineKeyboardMarkup: The keyboard with wallet buttons.
    """

    wallet_buttons = []

    TRANSLATION = await get_translation(lang=lang)

    for i, wallet in enumerate(user_wallets, start=1):
        balance = await get_sol_balance(wallet.wallet_address)

        wallet_info = TRANSLATION["wallet_info_template"].format(
            number=i,
            name=wallet.name,
            address=wallet.wallet_address,
            balance=balance
        )

        wallet_info_lines = wallet_info.split('\n')
        wallet_button_text = '\n'.join(wallet_info_lines)
        wallet_button = InlineKeyboardButton(
            text=wallet_button_text,
            callback_data=f"wallet_address:{wallet.wallet_address}",
        )

        wallet_buttons.append([wallet_button])

    return_to_main_menu_button = InlineKeyboardButton(
        text=TRANSLATION["button_back"],
        callback_data="callback_button_back",
    )

    wallet_buttons.append([return_to_main_menu_button])

    wallet_keyboard = InlineKeyboardMarkup(inline_keyboard=wallet_buttons)

    return wallet_keyboard


async def get_token_keyboard(wallet_address: str, lang: str) -> InlineKeyboardMarkup:
    """
        Function for creating a keyboard with user tokens.

        Args:
            wallet_address (str): The user wallet.

        Returns:
            InlineKeyboardMarkup: The keyboard with token buttons.
    """
    try:

        token_buttons = []
        TRANSLATION = await get_translation(lang=lang)
        sol_balance = await get_sol_balance(wallet_address)
        sol_token_info = TRANSLATION["token_info_template"].format(name='Solana', symbol='SOL', amount=sol_balance)
        sol_token_button = InlineKeyboardButton(text=sol_token_info, callback_data=f"sol_{sol_balance}")
        token_buttons.append([sol_token_button])

        spl_token_list = await get_spl_token_data(wallet_address, program_id=TOKEN_2022_PROGRAM_ID)

        for spl_token in spl_token_list:

            if spl_token:
                defaults = {}

                if 'metadata' in spl_token:
                    if 'name' in spl_token['metadata']:
                        defaults['name'] = spl_token['metadata']['name']
                    if 'symbol' in spl_token['metadata']:
                        defaults['symbol'] = spl_token['metadata']['symbol']
                    if 'uri' in spl_token['metadata']:
                        defaults['metadata_uri'] = spl_token['metadata']['uri']
                    if 'raw' in spl_token['metadata']:
                        defaults['raw_metadata'] = spl_token['metadata']['raw']

                if 'amount' in spl_token:
                    if 'uiAmount' in spl_token['amount']:
                        spl_balance = spl_token['amount']['uiAmount']
                        defaults['decimals'] = spl_token['amount']['decimals']

                if 'state' in spl_token:
                    defaults['state'] = spl_token['state']

                if 'raw' in spl_token:
                    defaults['raw_metadata'] = spl_token['raw']

                if 'mint' in spl_token and is_valid_wallet_address(spl_token['mint']):
                    token, created = await update_or_create_token(mint_account=spl_token['mint'], defaults=defaults)

                if token:
                    spl_token_info = TRANSLATION["token_info_template"].format(name=defaults['name'], symbol=defaults['symbol'], amount=spl_balance)

                    spl_token_button = InlineKeyboardButton(
                        text=spl_token_info,
                        callback_data=f'spl_{sol_balance}_{spl_balance}_{token.mint_account}',
                    )

                    token_buttons.append([spl_token_button])

        return_to_main_menu_button = InlineKeyboardButton(
            text=TRANSLATION["button_back"],
            callback_data="callback_button_back",
        )

        token_buttons.append([return_to_main_menu_button])

        token_keyboard = InlineKeyboardMarkup(inline_keyboard=token_buttons)

        return token_keyboard

    except Exception as error:
        detailed_error_traceback = traceback.format_exc()
        logger.error(f"Failed to get token keyboard: {error}\n{detailed_error_traceback}")
        raise Exception(f"Failed to get token keyboard: {error}\n{detailed_error_traceback}")
