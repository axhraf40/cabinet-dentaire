from django.apps import AppConfig


class GestionCabinetConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'gestion_cabinet'

    def ready(self):
        from .admin_config import configure_admin
        configure_admin()
