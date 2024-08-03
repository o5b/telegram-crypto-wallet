from django.db import models
from django.contrib.auth import get_user_model

from web.applications.core.models import Common, PathAndRename


class HDWallet(Common):
    """
    Hierarchical Deterministic wallets
    """
    user = models.ManyToManyField(
        verbose_name='HD-Wallet owners',
        to=get_user_model(),
        related_name='hdwallets',
    )

    name = models.CharField(
        verbose_name='HD-wallet name',
        max_length=100,
        blank=True,
    )

    first_address = models.CharField(
        verbose_name='First wallet address',
        help_text="Wallet address for initial derivation path, Ex.: \"m/44'/60'/0'/0/0\". Needed for identification HD-wallet",
        max_length=200,
        unique=True,
    )

    last_derivation_path = models.CharField(
        verbose_name='Last derivation path',
        max_length=100,
        blank=True,
    )

    class Meta:
        ordering = ['created']
        verbose_name = 'HD-wallet'
        verbose_name_plural = 'HD-wallets'

    def __str__(self):
        return f'{self.first_address[:4]}***{self.first_address[-4:]}'


class Wallet(Common):
    """
    Wallet
    """

    user = models.ManyToManyField(
        verbose_name='Wallet owners',
        to=get_user_model(),
        related_name='wallets',
    )

    hd_wallet = models.ForeignKey(
        verbose_name='HD-Wallet',
        to=HDWallet,
        on_delete=models.CASCADE,
        related_name='child_wallets',
        blank=True,
        null=True,
    )

    name = models.CharField(
        verbose_name='Wallet name',
        max_length=100,
        blank=True,
    )

    wallet_address = models.CharField(
        verbose_name='Wallet address',
        max_length=200,
        unique=True,
    )

    description = models.CharField(
        verbose_name='Wallet description',
        max_length=200,
        blank=True,
    )

    derivation_path = models.CharField(
        verbose_name='Derivation path',
        max_length=100,
        blank=True,
    )

    class Meta:
        ordering = ['created']
        verbose_name = 'wallet'
        verbose_name_plural = 'wallets'

    def __str__(self):
        return self.wallet_address


class Transaction(Common):
    """
    Transaction
    """
    wallet = models.ManyToManyField(
        verbose_name='Wallet',
        to=Wallet,
        related_name='transactions',
    )

    transaction_id = models.CharField(
        verbose_name='Transaction id',
        max_length=200,
        unique=True,
    )

    sender = models.CharField(
        verbose_name='Sender',
        max_length=200,
        blank=True,
    )

    recipient = models.CharField(
        verbose_name='Recipient',
        max_length=200,
        blank=True,
    )

    pre_balances = models.PositiveBigIntegerField(
        verbose_name='Pre-balances',
        blank=True,
        null=True,
    )

    post_balances = models.PositiveBigIntegerField(
        verbose_name='Post-balances',
        blank=True,
        null=True,
    )

    transaction_time = models.PositiveBigIntegerField(
        verbose_name='Transaction time',
        blank=True,
        null=True,
    )

    slot = models.PositiveBigIntegerField(
        verbose_name='Transaction slot',
        blank=True,
        null=True,
    )

    transaction_status = models.CharField(
        verbose_name='Transaction status',
        max_length=200,
        blank=True,
    )

    transaction_err = models.CharField(
        verbose_name='Transaction error',
        max_length=200,
        blank=True,
    )

    class Meta:
        ordering = ['transaction_time']
        verbose_name = 'transaction'
        verbose_name_plural = 'transactions'

    def __str__(self):
        return f'id: {self.transaction_id[:4]}...{self.transaction_id[-4:]}, time: {self.transaction_time}, slot: {self.slot}'


class Token(Common):
    """
    Token: https://solana.com/docs/core/tokens
    """

    mint_account = models.CharField(
        # Tokens on Solana are uniquely identified by the address of a Mint Account
        verbose_name='Mint account',
        max_length=100,
        unique=True,
    )

    token_account = models.CharField(
        verbose_name='Token account',
        max_length=100,
        blank=True,
    )

    program = models.CharField(
        verbose_name='Token program id',
        max_length=100,
        blank=True,
    )

    decimals = models.PositiveSmallIntegerField(
        verbose_name='Token decimals',
        default=9,
    )

    state = models.CharField(
        verbose_name='Token state',
        max_length=100,
        blank=True,
    )

    symbol = models.CharField(
        verbose_name='Token symbol',
        max_length=10,
        blank=True,
    )

    name = models.CharField(
        verbose_name='Token name',
        max_length=100,
        blank=True,
    )

    logo = models.ImageField(
        verbose_name='Token logo',
        upload_to=PathAndRename('wallet/token/logo'),
        blank=True,
        null=True,
    )

    logo_url =  models.URLField(
        verbose_name='Token logo url',
        blank=True,
    )

    metadata_uri =  models.CharField(
        verbose_name='Token metadata uri',
        max_length=2000,
        blank=True,
    )

    metadata_account = models.CharField(
        verbose_name='Metadata account',
        max_length=100,
        blank=True,
    )

    raw_metadata = models.JSONField(
        verbose_name='Raw token metadata',
        default=dict,
        null=True,
        blank=True,
    )

    mint_authority = models.CharField(
        verbose_name='Mint authority',
        max_length=100,
        blank=True,
    )

    freeze_authority = models.CharField(
        verbose_name='Freeze authority',
        max_length=100,
        blank=True,
    )

    class Meta:
        verbose_name = 'token'
        verbose_name_plural = 'tokens'

    def __str__(self):
        return f'token: {self.mint_account}, symbol: {self.symbol}'
