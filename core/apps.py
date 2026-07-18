from django.apps import AppConfig


class CoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'core'

    def ready(self):
        # Start the self-contained daily trash-purge scheduler. Skip it while
        # running management commands (migrate, collectstatic, etc.) so we don't
        # spawn background threads unnecessarily during those one-off tasks.
        import sys
        if len(sys.argv) > 1 and sys.argv[1] in (
            'migrate', 'makemigrations', 'collectstatic', 'shell',
            'runserver', 'test', 'check',
        ):
            # runserver is allowed (it's a long-running dev server).
            if sys.argv[1] == 'runserver':
                self._start_scheduler()
            return
        self._start_scheduler()

    def _start_scheduler(self):
        from .scheduler import start_scheduler
        start_scheduler()
