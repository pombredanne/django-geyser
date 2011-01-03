from django.contrib.contenttypes.models import ContentType
from django.contrib.auth.models import User

from geyser.tests.base import GeyserTestCase
from geyser.tests.testapp.models import TestModel1, TestModel2

from geyser.models import Droplet, Stream


class DropletTests(GeyserTestCase):
    fixtures = ['users.json', 'objects.json']
    
    def setUp(self):
        self.superuser = User.objects.get(pk=1)
        self.user = User.objects.get(pk=2)
        self.t1 = TestModel1.objects.get(pk=1)
        self.stream = Stream.objects.create()
    
    def test_remove_newest(self):
        droplet1 = Droplet(
            content_object=self.t1,
            stream=self.stream,
            published_by=self.user
        )
        droplet1.save()
        droplet1_updated = droplet1.updated
        self.assertTrue(droplet1.is_current)
        droplet2 = Droplet(
            content_object=self.t1,
            stream=self.stream,
            published_by=self.user
        )
        droplet2.save()
        self.assertTrue(droplet2.is_current)
        droplet1 = Droplet.objects.get(pk=droplet1.pk)
        self.assertFalse(droplet1.is_current)
        self.assertNotEqual(droplet1_updated, droplet1.updated)
    
    def test_first_publish(self):
        droplet1 = Droplet(
            content_object=self.t1,
            stream=self.stream,
            published_by=self.user
        )
        droplet1.save()
        self.assertEqual(droplet1.first.published, droplet1.published)
        self.assertEqual(droplet1.first.published_by, self.user)
        
        self.assertEqual(droplet1.first, droplet1)
        
        droplet2 = Droplet(
            content_object=self.t1,
            stream=self.stream,
            published_by=self.superuser
        )
        droplet2.save()
        self.assertEqual(droplet2.first, droplet1.first)
        
        self.assertEqual(droplet2.first.published_by, self.user)


class StreamTests(GeyserTestCase):
    fixtures = ['users.json', 'objects.json', 'streams.json', 'droplets.json']
    
    def test_droplet_list(self):
        stream = Stream.objects.get(pk=1)
        droplets = stream.droplets.get_list()
        self.assertEqual(len(droplets), 3)


__all__ = ('DropletTests', 'StreamTests')
