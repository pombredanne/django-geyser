import os

from django.conf import settings
from django.core.management import call_command
from django.db.models import loading
from django.test import TestCase

import authority


class GeyserTestCase(TestCase):
    def _pre_setup(self):
        self._original_template_dirs = settings.TEMPLATE_DIRS
        settings.TEMPLATE_DIRS = list(settings.TEMPLATE_DIRS)
        settings.TEMPLATE_DIRS.append(os.path.join(os.path.dirname(__file__), 'templates'))
        
        self._original_fixture_dirs = settings.FIXTURE_DIRS
        settings.FIXTURE_DIRS = list(settings.FIXTURE_DIRS)
        settings.FIXTURE_DIRS.append(os.path.join(os.path.dirname(__file__), 'fixtures'))
        
        self._original_installed_apps = settings.INSTALLED_APPS
        settings.INSTALLED_APPS = list(settings.INSTALLED_APPS)
        settings.INSTALLED_APPS.append('geyser.tests.testapp')
        loading.cache.loaded = False
        call_command('syncdb', interactive=False, verbosity=0)
        
        self._original_geyser = getattr(settings, 'GEYSER_PUBLISHABLES', {})
        settings.GEYSER_PUBLISHABLES = {
            'testapp.testmodel1': {
                'publish_to': ('testapp.testmodel2', 'testapp.testmodel3'),
                'auto_perms': ('owner',),
            },
            'testapp.testmodel2': {
                'publish_to': ('testapp.testmodel3',),
                'unique_for_date': ('name',),
            }
        }
        authority.autodiscover()
        
        super(TestCase, self)._pre_setup()
    
    def _post_teardown(self):
        super(TestCase, self)._post_teardown()
        settings.GEYSER_PUBLISHABLES = self._original_geyser
        settings.INSTALLED_APPS = self._original_installed_apps
        settings.FIXTURE_DIRS = self._original_fixture_dirs
        settings.TEMPLATE_DIRS = self._original_template_dirs
        loading.cache.loaded = False