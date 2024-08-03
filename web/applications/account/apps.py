from django.apps import AppConfig


class AccountConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'web.applications.account'

    def ready(self):
        import web.applications.account.signals
