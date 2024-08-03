from django.apps import AppConfig


class WalletConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'web.applications.wallet'

    def ready(self):
        import web.applications.wallet.signals
