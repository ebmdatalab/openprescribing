from django.apps import AppConfig


class FrontendConfig(AppConfig):
    """An appconfig to wire up our receiver handlers.

    Per best-practice documented in
    https://docs.djangoproject.com/en/1.8/topics/signals/#connecting-receiver-functions

    """

    name = "frontend"

    def ready(self):
        # Importing this to run the @admin.register decorators
        from . import admin  # noqa: F401

        # Importing this to run the signal handler decorators
        import frontend.signals.handlers  # noqa: F401
