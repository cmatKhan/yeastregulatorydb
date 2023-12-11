from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class UsersConfig(AppConfig):
    name = "yeastregulatorydb.users"
    verbose_name = _("Users")

    def ready(self):
        try:
            import yeastregulatorydb.users.signals  # noqa: F401  #type: ignore
        except ImportError:
            pass
