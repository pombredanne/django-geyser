from datetime import datetime

from django.conf import settings

from geyser.tests.base import GeyserTestCase
from geyser.tests.testapp.models import TestModel1, TestModel2, TestModel3

from geyser.models import Droplet


class ManagerTest(GeyserTestCase):
    fixtures = ['test_objects.json', 'test_droplets.json']
    
    def setUp(self):
        settings.GEYSER_PUBLISHABLES = {
            'testapp.testmodel1': {
                'publish_to': ('testapp.testmodel2', 'testapp.testmodel3'),
                'auto_perms': ('owner',),
                'unique_for_date': ('name',),
            },
            'testapp.testmodel2': {
                'publish_to': ('testapp.testmodel3',),
                'list_annotations': {
                    'published': 'pub_date',
                    'publication': 'pub_on'
                }
            }
        }
        self.t1a = TestModel1.objects.get(pk=1)
        self.t1b = TestModel1.objects.get(pk=2)
        self.t2a = TestModel2.objects.get(pk=1)
        self.t3a = TestModel3.objects.get(pk=1)
        self.t3b = TestModel3.objects.get(pk=2)
        self.t1a_t2a = Droplet.objects.get(pk=1)
        self.t1b_t2a = Droplet.objects.get(pk=2)
        self.t1a_t3a = Droplet.objects.get(pk=3)
        self.t2a_t3a = Droplet.objects.get(pk=4)
        self.t2a_t3b = Droplet.objects.get(pk=5)
    
    def test_get_list(self):
        # unfiltered
        all_pubs = Droplet.objects.get_list()
        self.assertEqual(all_pubs.count(), 5)
    
        # by publication
        to_3a = Droplet.objects.get_list(publications=self.t3a)
        self.assertTrue(self.t1a_t3a in to_3a)
        self.assertTrue(self.t2a_t3a in to_3a)
        self.assertEqual(len(to_3a), 2)
    
        # by publication list
        to_2a_or_3a = Droplet.objects.get_list(publications=[self.t2a, self.t3a])
        self.assertTrue(self.t1a_t2a in to_2a_or_3a)
        self.assertTrue(self.t1b_t2a in to_2a_or_3a)
        self.assertTrue(self.t1a_t3a in to_2a_or_3a)
        self.assertTrue(self.t2a_t3a in to_2a_or_3a)
        self.assertEqual(len(to_2a_or_3a), 4)                
    
        # by publishable model
        t1_pubs = Droplet.objects.get_list(publishable_models=TestModel1)
        self.assertTrue(self.t1a_t2a in t1_pubs)
        self.assertTrue(self.t1b_t2a in t1_pubs)
        self.assertTrue(self.t1a_t3a in t1_pubs)
        self.assertEqual(len(t1_pubs), 3)
    
        # by publishable model list
        t1_t2_pubs = Droplet.objects.get_list(publishable_models=[TestModel1, TestModel2])
        self.assertEqual(len(t1_t2_pubs), 5)
    
        # by publishable model and publication
        t1_to_2a = Droplet.objects.get_list(publishable_models=TestModel1, publications=self.t2a)
        self.assertTrue(self.t1a_t2a in t1_to_2a)
        self.assertTrue(self.t1b_t2a in t1_to_2a)
        self.assertEqual(len(t1_to_2a), 2)
        t2_to_3a = Droplet.objects.get_list(publishable_models=TestModel2, publications=self.t3a)
        self.assertTrue(self.t2a_t3a in t2_to_3a)
        self.assertEqual(len(t2_to_3a), 1)
        
        # by publishable list and publication
        t1_t2_to_3b = Droplet.objects.get_list(publishable_models=[TestModel1, TestModel2], publications=self.t3b)
        self.assertTrue(self.t2a_t3b in t1_t2_to_3b)
        self.assertEqual(len(t1_t2_to_3b), 1)
    
    def test_get_publishable_list(self):
        # should not be able to pass list of publishables
        self.assertRaises(TypeError,
            Droplet.objects.get_publishable_list, publishable_model=[TestModel1, TestModel2])
        
        # by publication
        t1_on_t2a = Droplet.objects.get_publishable_list(publishable_model=TestModel1, publications=self.t2a)
        self.assertTrue(self.t1a in t1_on_t2a)
        self.assertTrue(self.t1b in t1_on_t2a)
        self.assertEqual(len(t1_on_t2a), 2)
        self.assertTrue(isinstance(t1_on_t2a[0].published, datetime))
        self.assertEqual(t1_on_t2a[0].publication, self.t2a)
        self.assertTrue(isinstance(t1_on_t2a[1].published, datetime))
        self.assertEqual(t1_on_t2a[1].publication, self.t2a)


__all__ = ('ManagerTest',)