from django.apps import AppConfig

class CoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'core'
    verbose_name = 'Автосалон'

    def ready(self):
        # Эта строка обязательна, чтобы заработало автоматическое обновление статуса
        import core.signals