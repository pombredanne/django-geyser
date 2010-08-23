from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType

from rubberstamp.models import AppPermission

from geyser.tests.base import GeyserTestCase
from geyser.tests.testapp.models import TestModel1, TestModel2, TestModel3


class PermissionTest(GeyserTestCase):
    fixtures = ['users.json']
    
    def setUp(self):
        self.superuser = User.objects.get(pk=1)
        self.user = User.objects.get(pk=2)
        self.t1_ct = ContentType.objects.get_for_model(TestModel1)
        self.t2_ct = ContentType.objects.get_for_model(TestModel2)
        self.t3_ct = ContentType.objects.get_for_model(TestModel3)
    
    def test_app_permissions(self):
        perms = AppPermission.objects.all()
        self.assertEqual(len(perms), 2)
        
        publish_perm = perms.get(codename='publish')
        publish_types = publish_perm.content_types.all()
        self.assertTrue(self.t1_ct in publish_types)
        self.assertTrue(self.t2_ct in publish_types)
        
        publish_to_perm = perms.get(codename='publish_to')
        publish_to_types = publish_to_perm.content_types.all()
        self.assertTrue(self.t2_ct in publish_to_types)
        self.assertTrue(self.t3_ct in publish_to_types)
    
    def test_auto_permissions(self):
        t1a = TestModel1.objects.create(
            name='test model 1 with owner "user"',
            owner=self.user
        )
        self.assertTrue(self.user.has_perm('geyser.publish', obj=t1a))
        
        t1b = TestModel1.objects.create(
            name='test model 1 with owner "superuser"',
            owner=self.superuser
        )
        self.assertFalse(self.user.has_perm('geyser.publish', obj=t1b))
        
        t2a = TestModel2.objects.create(name='test model 2')
        self.assertFalse(self.user.has_perm('geyser.publish', obj=t2a))


__all__ = ('PermissionTest',)