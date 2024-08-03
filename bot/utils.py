import json
from typing import Any, Dict, List, Optional, Tuple

from django.contrib.auth import get_user_model
from django.contrib.auth.models import AbstractUser

from bot.translation.translation_en import TRANSLATION_EN
from bot.translation.translation_ru import TRANSLATION_RU
from web.applications.wallet.models import HDWallet, Token, Transaction, Wallet


async def get_translation(lang: str) -> dict:
    if lang == 'ru':
        TRANSLATION = TRANSLATION_RU
    else:
        TRANSLATION = TRANSLATION_EN
    return TRANSLATION


########### django #########

User = get_user_model()


async def update_or_create_user(telegram_id: int, defaults: dict) -> Tuple[AbstractUser, bool]:
    user, created = await User.objects.aupdate_or_create(telegram_id=telegram_id, defaults=defaults)
    return user, created


async def get_user(telegram_id: int) -> AbstractUser | None:
    user = await User.objects.filter(telegram_id=telegram_id).afirst()
    return user


async def update_or_create_token(mint_account: str, defaults: dict) -> Tuple[Token, bool]:
    token, created = await Token.objects.aupdate_or_create(mint_account=mint_account, defaults=defaults)
    return token, created


async def get_wallet(wallet_address: str) -> Wallet | None:
    wallet = await Wallet.objects.filter(wallet_address=wallet_address).afirst()
    return wallet


async def update_wallet(wallet_address: str, solana_derivation_path: str) -> Wallet | None:
    wallet = await Wallet.objects.filter(wallet_address=wallet_address).afirst()
    if wallet:
        wallet.solana_derivation_path = solana_derivation_path
        await wallet.asave()
    return wallet


async def get_token(mint_account: str) -> Token | None:
    token = await Token.objects.filter(mint_account=mint_account).afirst()
    return token


async def get_transaction_history_from_db(wallet_address: str) -> list[Transaction] | None:
    transaction_history_from_db = None
    wallet = await Wallet.objects.filter(wallet_address=wallet_address).afirst()
    if wallet:
        transaction_history_from_db = wallet.transactions.all().order_by('-transaction_time')
    return transaction_history_from_db


async def save_transaction(tr: Any) -> None:
    address_list = []
    wallets = None
    tr_dict = json.loads(tr.to_json())

    transaction_id = tr_dict['transaction']['signatures'][0] or ''
    sender = tr_dict['transaction']['message']['accountKeys'][0] or ''
    recipient = tr_dict['transaction']['message']['accountKeys'][1] or ''
    slot = tr_dict['slot'] or None
    transaction_time = tr_dict['blockTime'] or None
    transaction_status = f"{tr_dict['meta']['status'] or ''}"
    transaction_err = f"{tr_dict['meta']['err']  or ''}"
    pre_balances = tr_dict['meta']['preBalances'][0] or None
    post_balances = tr_dict['meta']['postBalances'][0] or None

    if sender:
        address_list.append(sender)

    if recipient:
        address_list.append(recipient)

    if address_list:
        wallets = await Wallet.objects.filter(wallet_address__in=address_list)

    if wallets and transaction_id:
        transaction_obj = await Transaction.objects.filter(transaction_id=transaction_id).afirst()

        if transaction_obj:
            # if the transaction exists - update the wallets
            await transaction_obj.wallet.aset(wallets)

        else:
            try:
                create_transaction_obj = await Transaction.objects.acreate(
                    transaction_id =transaction_id,
                    slot=slot,
                    transaction_time=transaction_time,
                    sender=sender,
                    recipient=recipient,
                    pre_balances=pre_balances,
                    post_balances=post_balances,
                    transaction_status=transaction_status,
                    transaction_err=transaction_err,
                )

                await create_transaction_obj.wallet.aset(wallets)
            except Exception as er:
                print(f'Error create transaction: {er}')

    return None


async def delete_wallet(user: AbstractUser, wallet_address: str) -> int | None:
    number_objects_deleted = None
    wallet = await Wallet.objects.filter(user=user, wallet_address=wallet_address).afirst()
    if wallet:
        number_objects_deleted = await wallet.adelete()
    return number_objects_deleted


async def create_wallet(
        user: AbstractUser,
        wallet_address: str,
        name: str,
        description: str,
        derivation_path: str
    ) -> Wallet | None:

    user.last_solana_derivation_path = derivation_path
    await user.asave()

    hd_wallet = await HDWallet.objects.acreate(
        name=name,
        first_address=wallet_address,
        last_derivation_path=derivation_path,
    )

    if hd_wallet:
        await hd_wallet.user.aset([user])

    wallet = await Wallet.objects.acreate(
        wallet_address=wallet_address,
        name=name,
        description=description,
        derivation_path=derivation_path,
        hd_wallet=hd_wallet,
    )

    if wallet:
        await wallet.user.aset([user])
        return wallet

    return None


async def create_wallet_from_seed(
        user: AbstractUser,
        name: str,
        description: str,
        wallet_address: str,
        derivation_path: str
    ) -> Wallet | None:

    user.last_solana_derivation_path = derivation_path
    await user.asave()

    wallet = await Wallet.objects.acreate(
        wallet_address=wallet_address,
        name=name,
        description=description,
        derivation_path=derivation_path,
    )

    if wallet:
        await wallet.user.aset([user])
        return wallet

    return None


async def connect_wallet(
        user: AbstractUser,
        wallet_address: str,
        name: str,
        description: str
    ) -> Wallet | None:

    wallet = await Wallet.objects.acreate(
        wallet_address=wallet_address,
        name=name,
        description=description,
    )

    if wallet:
        await wallet.user.aset([user])
        return  wallet

    return None

############################
