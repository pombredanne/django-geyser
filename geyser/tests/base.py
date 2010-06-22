from django.conf import settings
from django.core.management import call_command
from django.db.models import loading
from django.test import TestCase

class GeyserTestCase(TestCase):
    apps = ('geyser.tests.testapp',)

    def _pre_setup(self):
        self._original_installed_apps = settings.INSTALLED_APPS
        settings.INSTALLED_APPS = list(settings.INSTALLED_APPS)
        for app in self.apps:
            settings.INSTALLED_APPS.append(app)
        loading.cache.loaded = False
        call_command('syncdb', interactive=False, verbosity=0)
        
        if hasattr(settings, 'GEYSER_PUBLISH_SETTINGS'):
            self._geyser_settings = settings.GEYSER_PUBLISH_SETTINGS
            del settings.GEYSER_PUBLISH_SETTINGS
        
        super(TestCase, self)._pre_setup()
    
    def _post_teardown(self):
        super(TestCase, self)._post_teardown()
        
        if hasattr(self, '_geyser_settings'):
            settings.GEYSER_PUBLISH_SETTINGS = self._geyser_settings
        
        settings.INSTALLED_APPS = self._original_installed_apps
        loading.cache.loaded = False