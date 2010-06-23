from django.conf import settings
from django.core.management import call_command

import authority

from geyser.tests.base import GeyserTestCase
from geyser.tests.testapp.models import TestModel1, TestModel2, TestModel3

class PermissionTest(GeyserTestCase):
    def setUp(self):
        settings.GEYSER_PUBLISHABLES = {
            'testapp.testmodel1': {
                'publish_to': ('testapp.testmodel2',),
                'auto_perms': ('owner',),
                'unique_for_date': ('name',),
            },
            'testapp.testmodel2': {
                'publish_to': ('testapp.testmodel3',),
            }
        }
        authority.autodiscover()
    def test_publishable_permission(self):
        permission_list = authority.sites.site.get_permissions_by_model(TestModel1)
        self.assertTrue(permission_list)
        permission = permission_list[0]
        self.assertEqual(permission.__name__, 'TestModel1Permission')
        self.assertEqual(permission.label, 'testmodel1_permission')
        self.assertTrue('publish_testmodel1' in permission.checks)
        self.assertEqual(len(permission.checks), 5)
    def test_publication_permission(self):
        permission_list = authority.sites.site.get_permissions_by_model(TestModel3)
        self.assertTrue(permission_list)
        permission = permission_list[0]
        self.assertEqual(permission.__name__, 'TestModel3Permission')
        self.assertEqual(permission.label, 'testmodel3_permission')
        self.assertTrue('publish_testmodel2_to_testmodel3' in permission.checks)
        self.assertEqual(len(permission.checks), 5)
    def test_both_permission(self):
        permission_list = authority.sites.site.get_permissions_by_model(TestModel2)
        self.assertTrue(permission_list)
        permission = permission_list[0]
        self.assertEqual(permission.__name__, 'TestModel2Permission')
        self.assertEqual(permission.label, 'testmodel2_permission')
        self.assertTrue('publish_testmodel2' in permission.checks)
        self.assertTrue('publish_testmodel1_to_testmodel2' in permission.checks)
        self.assertEqual(len(permission.checks), 6)        

__all__ = ('PermissionTest',)