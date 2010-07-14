from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType

from geyser.models import PublishablePermission
from geyser.tests.base import GeyserTestCase
from geyser.tests.testapp.models import TestModel1, TestModel2


class PermissionTest(GeyserTestCase):
    fixtures = ['users.json']
    
    def setUp(self):
        self.superuser = User.objects.get(pk=1)
        self.user = User.objects.get(pk=2)
        self.t1_ct = ContentType.objects.get_for_model(TestModel1)
        self.t2_ct = ContentType.objects.get_for_model(TestModel2)
    
    def test_auto_permissions(self):
        t1a = TestModel1.objects.create(
            name='test model 1 with owner "user"',
            owner=self.user
        )
        self.assertTrue(
            PublishablePermission.objects.filter(
                content_type=self.t1_ct, object_id=t1a.id, user=self.user))
        
        t1b = TestModel1.objects.create(
            name='test model 1 with owner "superuser"',
            owner=self.superuser
        )
        self.assertFalse(
            PublishablePermission.objects.filter(
                content_type=self.t1_ct, object_id=t1b.id, user=self.user))
        
        t2a = TestModel2.objects.create(name='test model 2')
        self.assertFalse(
            PublishablePermission.objects.filter(
                content_type=self.t2_ct, object_id=t2a.id, user=self.user))


__all__ = ('PermissionTest',)