from django.apps import AppConfig

class CoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'core'
    verbose_name = 'Автосалон'

    def ready(self):
        # Подключаем сигналы (аналог триггеров БД)
        import core.signals