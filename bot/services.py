import asyncio
import io
import math
import time
import traceback
from pprint import pprint
from typing import Any, Dict, List, Optional, Tuple

import base58
import httpx
import mnemonic
import requests
import spl.token.instructions as spl_token_instructions
from PIL import Image
from solana.rpc import commitment as solana_commitment
from solana.rpc.async_api import AsyncClient
from solana.rpc.types import TokenAccountOpts, TxOpts
# from solana.transaction import Transaction
from solders.transaction import Transaction
from solders.instruction import AccountMeta, Instruction
from solders.keypair import Keypair
from solders.pubkey import Pubkey
from solders.signature import Signature
from solders.system_program import ID as SYS_PROGRAM_ID
from solders.system_program import TransferParams, transfer
from solders.sysvar import RENT
from solders.transaction_status import TransactionConfirmationStatus
from solders.message import Message
from spl.token.constants import (ASSOCIATED_TOKEN_PROGRAM_ID,
    # TOKEN_2022_PROGRAM_ID,
    TOKEN_PROGRAM_ID,
)

from bot.config import LAMPORT_TO_SOL_RATIO, SOLANA_NODE_URL
from bot.validators import (is_valid_amount, is_valid_private_key,
                            is_valid_wallet_address)
from logger_config import logger


TOKEN_2022_PROGRAM_ID: Pubkey = Pubkey.from_string("TokenzQdBNbLqP5VEhdkAS6EPFLC1PHnBqCXEpPxuEb")
"""Public key that identifies the SPL token program."""

# Например, установить таймаут на чтение ответа 120 секунд, таймаут на соединение 20 секунд
timeout_settings = httpx.Timeout(read=120.0, connect=20.0, write=None, pool=None)
http_client = AsyncClient(SOLANA_NODE_URL, timeout=timeout_settings)


async def create_solana_wallet() -> Tuple[str, str, str]:
    """
        Generate a new Solana wallet.

        Returns:
            Tuple[str, str, str]: A tuple containing the public address and private key of the generated wallet.

        Raises:
            Exception: If there's an error during the wallet creation process.
    """
    try:
        solana_derivation_path = "m/44'/501'/0'/0'"
        mnemo = mnemonic.Mnemonic("english")
        words = mnemo.generate(strength=128) # strength=128 for 12 words, strength=256 for 24 words
        seed = mnemo.to_seed(words, passphrase="")
        keypair = Keypair.from_seed_and_derivation_path(seed, solana_derivation_path)
        wallet_address = str(keypair.pubkey())
        private_key = keypair.secret().hex()
        return wallet_address, private_key, words

    except Exception as e:
        detailed_error_traceback = traceback.format_exc()
        logger.error(f"Failed to create Solana wallet: {e}\n{detailed_error_traceback}")
        raise Exception(f"Failed to create Solana wallet: {e}")


def get_wallet_address_from_private_key(private_key: str) -> str:
    """
        Gets the wallet address from the private key.

        Args:
            private_key (str): A string containing the presumed private key.

        Returns:
            str: The wallet address as a string.
    """
    # Создание объекта Keypair из закрытого ключа, преобразованного из шестнадцатеричной строки в байтовый формат.
    keypair = Keypair.from_seed(bytes.fromhex(private_key))
    wallet_address = str(keypair.pubkey())
    return wallet_address


async def get_spl_token_metadata_from_uri(uri, client):
    metadata = {}
    user_agent =  {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36"}
    try:
        response = requests.get(uri, headers=user_agent)
        if response.status_code == 200:
            if hasattr(response, 'json') and response.json():
                response_json = response.json()
                if response_json:
                    metadata['raw'] = response_json
                    if 'description' in response_json:
                        metadata['description'] = response_json['description']
                    if 'image' in response_json:
                        metadata['image'] = response_json['image']
        return metadata
    except Exception as error:
        detailed_error_traceback = traceback.format_exc()
        logger.error(f"Failed to get Solana SPL token data: {error}\n{detailed_error_traceback}")
        raise Exception(f"Failed to get Solana SPL token data: {error}\n{detailed_error_traceback}")


async def get_spl_token_metadata(mint_address, client):
    try:
        metadata = {}
        res = await client.get_account_info_json_parsed(pubkey=Pubkey.from_string(mint_address))
        if res and hasattr(res, 'value'):
            info = res.value
            if info and hasattr(info, 'data'):
                if hasattr(info.data, 'parsed') and info.data.parsed:
                    if 'info' in info.data.parsed and info.data.parsed['info']:
                        if 'extensions' in info.data.parsed['info'] and info.data.parsed['info']['extensions']:
                            for extension in info.data.parsed['info']['extensions']:
                                if 'extension' in extension and extension['extension'] == 'tokenMetadata':
                                    if 'state' in extension and extension['state']:
                                        if 'name' in extension['state']:
                                            metadata['name'] = extension['state']['name']
                                        if 'symbol' in extension['state']:
                                            metadata['symbol'] = extension['state']['symbol']
                                        if 'uri' in extension['state']:
                                            metadata['uri'] = extension['state']['uri']
                                            if metadata['uri']:
                                                metadata_from_uri = await get_spl_token_metadata_from_uri(metadata['uri'], client)
                                                if metadata_from_uri and isinstance(metadata_from_uri, dict):
                                                    metadata.update(metadata_from_uri)
                                                    # if 'image' in metadata_from_uri and metadata_from_uri['image']:
                                                    #     img_data = requests.get(metadata_from_uri['image']).content
                                                    #     img = Image.open(io.BytesIO(img_data))
                                                    #     if isinstance(img, Image.Image):
                                                    #         width, height = img.size
                                                    #         max_size = max(width, height)
                                                    #         proportion_side = math.ceil(max_size / 20)
                                                    #         resize_img = img.resize(
                                                    #             (width // proportion_side, height // proportion_side)
                                                    #         )
                                                    #         img_path = f"./media/token_logo/{metadata['symbol']}.png"
                                                    #         resize_img.save(img_path)
                                                    #         metadata['logo'] = img_path

        logger.debug(f"***** Spl token metadata: {metadata}")
        return metadata
    except Exception as error:
        detailed_error_traceback = traceback.format_exc()
        logger.error(f"Failed to get Solana SPL token data: {error}\n{detailed_error_traceback}")
        raise Exception(f"Failed to get Solana SPL token data: {error}\n{detailed_error_traceback}")


async def get_spl_token_data(wallet_address, client):
    try:
        spl_tokens = []
        opts = TokenAccountOpts(program_id=TOKEN_2022_PROGRAM_ID)
        pubkey = Pubkey.from_string(wallet_address)
        spl_token_accounts = await client.get_token_accounts_by_owner_json_parsed(owner=pubkey, opts=opts)
        if spl_token_accounts and hasattr(spl_token_accounts, 'value'):
            spl_token_accounts_list = spl_token_accounts.value
            if spl_token_accounts_list:
                for token in spl_token_accounts_list:
                    spl_token_data = {}
                    if token and hasattr(token, 'account'):
                        if token.account and hasattr(token.account, 'data'):
                            if token.account.data and hasattr(token.account.data, 'parsed'):
                                if token.account.data.parsed and 'info' in token.account.data.parsed:
                                    if token.account.data.parsed['info']:
                                        if 'isNative' in token.account.data.parsed['info']:
                                            spl_token_data['is_native'] = token.account.data.parsed['info']['isNative']
                                        if 'state' in token.account.data.parsed['info']:
                                            spl_token_data['state'] = token.account.data.parsed['info']['state']
                                        if 'tokenAmount' in token.account.data.parsed['info']:
                                            spl_token_data['amount'] = token.account.data.parsed['info']['tokenAmount']
                                        if 'mint' in token.account.data.parsed['info']:
                                            spl_token_data['mint'] = token.account.data.parsed['info']['mint']
                                            if spl_token_data['mint']:
                                                metadata = await get_spl_token_metadata(spl_token_data['mint'], client)
                                                if metadata:
                                                    spl_token_data['metadata'] = metadata
                                        spl_tokens.append(spl_token_data)
        for t in spl_tokens:
            print(f"***** List spl token data: {t}")
        return spl_tokens
    except Exception as error:
        detailed_error_traceback = traceback.format_exc()
        logger.error(f"Failed to get Solana SPL token data: {error}\n{detailed_error_traceback}")
        raise Exception(f"Failed to get Solana SPL token data: {error}\n{detailed_error_traceback}")


async def get_sol_balance(wallet_addresses, client):
    """
        Asynchronously retrieves the SOL balance for the specified wallet addresses.

        Args:
            wallet_addresses (Union[str, List[str]]): The wallet address or a list of wallet addresses.
            client: The Solana client.

        Returns:
            Union[float, List[float]]: The SOL balance or a list of SOL balances corresponding to the wallet addresses.
    """
    try:
        # Если передан одиночный адрес кошелька
        if isinstance(wallet_addresses, str):
            balance = (await client.get_balance(pubkey=Pubkey.from_string(wallet_addresses))).value
            # Преобразование лампортов в SOL
            sol_balance = balance / LAMPORT_TO_SOL_RATIO
            logger.debug(f"wallet_address: {wallet_addresses}, balance: {balance}, sol_balance: {sol_balance}")
            # spl_tokens_data = await get_spl_token_data(wallet_addresses, client)
            return sol_balance  #, spl_tokens_data
        # Если передан список адресов кошельков
        elif isinstance(wallet_addresses, list):
            sol_balances = []
            for address in wallet_addresses:
                balance = (await client.get_balance(Pubkey.from_string(address))).value
                # Преобразование лампортов в SOL
                sol_balance = balance / LAMPORT_TO_SOL_RATIO
                sol_balances.append(sol_balance)
            return sol_balances
        else:
            raise ValueError("Invalid type for wallet_addresses. Expected str or list[str].")
    except Exception as error:
        detailed_error_traceback = traceback.format_exc()
        logger.error(f"Failed to get Solana balance: {error}\n{detailed_error_traceback}")
        raise Exception(f"Failed to get Solana balance: {error}\n{detailed_error_traceback}")


async def transfer_sol_token(sender_address: str, sender_private_key: str, recipient_address: str, amount: float,
                         client: AsyncClient) -> bool:
    """
        Asynchronous function to transfer tokens between wallets.

        Args:
            sender_address (str): Sender's address.
            sender_private_key (str): Sender's private key.
            recipient_address (str): Recipient's address.
            amount (float): Amount of tokens to transfer.
            client (AsyncClient): Asynchronous client for sending the transaction.

        Raises:
            ValueError: If any of the provided addresses is invalid or the private key is invalid.

        Returns:
            bool: True if the transfer is successful, False otherwise.
    """
    if not is_valid_wallet_address(sender_address):
        raise ValueError("Invalid sender address")

    if not is_valid_wallet_address(recipient_address):
        raise ValueError("Invalid recipient address")

    if not is_valid_private_key(sender_private_key):
        raise ValueError("Invalid sender private key")

    if not is_valid_amount(amount):
        raise ValueError("Invalid amount")

    sender_keypair = Keypair.from_seed(bytes.fromhex(sender_private_key))

    # txn = Transaction().add(
    #     transfer(
    #         TransferParams(
    #             from_pubkey=sender_keypair.pubkey(),
    #             to_pubkey=Pubkey.from_string(recipient_address),
    #             # Количество лампортов для перевода, преобразованное из суммы SOL.
    #             lamports=int(amount * LAMPORT_TO_SOL_RATIO),
    #         )
    #     )
    # )

    # send_transaction_response = await client.send_transaction(txn, sender_keypair)

    params = [
        transfer(
            TransferParams(
                from_pubkey=sender_keypair.pubkey(),
                to_pubkey=Pubkey.from_string(recipient_address),
                # Количество лампортов для перевода, преобразованное из суммы SOL.
                lamports=int(amount * LAMPORT_TO_SOL_RATIO),
            )
        )
    ]

    msg = Message(params, sender_keypair.pubkey())
    latest_blockhash = (await client.get_latest_blockhash()).value.blockhash
    send_transaction_response = await client.send_transaction(Transaction([sender_keypair], msg, latest_blockhash))

    confirm_transaction_response = await client.confirm_transaction(send_transaction_response.value)

    if hasattr(confirm_transaction_response, 'value') and confirm_transaction_response.value[0]:
        if hasattr(confirm_transaction_response.value[0], 'confirmation_status'):
            confirmation_status = confirm_transaction_response.value[0].confirmation_status
            if confirmation_status:
                logger.debug(f"Transaction confirmation_status: {confirmation_status}")
                if confirmation_status in [TransactionConfirmationStatus.Confirmed,
                                           TransactionConfirmationStatus.Finalized]:
                    return True
    return False


def get_associated_token_address(owner: Pubkey, mint: Pubkey, token_program: Pubkey) -> Pubkey:
    """Derives the associated token address for the given wallet address and token mint.

    Returns:
        The public key of the derived associated token address.
    """
    key, _ = Pubkey.find_program_address(
        # seeds=[bytes(owner), bytes(TOKEN_2022_PROGRAM_ID), bytes(mint)],
        seeds=[bytes(owner), bytes(token_program), bytes(mint)],
        program_id=ASSOCIATED_TOKEN_PROGRAM_ID,
    )
    return key


def create_associated_token_account(payer: Pubkey, owner: Pubkey, mint: Pubkey, token_program: Pubkey) -> Instruction:
    """Creates a transaction instruction to create an associated token account.

    Returns:
        The instruction to create the associated token account.
    """
    associated_token_address = get_associated_token_address(owner, mint, token_program)
    return Instruction(
        accounts=[
            AccountMeta(pubkey=payer, is_signer=True, is_writable=True),
            AccountMeta(pubkey=associated_token_address, is_signer=False, is_writable=True),
            AccountMeta(pubkey=owner, is_signer=False, is_writable=False),
            AccountMeta(pubkey=mint, is_signer=False, is_writable=False),
            AccountMeta(pubkey=SYS_PROGRAM_ID, is_signer=False, is_writable=False),
            # AccountMeta(pubkey=TOKEN_2022_PROGRAM_ID, is_signer=False, is_writable=False),
            AccountMeta(pubkey=token_program, is_signer=False, is_writable=False),
            AccountMeta(pubkey=RENT, is_signer=False, is_writable=False),
        ],
        program_id=ASSOCIATED_TOKEN_PROGRAM_ID,
        data=bytes(0),
    )


async def get_token_account(owner: Pubkey, mint: Pubkey, client: AsyncClient) -> Pubkey | None:
    """ Get an associated token account if it exists.

        Returns:
            The public key of associated token account.
    """
    for attempt in range(5):
        try:
            response = await client.get_token_accounts_by_owner(owner=owner, opts=TokenAccountOpts(mint=mint))
            break
        except Exception as e:
            print(f"Error get token account for the owner: {owner}. Error msg.: {e}. Attempt {attempt + 1} out of 5.")
            await asyncio.sleep(10)
    else:
        raise Exception(f"Failed to get token account: {mint} from owner: {owner} after 5 attempts.")

    if response and hasattr(response, 'value'):
        accounts = response.value
        if accounts and hasattr(accounts[0], 'pubkey'):
            return accounts[0].pubkey
    return None


async def get_token_program_id(mint: Pubkey, client: AsyncClient) -> Pubkey | None:
    """ Get a Token Program (owner) from the token.
        Ex.: TOKEN_2022_PROGRAM_ID, TOKEN_PROGRAM_ID, ...

        Returns:
            The public key of Token Program.
    """
    for attempt in range(5):
        try:
            response = await client.get_account_info(pubkey=mint)
            break
        except Exception as e:
            print(f"Error when get account info: {e}. Attempt {attempt + 1} out of 5.")
            await asyncio.sleep(10)
    else:
        raise Exception("Failed to get account info after 5 attempts.")

    if response and hasattr(response, 'value'):
        if response.value and hasattr(response.value, 'owner'):
            return response.value.owner
    return None


async def get_transaction_confirmation_status(response_value, client) -> bool:
    confirm_transaction = await client.confirm_transaction(response_value)

    sig = Signature.from_string(f'{response_value}')
    if sig:
        res = await client.get_transaction(sig)
        print('******************** Transaction ***********************')
        pprint(res)

    if hasattr(confirm_transaction, 'value') and confirm_transaction.value[0]:
        if hasattr(confirm_transaction.value[0], 'confirmation_status'):
            confirmation_status = confirm_transaction.value[0].confirmation_status
            if confirmation_status:
                logger.debug(f"Transaction confirmation_status: {confirmation_status}")
                print(f'****** confirmation_status: {confirmation_status}')
                logger.debug(f"Transaction confirmation_status: {confirmation_status}")
                if confirmation_status in [TransactionConfirmationStatus.Confirmed, TransactionConfirmationStatus.Finalized]:
                    return True
    return False


async def transfer_spl_token(
        sender_address: str,
        sender_private_key: str,
        recipient_address: str,
        mint: str,
        amount: float,
        decimals: int,
    ) -> bool:

    try:
        client = AsyncClient(SOLANA_NODE_URL, timeout=30)

        if not is_valid_wallet_address(sender_address):
            raise ValueError("Invalid sender address")

        if not is_valid_wallet_address(recipient_address):
            raise ValueError("Invalid recipient address")

        if not is_valid_wallet_address(mint):
            raise ValueError("Invalid mint")

        if not is_valid_private_key(sender_private_key):
            raise ValueError("Invalid sender private key")

        if not is_valid_amount(amount):
            raise ValueError("Invalid amount")

        if not is_valid_amount(decimals):
            raise ValueError("Invalid decimals")

        sender_public_key = Pubkey.from_string(sender_address)
        sender_keypair = Keypair.from_seed(bytes.fromhex(sender_private_key))
        receiver_public_key = Pubkey.from_string(recipient_address)
        token_mint_public_key = Pubkey.from_string(mint)

        sender_associated_token_public_key = await get_token_account(sender_public_key, token_mint_public_key, client)

        if not sender_associated_token_public_key:
            raise Exception("Sender associated token account not found")

        receiver_associated_token_public_key = await get_token_account(receiver_public_key, token_mint_public_key, client)

        token_program_public_key = await get_token_program_id(token_mint_public_key, client)

        if not token_program_public_key:
            raise Exception("Token program not found")

        # transaction = Transaction()
        params = []

        opts = TxOpts(
            skip_confirmation=False,
            skip_preflight=False,
            preflight_commitment=solana_commitment.Finalized,
        )

        if not receiver_associated_token_public_key:
            receiver_associated_token_public_key = get_associated_token_address(
                owner=receiver_public_key,
                mint=token_mint_public_key,
                token_program=token_program_public_key,
            )

            if not receiver_associated_token_public_key:
                raise Exception("It is not possible to get a Receiver Associated Token Account from this data.")

            # transaction.add(
            #     create_associated_token_account(
            #         payer=sender_public_key,
            #         owner=receiver_public_key,
            #         mint=token_mint_public_key,
            #         token_program=token_program_public_key,
            #     )
            # )

            params.append(
                create_associated_token_account(
                    payer=sender_public_key,
                    owner=receiver_public_key,
                    mint=token_mint_public_key,
                    token_program=token_program_public_key,
                )
            )

            # TODO: нужно узнать, добавлять ли в транзакцию инструкцию для инициализации создаваемого associated_token_account

            # transaction.add(
            #     spl_token_instructions.initialize_account(
            #         spl_token_instructions.InitializeAccountParams(
            #             account=receiver_associated_token_public_key,
            #             mint=token_mint_public_key,
            #             owner=receiver_public_key,
            #             program_id=token_program_public_key,
            #         )
            #     )
            # )

            # The account initialization instruction gives this error::

            # SendTransactionPreflightFailureMessage {
            # message: "Transaction simulation failed: Error processing Instruction 1: custom program error: 0x6",
            # data: RpcSimulateTransactionResult( RpcSimulateTransactionResult {
            #    err: Some(InstructionError(1, Custom(6))),
            #       logs: Some([
            #         "Program ATokenGPvbdGVxr1b2hvZbsiqW5xWH25efTNsLJA8knL invoke [1]",
            #         "Program log: Create",
            #         "Program TokenzQdBNbLqP5VEhdkAS6EPFLC1PHnBqCXEpPxuEb invoke [2]",
            #         "Program log: Instruction: GetAccountDataSize",
            #         "Program TokenzQdBNbLqP5VEhdkAS6EPFLC1PHnBqCXEpPxuEb consumed 2941 of 591495 compute units",
            #         "Program return: TokenzQdBNbLqP5VEhdkAS6EPFLC1PHnBqCXEpPxuEb qgAAAAAAAAA=",
            #         "Program TokenzQdBNbLqP5VEhdkAS6EPFLC1PHnBqCXEpPxuEb success",
            #         "Program 11111111111111111111111111111111 invoke [2]",
            #         "Program 11111111111111111111111111111111 success",
            #         "Program log: Initialize the associated token account",
            #         "Program TokenzQdBNbLqP5VEhdkAS6EPFLC1PHnBqCXEpPxuEb invoke [2]",
            #         "Program log: Instruction: InitializeImmutableOwner",
            #         "Program TokenzQdBNbLqP5VEhdkAS6EPFLC1PHnBqCXEpPxuEb consumed 1924 of 583624 compute units",
            #         "Program TokenzQdBNbLqP5VEhdkAS6EPFLC1PHnBqCXEpPxuEb success",
            #         "Program TokenzQdBNbLqP5VEhdkAS6EPFLC1PHnBqCXEpPxuEb invoke [2]",
            #         "Program log: Instruction: InitializeAccount3",
            #         "Program TokenzQdBNbLqP5VEhdkAS6EPFLC1PHnBqCXEpPxuEb consumed 5175 of 579310 compute units",
            #         "Program TokenzQdBNbLqP5VEhdkAS6EPFLC1PHnBqCXEpPxuEb success",
            #         "Program ATokenGPvbdGVxr1b2hvZbsiqW5xWH25efTNsLJA8knL consumed 26203 of 600000 compute units",
            #         "Program ATokenGPvbdGVxr1b2hvZbsiqW5xWH25efTNsLJA8knL success",
            #         "Program TokenzQdBNbLqP5VEhdkAS6EPFLC1PHnBqCXEpPxuEb invoke [1]",
            #         "Program log: Instruction: InitializeAccount",
            #         "Program log: Error: account or token already in use",
            #         "Program TokenzQdBNbLqP5VEhdkAS6EPFLC1PHnBqCXEpPxuEb consumed 2379 of 573797 compute units",
            #         "Program TokenzQdBNbLqP5VEhdkAS6EPFLC1PHnBqCXEpPxuEb failed: custom program error: 0x6"
            #         ]),
            #       accounts: None, units_consumed: Some(28582), return_data: None, inner_instructions: None
            #     })
            # }

            # Without the account initialization instructions, the token transfer is successful:

            # log_messages: Some(
            #     [
            #         "Program ATokenGPvbdGVxr1b2hvZbsiqW5xWH25efTNsLJA8knL invoke [1]",
            #         "Program log: Create",
            #         "Program TokenzQdBNbLqP5VEhdkAS6EPFLC1PHnBqCXEpPxuEb invoke [2]",
            #         "Program log: Instruction: GetAccountDataSize",
            #         "Program TokenzQdBNbLqP5VEhdkAS6EPFLC1PHnBqCXEpPxuEb consumed 2941 of 394495 compute units",
            #         "Program return: TokenzQdBNbLqP5VEhdkAS6EPFLC1PHnBqCXEpPxuEb qgAAAAAAAAA=",
            #         "Program TokenzQdBNbLqP5VEhdkAS6EPFLC1PHnBqCXEpPxuEb success",
            #         "Program 11111111111111111111111111111111 invoke [2]",
            #         "Program 11111111111111111111111111111111 success",
            #         "Program log: Initialize the associated token account",
            #         "Program TokenzQdBNbLqP5VEhdkAS6EPFLC1PHnBqCXEpPxuEb invoke [2]",
            #         "Program log: Instruction: InitializeImmutableOwner",
            #         "Program TokenzQdBNbLqP5VEhdkAS6EPFLC1PHnBqCXEpPxuEb consumed 1924 of 386624 compute units",
            #         "Program TokenzQdBNbLqP5VEhdkAS6EPFLC1PHnBqCXEpPxuEb success",
            #         "Program TokenzQdBNbLqP5VEhdkAS6EPFLC1PHnBqCXEpPxuEb invoke [2]",
            #         "Program log: Instruction: InitializeAccount3",
            #         "Program TokenzQdBNbLqP5VEhdkAS6EPFLC1PHnBqCXEpPxuEb consumed 5175 of 382301 compute units",
            #         "Program TokenzQdBNbLqP5VEhdkAS6EPFLC1PHnBqCXEpPxuEb success",
            #         "Program ATokenGPvbdGVxr1b2hvZbsiqW5xWH25efTNsLJA8knL consumed 23212 of 400000 compute units",
            #         "Program ATokenGPvbdGVxr1b2hvZbsiqW5xWH25efTNsLJA8knL success",
            #         "Program TokenzQdBNbLqP5VEhdkAS6EPFLC1PHnBqCXEpPxuEb invoke [1]",
            #         "Program log: Instruction: TransferChecked",
            #         "Program TokenzQdBNbLqP5VEhdkAS6EPFLC1PHnBqCXEpPxuEb consumed 8509 of 376788 compute units",
            #         "Program TokenzQdBNbLqP5VEhdkAS6EPFLC1PHnBqCXEpPxuEb success",
            #     ],
            # ),

        # transaction.add(
        #     spl_token_instructions.transfer_checked(
        #         spl_token_instructions.TransferCheckedParams(
        #             program_id=token_program_public_key,    # program_id=TOKEN_2022_PROGRAM_ID
        #             source=sender_associated_token_public_key,
        #             mint=token_mint_public_key,
        #             dest=receiver_associated_token_public_key,
        #             owner=sender_public_key,
        #             amount=int(float(amount) * (10 ** int(decimals))),
        #             decimals=decimals,
        #         )
        #     )
        # )

        # for attempt in range(5):
        #     try:
        #         response = await client.send_transaction(transaction, sender_keypair, opts=opts)
        #         break
        #     except Exception as e:
        #         print(f"Error when transferring token: {e}. Attempt {attempt + 1} out of 5.")
        #         await asyncio.sleep(10)
        # else:
        #     raise Exception("Failed to transfer token after 5 attempts.")

        params.append(
            spl_token_instructions.transfer_checked(
                spl_token_instructions.TransferCheckedParams(
                    program_id=token_program_public_key,    # program_id=TOKEN_2022_PROGRAM_ID
                    source=sender_associated_token_public_key,
                    mint=token_mint_public_key,
                    dest=receiver_associated_token_public_key,
                    owner=sender_public_key,
                    amount=int(float(amount) * (10 ** int(decimals))),
                    decimals=decimals,
                )
            )
        )

        msg = Message(params, sender_keypair.pubkey())

        for attempt in range(5):
            try:
                latest_blockhash = (await client.get_latest_blockhash()).value.blockhash
                print(f'******** latest_blockhash: {latest_blockhash}')
                response = await client.send_transaction(Transaction([sender_keypair], msg, latest_blockhash), opts=opts)
                break
            except Exception as e:
                print(f"Error when transferring token: {e}. Attempt {attempt + 1} out of 5.")
                await asyncio.sleep(10)
        else:
            raise Exception("Failed to transfer token after 5 attempts.")

        if response and hasattr(response, 'value') and response.value:
            is_transaction_confirmation = await get_transaction_confirmation_status(response.value, client)
            if is_transaction_confirmation:
                return True
        return False

    except Exception as error:
        detailed_error_traceback = traceback.format_exc()
        logger.error(f"Failed transfer spl token: {error}\n{detailed_error_traceback}")
        raise Exception(f"Failed transfer spl token: {error}\n{detailed_error_traceback}")
    finally:
        await client.close()


def decode_solana_address(encoded_address: str) -> Optional[Any]:
    """
        Decodes a Solana address from Base58 format.

        Arguments:
        encoded_address (str): The encoded Solana address in Base58 format.

        Returns:
        str or None: The decoded Solana address as a string or None in case of error.
    """
    try:
        # Декодируем адрес из формата Base58
        decoded_bytes = base58.b58decode(encoded_address)
        # Преобразуем байтовые данные в строку
        decoded_address = decoded_bytes.decode('utf-8')
        return decoded_address
    except Exception as e:
        print(f"Failed to decode Solana address: {e}")
        return None


async def get_solana_transaction_history(wallet_address: str, transaction_id_before: str | None, transaction_limit: int) -> list[dict]:
    """
        Retrieves transaction history for a given Solana wallet address.

        Arguments:
        wallet_address (str): The Solana wallet address.

        Returns:
        list[dict]: A list of dictionaries representing transactions in JSON format.
    """
    try:
        transaction_history = []

        # # Декодируем строку Base58 в байтовый формат
        # pubkey_bytes = base58.b58decode(wallet_address)
        # # Создаем объект Pubkey из байтового представления
        # pubkey = Pubkey(pubkey_bytes)
        pubkey = Pubkey.from_string(wallet_address)

        try:
            signature_statuses = (
                await http_client.get_signatures_for_address(pubkey, before=transaction_id_before, limit=transaction_limit)
            ).value

            if signature_statuses:
                for signature_status in signature_statuses:
                    # Получаем транзакцию по подписи
                    transaction = (await http_client.get_transaction(signature_status.signature)).value
                    # Добавляем полученную транзакцию в историю транзакций
                    transaction_history.append(transaction)

                # Возвращаем список истории транзакций
                return transaction_history
            return []

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 429:
                # Если получена ошибка "429 Too Many Requests", вернем None
                return []
            else:
                raise e

    except Exception as e:
        detailed_error_traceback = traceback.format_exc()
        logger.error(
            f"Failed to get transaction history for Solana wallet {wallet_address}: {e}\n{detailed_error_traceback}")
        return []
