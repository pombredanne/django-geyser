from django.conf import settings

from django.contrib.contenttypes.models import ContentType

from geyser.tests.base import GeyserTestCase
from geyser.tests.testapp.models import TestModel1, TestModel2

from geyser.models import Droplet


class ModelTest(GeyserTestCase):
    fixtures = ['test_objects.json']
    
    def setUp(self):
        settings.GEYSER_PUBLISHABLES = {
            'testapp.testmodel1': {
                'publish_to': ('testapp.testmodel2',),
                'unique_for_date': ('name',),
            },
            'testapp.testmodel2': {
                'publish_to': ('testapp.testmodel3',),
            }
        }
        self.t1 = TestModel1.objects.get(pk=1)
        self.t2 = TestModel2.objects.get(pk=1)
    
    def test_remove_newest(self):
        droplet1 = Droplet(
            publishable=self.t1,
            publication=self.t2
        )
        droplet1.save()
        droplet1_updated = droplet1.updated
        self.assertTrue(droplet1.is_newest)
        droplet2 = Droplet(
            publishable=self.t1,
            publication=self.t2
        )
        droplet2.save()
        self.assertTrue(droplet2.is_newest)
        droplet1 = Droplet.objects.get(pk=droplet1.pk)
        self.assertFalse(droplet1.is_newest)
        self.assertNotEqual(droplet1_updated, droplet1.updated)


__all__ = ('ModelTest',)