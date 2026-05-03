from django.apps import AppConfig


class CommerceConfig(AppConfig):
    name = 'commerce'

    def ready(self):
        import commerce.signals