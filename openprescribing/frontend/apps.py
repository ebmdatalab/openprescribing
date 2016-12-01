from django.apps import AppConfig


class FrontendConfig(AppConfig):
    """An appconfig to wire up our receiver handlers.

    Per best-practice documented in
    https://docs.djangoproject.com/en/1.8/topics/signals/#connecting-receiver-functions

    """
    name = 'frontend'

    def ready(self):
        import admin
        import frontend.signals.handlers
