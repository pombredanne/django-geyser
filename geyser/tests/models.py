from django.contrib.contenttypes.models import ContentType
from django.contrib.auth.models import User

from geyser.tests.base import GeyserTestCase
from geyser.tests.testapp.models import TestModel1, TestModel2

from geyser.models import Droplet, DropletFirst


class ModelTest(GeyserTestCase):
    fixtures = ['users.json', 'objects.json']
    
    def setUp(self):
        self.superuser = User.objects.get(pk=1)
        self.user = User.objects.get(pk=2)
        self.t1 = TestModel1.objects.get(pk=1)
        self.t2 = TestModel2.objects.get(pk=1)
    
    def test_remove_newest(self):
        droplet1 = Droplet(
            publishable=self.t1,
            publication=self.t2,
            published_by=self.user
        )
        droplet1.save()
        droplet1_updated = droplet1.updated
        self.assertTrue(droplet1.is_newest)
        droplet2 = Droplet(
            publishable=self.t1,
            publication=self.t2,
            published_by=self.user
        )
        droplet2.save()
        self.assertTrue(droplet2.is_newest)
        droplet1 = Droplet.objects.get(pk=droplet1.pk)
        self.assertFalse(droplet1.is_newest)
        self.assertNotEqual(droplet1_updated, droplet1.updated)
    
    def test_first_publish(self):
        droplet1 = Droplet(
            publishable=self.t1,
            publication=self.t2,
            published_by=self.user
        )
        droplet1.save()
        self.assertEqual(droplet1.first.published, droplet1.published)
        self.assertEqual(droplet1.first.published_by, self.user)
        
        first1 = DropletFirst.objects.get(
            publishable_type=ContentType.objects.get_for_model(TestModel1),
            publishable_id=1
        )
        self.assertEqual(droplet1.first, first1)
        
        droplet2 = Droplet(
            publishable=self.t1,
            publication=self.t2,
            published_by=self.superuser
        )
        droplet2.save()
        self.assertEqual(droplet2.first, droplet1.first)
        
        first1 = DropletFirst.objects.get(
            publishable_type=ContentType.objects.get_for_model(TestModel1),
            publishable_id=1
        )
        self.assertEqual(first1.published_by, self.user)


__all__ = ('ModelTest',)