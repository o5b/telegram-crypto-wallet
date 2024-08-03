from django.contrib import admin
from django.utils.html import mark_safe
from django.contrib.auth import get_user_model

from web.applications.core.admin import CommonAdmin
from . import models

User = get_user_model()


@admin.register(models.HDWallet)
class HDWalletAdmin(CommonAdmin):
    list_display = ['first_address', 'get_users', 'name', 'status', 'created']
    list_filter = ['status']
    search_fields = ['user', 'name', 'description']
    date_hierarchy = 'created'
    ordering = ['-created']

    @admin.display(description='User')
    def get_users(self, obj):
        users = User.objects.filter(hdwallets=obj)
        if users:
            return [user for user in users]
        return None


@admin.register(models.Wallet)
class WalletAdmin(CommonAdmin):
    list_display = ['wallet_address', 'get_users', 'status', 'name', 'created']
    list_filter = ['status']
    search_fields = ['user', 'name', 'description']
    date_hierarchy = 'created'
    ordering = ['-created']

    @admin.display(description='User')
    def get_users(self, obj):
        users = User.objects.filter(wallets=obj)
        if users:
            return [user for user in users]
        return None


@admin.register(models.Transaction)
class TransactionAdmin(CommonAdmin):
    list_display = ['transaction_time', 'get_wallet', 'get_amount']
    list_filter = ['status']
    search_fields = ['transaction_id', 'sender', 'recipient']
    date_hierarchy = 'created'
    ordering = ['-transaction_time']

    def get_wallet(self, obj):
        wallet_address_list = [w.wallet_address for w in obj.wallet.all()]
        format_sender = f'{obj.sender[:4]}***{obj.sender[-4:]}'
        format_recipient = f'{obj.recipient[:4]}***{obj.recipient[-4:]}'

        if obj.sender in wallet_address_list:
            wallet = obj.wallet.filter(wallet_address=obj.sender).first()
            res_sender = f'&ensp;&ensp;&ensp;<a href="/admin/wallet/wallet/{wallet.id}/change/" target="_blank">{format_sender}</a>'
        else:
            res_sender = '&ensp;&ensp;&ensp;' + format_sender

        if obj.recipient in wallet_address_list:
            wallet = obj.wallet.filter(wallet_address=obj.recipient).first()
            res_recipient = f'<a href="/admin/wallet/wallet/{wallet.id}/change/" target="_blank">{format_recipient}</a>'
        else:
            res_recipient = format_recipient

        return mark_safe(res_sender + '&ensp;|&ensp;' + res_recipient)
    get_wallet.short_description = 'wallets: sender | recipient'

    def get_amount(self, obj):
        amount = obj.pre_balances - obj.post_balances
        return f'{amount:_}'
    get_amount.short_description = 'Amount'


@admin.register(models.Token)
class TokenAdmin(CommonAdmin):
    list_display = ['mint_account', 'symbol', 'name', 'decimals', 'state', 'status', 'created']
    list_filter = ['status', 'state']
    search_fields = ['mint_account', 'symbol', 'name']
    date_hierarchy = 'created'
    ordering = ['-created']
