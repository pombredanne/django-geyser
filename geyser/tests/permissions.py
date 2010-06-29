from django.conf import settings

from django.contrib.auth.models import User

import authority
from authority.sites import site

from geyser.tests.base import GeyserTestCase
from geyser.tests.testapp.models import TestModel1, TestModel2, TestModel3


class PermissionTest(GeyserTestCase):
    fixtures = ['users.json']
    
    def setUp(self):
        settings.GEYSER_PUBLISHABLES = {
            'testapp.testmodel1': {
                'publish_to': ('testapp.testmodel2',),
                'auto_perms': ('owner',),
            },
            'testapp.testmodel2': {
                'publish_to': ('testapp.testmodel3',),
            }
        }
        authority.autodiscover()
    
    def test_publishable_permission(self):
        permission_list = site.get_permissions_by_model(TestModel1)
        self.assertTrue(permission_list)
        permission = permission_list[0]
        self.assertEqual(permission.__name__, 'TestModel1Permission')
        self.assertEqual(permission.label, 'testmodel1_permission')
        self.assertTrue('publish_testmodel1' in permission.checks)
        self.assertEqual(len(permission.checks), 5)
    
    def test_publication_permission(self):
        permission_list = site.get_permissions_by_model(TestModel3)
        self.assertTrue(permission_list)
        permission = permission_list[0]
        self.assertEqual(permission.__name__, 'TestModel3Permission')
        self.assertEqual(permission.label, 'testmodel3_permission')
        self.assertTrue('publish_testmodel2_to_testmodel3' in permission.checks)
        self.assertEqual(len(permission.checks), 5)
    
    def test_both_permission(self):
        permission_list = site.get_permissions_by_model(TestModel2)
        self.assertTrue(permission_list)
        permission = permission_list[0]
        self.assertEqual(permission.__name__, 'TestModel2Permission')
        self.assertEqual(permission.label, 'testmodel2_permission')
        self.assertTrue('publish_testmodel2' in permission.checks)
        self.assertTrue('publish_testmodel1_to_testmodel2' in permission.checks)
        self.assertEqual(len(permission.checks), 6)
    
    def test_auto_permissions(self):
        superuser = User.objects.get(pk=1)
        user = User.objects.get(pk=2)
        t1_permission = site.get_permissions_by_model(TestModel1)[0]
        user_t1_check = t1_permission(user)
        t2_permission = site.get_permissions_by_model(TestModel2)[0]
        user_t2_check = t2_permission(user)
        t1a = TestModel1.objects.create(
            name='test model with owner "user"',
            owner=user
        )
        self.assertTrue(user_t1_check.has_perm('testmodel1_permission.publish_testmodel1', t1a))
        t1b = TestModel1.objects.create(
            name='test model with owner "user"',
            owner=superuser
        )
        self.assertFalse(user_t1_check.has_perm('testmodel1_permission.publish_testmodel1', t1b))
        t2a = TestModel2.objects.create(name='test model with owner "user"')
        self.assertFalse(user_t2_check.has_perm('testmodel1_permission.publish_testmodel1', t2a))


__all__ = ('PermissionTest',)