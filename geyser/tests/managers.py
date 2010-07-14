from django.core.exceptions import ValidationError

from django.contrib.auth.models import User, Permission

from geyser.tests.base import GeyserTestCase
from geyser.tests.testapp.models import TestModel1, TestModel2, TestModel3
from geyser.models import Droplet


class ManagerGetListTest(GeyserTestCase):
    fixtures = ['users.json', 'objects.json', 'droplets.json']
    
    def setUp(self):        
        self.t1a = TestModel1.objects.get(pk=1)
        self.t1b = TestModel1.objects.get(pk=2)
        self.t2a = TestModel2.objects.get(pk=1)
        self.t3a = TestModel3.objects.get(pk=1)
        self.t3b = TestModel3.objects.get(pk=2)
        self.t1a_t2a = Droplet.objects.get(pk=1)
        self.t1b_t2a = Droplet.objects.get(pk=2)
        self.t1a_t3a = Droplet.objects.get(pk=3)
        self.t2a_t3a = Droplet.objects.get(pk=4)
        self.t2a_t3b_old = Droplet.objects.get(pk=5)
        self.t2a_t3b = Droplet.objects.get(pk=6)
        self.t2a_t3b_future = Droplet.objects.get(pk=7)
    
    def test_unfiltered(self):
        # unfiltered
        all_pubs = Droplet.objects.get_list()
        self.assertEqual(len(all_pubs), 4)
        #test ordering
        all_list = [self.t2a_t3a, self.t1a_t3a, self.t1b_t2a, self.t1a_t2a]
        self.assertTrue(all(p == l for (p, l) in zip(all_pubs, all_list)))
    
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
        self.assertEqual(len(t1_t2_pubs), 4)
    
        # by publishable model and publication
        t1_to_2a = Droplet.objects.get_list(publishable_models=TestModel1, publications=self.t2a)
        self.assertTrue(self.t1a_t2a in t1_to_2a)
        self.assertTrue(self.t1b_t2a in t1_to_2a)
        self.assertEqual(len(t1_to_2a), 2)
        t2_to_3a = Droplet.objects.get_list(publishable_models=TestModel2, publications=self.t3a)
        self.assertTrue(self.t2a_t3a in t2_to_3a)
        self.assertEqual(len(t2_to_3a), 1)
        
        # by publishable list and publication
        t1_t2_to_3b = Droplet.objects.get_list(publishable_models=[TestModel1, TestModel2], publications=self.t3b, include_future=True)
        self.assertTrue(self.t2a_t3b_future in t1_t2_to_3b)
        self.assertEqual(len(t1_t2_to_3b), 1)
        
        #by publishable instance
        t1a_pubs = Droplet.objects.get_list(publishable=self.t1a)
        self.assertTrue(self.t1a_t2a in t1a_pubs)
        self.assertTrue(self.t1a_t3a in t1a_pubs)
        self.assertEqual(len(t1a_pubs), 2)
    
    def test_filtered(self):
        #by year
        year_2010_kwarg = Droplet.objects.get_list(year=2010)
        self.assertTrue(self.t1a_t2a not in year_2010_kwarg)
        self.assertEqual(len(year_2010_kwarg), 3)
        year_2010_filter = Droplet.objects.get_list(filters={'published__year': 2010})
        self.assertTrue(self.t1a_t2a not in year_2010_filter)
        self.assertEqual(len(year_2010_filter), 3)
        
        #by month include old
        month_06_kwarg_old = Droplet.objects.get_list(month=6, include_old=True)
        self.assertTrue(self.t2a_t3b_old in month_06_kwarg_old)
        self.assertEqual(len(month_06_kwarg_old), 4)
        month_06_filter_old = Droplet.objects.get_list(filters={'published__month': 6}, include_old=True)
        self.assertTrue(self.t2a_t3b_old in month_06_filter_old)
        self.assertEqual(len(month_06_filter_old), 4)
        
        #include future
        month_06_future = Droplet.objects.get_list(filters={'published__month': 6}, include_future=True)
        self.assertTrue(self.t2a_t3b_future in month_06_future)
        self.assertEqual(len(month_06_future), 3)
        
        #by day kwarg
        day_27 = Droplet.objects.get_list(day=27)
        self.assertTrue(self.t2a_t3a in day_27)
        self.assertEqual(len(day_27), 1)
    
    def test_publishable_filter(self):
        #by pk
        tb_pubs = Droplet.objects.get_list(publishable_filters={'pk': 2})
        self.assertTrue(self.t1b_t2a in tb_pubs)
        self.assertEqual(len(tb_pubs), 1)
        
        #by name
        t1a_pubs = Droplet.objects.get_list(publishable_filters={'name': 'test object 1a'})
        self.assertTrue(self.t1a_t2a in t1a_pubs)
        self.assertTrue(self.t1a_t3a in t1a_pubs)
        self.assertEqual(len(t1a_pubs), 2)
        
        #by owner
        user = User.objects.get(pk=2)
        user_pubs = Droplet.objects.get_list(publishable_filters={'owner': user})
        self.assertTrue(user_pubs)
        self.assertTrue(all(d.publishable.owner == user for d in user_pubs))


class ManagerPublishTest(GeyserTestCase):
    fixtures = ['users.json', 'objects.json', 'permissions.json']
    
    def setUp(self):        
        self.t1a = TestModel1.objects.get(pk=1)
        self.t1b = TestModel1.objects.get(pk=2)
        self.t2a = TestModel2.objects.get(pk=1)
        self.t3a = TestModel3.objects.get(pk=1)
        self.t3b = TestModel3.objects.get(pk=2)
        self.user = User.objects.get(pk=2)
        add_perm = Permission.objects.get(codename='add_droplet')
        self.user.user_permissions.add(add_perm)
    
    def test_get_allowed_no_perm(self):
        self.user.user_permissions.clear()
        allowed_no_perm = Droplet.objects.get_allowed_publications(self.t1a, self.user)
        self.assertEqual(allowed_no_perm, None)

    def test_get_allowed(self):
        allowed = Droplet.objects.get_allowed_publications(self.t1a, self.user)
        self.assertTrue(self.t3a in allowed)
        self.assertTrue(self.t3b in allowed)
        self.assertEqual(len(allowed), 2)
    
    def test_get_allowed_superuser(self):
        superuser = User.objects.get(pk=1)
        allowed = Droplet.objects.get_allowed_publications(self.t1a, superuser)
        self.assertTrue(self.t2a in allowed)
        self.assertTrue(self.t3a in allowed)
        self.assertTrue(self.t3b in allowed)
        self.assertEqual(len(allowed), 3)        
    
    def test_publish_1to1(self):        
        Droplet.objects.publish(self.t1a, self.t2a, published_by=self.user)
        droplets = Droplet.objects.all()
        self.assertEqual(len(droplets), 1)
        droplet = droplets[0]
        self.assertEqual(droplet.publishable, self.t1a)
        self.assertEqual(droplet.publication, self.t2a)
        self.assertEqual(droplet.published_by, self.user)
        
    def test_publish_1to2(self):
        published = Droplet.objects.publish(self.t1a, [self.t2a, self.t3a])
        self.assertEqual(len(published), 2)
        droplets = Droplet.objects.all()
        self.assertTrue(all(d in published for d in droplets))
        self.assertEqual(len(droplets), 2)
        self.assertEqual(droplets[0].publishable, self.t1a)
        self.assertEqual(droplets[1].publishable, self.t1a)
        self.assertTrue(any(d.publication == self.t2a for d in droplets))
        self.assertTrue(any(d.publication == self.t3a for d in droplets))
    
    def test_publish_as_user(self):
        Droplet.objects.publish(self.t1a, as_user=self.user)
        droplets = Droplet.objects.all()
        self.assertEqual(len(droplets), 2)
        self.assertTrue(any(d.publication == self.t3a for d in droplets))
        self.assertTrue(any(d.publication == self.t3b for d in droplets))
        self.assertEqual(droplets[0].published_by, self.user)


class ManagerUniquenessTest(GeyserTestCase):
    def setUp(self):
        self.t2a = TestModel2.objects.create(name='an object')
        self.t2b = TestModel2.objects.create(name='an object')
        self.t3 = TestModel3.objects.create(name='t3 object')
    
    def test_unique_for_date(self):
        da = Droplet.objects.publish(publishable=self.t2a)
        self.assertRaises(ValidationError, Droplet.objects.publish, publishable=self.t2b)


class ManagerUnpublishTest(GeyserTestCase):
    fixtures = ['users.json', 'objects.json', 'permissions.json', 'droplets.json']
    
    def setUp(self):        
        self.t1a = TestModel1.objects.get(pk=1)
        self.t2a = TestModel2.objects.get(pk=1)
        self.t3a = TestModel3.objects.get(pk=1)
        self.t1a_t2a = Droplet.objects.get(pk=1)
        self.t1a_t3a = Droplet.objects.get(pk=3)

        self.user = User.objects.get(pk=2)
        add_perm = Permission.objects.get(codename='add_droplet')
        self.user.user_permissions.add(add_perm)
    
    def test_unpublish(self):
        t1a_t2a_updated = self.t1a_t2a.updated
        Droplet.objects.unpublish(self.t1a, self.t2a)
        self.t1a_t2a = Droplet.objects.get(pk=1)
        all_droplets = Droplet.objects.all()
        self.assertTrue(self.t1a_t2a in all_droplets)
        self.assertFalse(self.t1a_t2a.is_newest)
        list_droplets = Droplet.objects.get_list()
        self.assertFalse(any(d.publication == self.t2a and d.publishable == self.t1a for d in list_droplets))
        self.assertNotEqual(self.t1a_t2a.updated, t1a_t2a_updated)
        
    def test_unpublish_as_user(self):
        Droplet.objects.unpublish(self.t1a, as_user=self.user)
        droplets = Droplet.objects.get_list(publishable=self.t1a)
        self.assertFalse(self.t1a_t3a in droplets)
        self.assertTrue(self.t1a_t2a in droplets)
        self.assertEqual(len(droplets), 1)
        self.t1a_t3a = Droplet.objects.get(pk=3)
        self.assertEqual(self.t1a_t3a.updated_by, self.user)


__all__ = ('ManagerGetListTest', 'ManagerPublishTest', 'ManagerUniquenessTest', 'ManagerUnpublishTest', )