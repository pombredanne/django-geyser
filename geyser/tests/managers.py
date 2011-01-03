from datetime import datetime

from django.core.exceptions import ValidationError, ImproperlyConfigured

from django.conf import settings
from django.db import connection, reset_queries
from django.contrib.auth.models import User, Permission

from geyser.tests.base import GeyserTestCase
from geyser.tests.testapp.models import TestModel1, TestModel2, TestModel3
from geyser.models import Droplet, Stream


class DropletManagerGetListTest(GeyserTestCase):
    fixtures = ['users.json', 'objects.json', 'streams.json', 'droplets.json']
    
    def setUp(self):        
        self.t1a = TestModel1.objects.get(pk=1)
        self.t1b = TestModel1.objects.get(pk=2)
        self.t2a = TestModel2.objects.get(pk=1)
        self.t3a = TestModel3.objects.get(pk=1)
        self.s1 = Stream.objects.get(pk=1)
        self.s2 = Stream.objects.get(pk=2)
        self.s3 = Stream.objects.get(pk=3)
        self.t1a_s1 = Droplet.objects.get(pk=1)
        self.t1b_s1 = Droplet.objects.get(pk=2)
        self.t1a_s2 = Droplet.objects.get(pk=3)
        self.t2a_s3 = Droplet.objects.get(pk=4)
        self.t3a_s1 = Droplet.objects.get(pk=5)
        self.t2a_s1_unpublished = Droplet.objects.get(pk=6)
        self.t2a_s1_future = Droplet.objects.get(pk=7)
    
    def test_unfiltered(self):
        # unfiltered
        all_pubs = Droplet.objects.get_list()
        self.assertEqual(len(all_pubs), 5)
        #test ordering (reverse publish date)
        all_list = [self.t3a_s1, self.t2a_s3, self.t1a_s2, self.t1b_s1, self.t1a_s1]
        self.assertTrue(all(p == l for (p, l) in zip(all_pubs, all_list)))
    
        # by publication
        to_s1 = Droplet.objects.get_list(stream=self.s1)
        self.assertTrue(self.t1a_s1 in to_s1)
        self.assertTrue(self.t1b_s1 in to_s1)
        self.assertTrue(self.t3a_s1 in to_s1)
        self.assertEqual(len(to_s1), 3)
    
        # by publication list
        to_s2_or_s3 = Droplet.objects.get_list(stream=[self.s2, self.s3])
        self.assertTrue(self.t1a_s2 in to_s2_or_s3)
        self.assertTrue(self.t2a_s3 in to_s2_or_s3)
        self.assertEqual(len(to_s2_or_s3), 2)                
    
        # by publishable model
        t1_pubs = Droplet.objects.get_list(models=TestModel1)
        self.assertTrue(self.t1a_s1 in t1_pubs)
        self.assertTrue(self.t1b_s1 in t1_pubs)
        self.assertTrue(self.t1a_s2 in t1_pubs)
        self.assertEqual(len(t1_pubs), 3)
    
        # by publishable model list
        t1_t2_pubs = Droplet.objects.get_list(models=[TestModel1, TestModel2])
        self.assertEqual(len(t1_t2_pubs), 4)
    
        # by publishable model and publication
        t1_to_s1 = Droplet.objects.get_list(models=TestModel1, stream=self.s1)
        self.assertTrue(self.t1a_s1 in t1_to_s1)
        self.assertTrue(self.t1b_s1 in t1_to_s1)
        self.assertEqual(len(t1_to_s1), 2)
        t2_to_s3 = Droplet.objects.get_list(models=TestModel2, stream=self.s3)
        self.assertTrue(self.t2a_s3 in t2_to_s3)
        self.assertEqual(len(t2_to_s3), 1)
        
        # by publishable list and publication
        t1_t3_to_s1 = Droplet.objects.get_list(models=[TestModel1, TestModel3], stream=self.s1)
        self.assertTrue(self.t1a_s1 in t1_t3_to_s1)
        self.assertTrue(self.t1b_s1 in t1_t3_to_s1)
        self.assertTrue(self.t3a_s1 in t1_t3_to_s1)
        self.assertEqual(len(t1_t3_to_s1), 3)
        
        #by publishable instance
        t1a_pubs = Droplet.objects.get_list(obj=self.t1a)
        self.assertTrue(self.t1a_s1 in t1a_pubs)
        self.assertTrue(self.t1a_s2 in t1a_pubs)
        self.assertEqual(len(t1a_pubs), 2)
    
    def test_filtered(self):
        #by year
        year_2010_kwarg = Droplet.objects.get_list(year=2010)
        self.assertTrue(self.t1a_s1 not in year_2010_kwarg)
        self.assertEqual(len(year_2010_kwarg), 4)
        year_2010_filter = Droplet.objects.get_list(filters={'published__year': 2010})
        self.assertTrue(self.t1a_s1 not in year_2010_filter)
        self.assertEqual(len(year_2010_filter), 4)
        
        #by month include unpublished
        month_06_kwarg_unpublished = Droplet.objects.get_list(month=6, include_unpublished=True)
        self.assertTrue(self.t2a_s1_unpublished in month_06_kwarg_unpublished)
        self.assertEqual(len(month_06_kwarg_unpublished), 3)
        month_06_filter_unpublished = Droplet.objects.get_list(filters={'published__month': 6}, include_unpublished=True)
        self.assertTrue(self.t2a_s1_unpublished in month_06_filter_unpublished)
        self.assertEqual(len(month_06_filter_unpublished), 3)
        
        #include future
        month_06_future = Droplet.objects.get_list(filters={'published__month': 6}, include_future=True)
        self.assertTrue(self.t2a_s1_future in month_06_future)
        self.assertEqual(len(month_06_future), 3)
        
        #by day kwarg
        day_27 = Droplet.objects.get_list(day=27)
        self.assertTrue(self.t2a_s3 in day_27)
        self.assertEqual(len(day_27), 1)
    
    def test_publishable_filter(self):
        #by pk
        tb_pubs = Droplet.objects.get_list(obj_filters={'pk': 2})
        self.assertTrue(self.t1b_s1 in tb_pubs)
        self.assertEqual(len(tb_pubs), 1)
        
        #by name
        t1a_pubs = Droplet.objects.get_list(obj_filters={'name': 'test object 1a'})
        self.assertTrue(self.t1a_s1 in t1a_pubs)
        self.assertTrue(self.t1a_s2 in t1a_pubs)
        self.assertEqual(len(t1a_pubs), 2)
        
        #by owner
        user = User.objects.get(pk=2)
        user_pubs = Droplet.objects.get_list(obj_filters={'owner': user})
        self.assertTrue(user_pubs)
        self.assertTrue(all(d.content_object.owner == user for d in user_pubs))


class DropletManagerSelectRelatedTest(GeyserTestCase):
    fixtures = ['users.json', 'objects.json', 'streams.json', 'droplets.json']
    
    def setUp(self):
        settings.DEBUG = True
        reset_queries()
    
    def tearDown(self):
        settings.DEBUG = False
    
    def test_select_related(self):
        t1_pubs = list(Droplet.objects.get_list(models=TestModel1))
        query_count = len(connection.queries)
        for droplet in t1_pubs:
            droplet.first
            droplet.content_object
            droplet.stream
        self.assertEqual(len(connection.queries), query_count)


class DropletManagerPermissionsTest(GeyserTestCase):
    fixtures = ['users.json', 'objects.json', 'streams.json', 'permissions.json']
    
    def setUp(self):        
        self.t1a = TestModel1.objects.get(pk=1)
        self.t1b = TestModel1.objects.get(pk=2)
        self.s1 = Stream.objects.get(pk=1)
        self.s2 = Stream.objects.get(pk=2)
        self.s3 = Stream.objects.get(pk=3)
    
    def test_get_allowed(self):
        user = User.objects.get(pk=2)
        allowed = Droplet.objects.get_allowed_publications(self.t1a, user)
        self.assertTrue(self.s1 in allowed)
        self.assertEqual(len(allowed), 1)
        allowed = Droplet.objects.get_allowed_publications(self.t1b, user)
        self.assertTrue(self.s1 in allowed)
        self.assertEqual(len(allowed), 1)
    
    def test_get_allowed_inactive(self):
        user = User.objects.get(pk=3)
        allowed = Droplet.objects.get_allowed_publications(self.t1a, user)
        self.assertEqual(allowed, None)
    
    def test_get_allowed_no_perm(self):
        user = User.objects.get(pk=4)
        allowed = Droplet.objects.get_allowed_publications(self.t1a, user)
        self.assertEqual(allowed, None)
    
    def test_get_allowed_without_publishable_object(self):
        user = User.objects.get(pk=6)
        allowed = Droplet.objects.get_allowed_publications(self.t1a, user)
        self.assertEqual(allowed, None)
    
    def test_get_allowed_without_publication_object(self):
        user = User.objects.get(pk=7)
        allowed = Droplet.objects.get_allowed_publications(self.t1a, user)
        self.assertEqual(list(allowed), [])
    
    def test_get_allowed_superuser(self):
        superuser = User.objects.get(pk=1)
        allowed = Droplet.objects.get_allowed_publications(self.t1a, superuser)
        self.assertTrue(self.s1 in allowed)
        self.assertTrue(self.s2 in allowed)
        self.assertTrue(self.s3 in allowed)
        self.assertEqual(len(allowed), 3)
    
    def test_get_allowed_not_in_settings(self):
        user = User.objects.get(pk=2)
        self.assertRaises(ImproperlyConfigured, Droplet.objects.get_allowed_publications, user, user)
    
    def test_get_allowed_with_publishable_object(self):
        user = User.objects.get(pk=9)
        allowed = Droplet.objects.get_allowed_publications(self.t1a, user)
        self.assertTrue(self.s1 in allowed)
        self.assertEqual(len(allowed), 1)
        allowed = Droplet.objects.get_allowed_publications(self.t1b, user)
        self.assertEqual(allowed, None)


class DropletManagerPublishTest(GeyserTestCase):
    fixtures = ['users.json', 'objects.json', 'streams.json', 'permissions.json']
    
    def setUp(self):        
        self.t1a = TestModel1.objects.get(pk=1)
        self.s1 = Stream.objects.get(pk=1)
        self.s2 = Stream.objects.get(pk=2)
        self.user = User.objects.get(pk=2)
    
    def test_publish_1to1(self):        
        Droplet.objects.publish(self.t1a, self.s1, published_by=self.user)
        droplets = Droplet.objects.all()
        self.assertEqual(len(droplets), 1)
        droplet = droplets[0]
        self.assertEqual(droplet.content_object, self.t1a)
        self.assertEqual(droplet.stream, self.s1)
        self.assertEqual(droplet.published_by, self.user)
        
    def test_publish_1to2(self):
        published = Droplet.objects.publish(self.t1a, [self.s1, self.s2])
        self.assertEqual(len(published), 2)
        droplets = Droplet.objects.all()
        self.assertTrue(all(d in published for d in droplets))
        self.assertEqual(len(droplets), 2)
        self.assertTrue(all(d.content_object == self.t1a for d in droplets))
        self.assertTrue(any(d.stream == self.s1 for d in droplets))
        self.assertTrue(any(d.stream == self.s2 for d in droplets))
    
    def test_publish_as_user(self):
        Droplet.objects.publish(self.t1a, as_user=self.user)
        droplets = Droplet.objects.all()
        self.assertEqual(len(droplets), 1)
        self.assertTrue(any(d.stream == self.s1 for d in droplets))
        self.assertFalse(any(d.stream == self.s2 for d in droplets))
        self.assertEqual(droplets[0].published_by, self.user)
    
    def test_publish_with_date(self):
        Droplet.objects.publish(self.t1a, self.s1, published=datetime(2010, 7, 1))
        droplet = Droplet.objects.all()[0]
        self.assertEqual(droplet.published, datetime(2010, 7, 1))


class DropletManagerUniquenessTest(GeyserTestCase):
    def setUp(self):
        self.t2a = TestModel2.objects.create(name='an object')
        self.t2b = TestModel2.objects.create(name='an object')
        self.s1 = Stream.objects.create()
    
    def test_first_publish(self):
        da = Droplet.objects.publish(self.t2a)
        self.assertRaises(ValidationError, Droplet.objects.publish, self.t2b)
    
    def test_later_publish(self):
        d = Droplet.objects.create(
            content_object=self.t2a,
            stream=self.s1,
            published=datetime(2010, 7, 21)
        )
        da = Droplet.objects.publish(self.t2a)
        Droplet.objects.publish(self.t2b)


class DropletManagerUnpublishTest(GeyserTestCase):
    fixtures = ['users.json', 'objects.json', 'streams.json', 'droplets.json', 'permissions.json']
    
    def setUp(self):        
        self.t1a = TestModel1.objects.get(pk=1)
        self.s1 = Stream.objects.get(pk=1)
        self.t1a_s1 = Droplet.objects.get(pk=1)
        self.t1a_s2 = Droplet.objects.get(pk=3)

        self.user = User.objects.get(pk=2)
    
    def test_unpublish(self):
        t1a_s1_updated = self.t1a_s1.updated
        Droplet.objects.unpublish(self.t1a, self.s1)
        self.t1a_s1 = Droplet.objects.get(pk=1)
        all_droplets = Droplet.objects.all()
        self.assertTrue(self.t1a_s1 in all_droplets)
        self.assertFalse(self.t1a_s1.is_current)
        list_droplets = Droplet.objects.get_list()
        self.assertFalse(any(d.stream == self.s1 and d.content_object == self.t1a for d in list_droplets))
        self.assertNotEqual(self.t1a_s1.updated, t1a_s1_updated)
        
    def test_unpublish_as_user(self):
        Droplet.objects.unpublish(self.t1a, as_user=self.user)
        droplets = Droplet.objects.get_list(obj=self.t1a)
        self.assertFalse(self.t1a_s1 in droplets)
        self.assertTrue(self.t1a_s2 in droplets)
        self.assertEqual(len(droplets), 1)
        self.t1a_s2 = Droplet.objects.get(pk=3)
        self.assertEqual(self.t1a_s2.updated_by, self.user)


__all__ = (
    'DropletManagerGetListTest',
    'DropletManagerSelectRelatedTest',
    'DropletManagerPermissionsTest',
    'DropletManagerPublishTest',
    'DropletManagerUniquenessTest',
    'DropletManagerUnpublishTest',
)
