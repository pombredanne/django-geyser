from timeit import default_timer as now

from django.conf import settings
from django.db import connection, reset_queries

from geyser.query import GenericQuerySet
from geyser.models import Droplet
from geyser.tests.base import GeyserTestCase, NUM_RELATED_TYPES
from geyser.tests.testapp.models import TestModel1


class QuerySetTestCase(GeyserTestCase):
    fixtures = ['users.json', 'objects.json', 'streams.json', 'droplets.json']
    
    def setUp(self):
        settings.DEBUG = True
        reset_queries()
    
    def tearDown(self):
        settings.DEBUG = False
    
    def test_lazy_evaluation(self):
        all = GenericQuerySet(Droplet).all()
        query_count = len(connection.queries)
        all.select_related_generic()
        self.assertEqual(len(connection.queries), query_count)

    def test_select_all(self):
        all = list(GenericQuerySet(Droplet).select_related_generic())
        query_count = len(connection.queries)
        
        for droplet in all:
            droplet.content_object
        self.assertEqual(len(connection.queries), query_count)
    
    def test_membership_test(self):
        a = GenericQuerySet(Droplet).get(pk=1)
        all = GenericQuerySet(Droplet).select_related_generic()
        self.assertTrue(a in all)
        
        query_count = len(connection.queries)
        all[0].content_object
        self.assertEqual(len(connection.queries), query_count)
    
    def test_after_select_related(self):
        all = list(GenericQuerySet(Droplet).select_related('first').all().select_related_generic())
        # the .all is to test chaining (the _clone method)
        query_count = len(connection.queries)
        self.assertEqual(query_count, NUM_RELATED_TYPES + 1)
        for droplet in all:
            droplet.first
            droplet.content_object
        self.assertEqual(len(connection.queries), query_count)
    
    def test_before_select_related(self):
        all = list(GenericQuerySet(Droplet).select_related_generic().all().select_related('first'))
        # the .all is to test chaining (the _clone method)
        query_count = len(connection.queries)
        self.assertEqual(query_count, NUM_RELATED_TYPES + 1)
        for droplet in all:
            droplet.first
            droplet.content_object
        self.assertEqual(len(connection.queries), query_count)
    
    def test_auto_content_type_select_related(self):
        all = list(GenericQuerySet(Droplet).select_related_generic())
        self.assertEqual(len(connection.queries), NUM_RELATED_TYPES + 1)
    
    def test_multiple_select_related_generic_calls(self):
        all = list(GenericQuerySet(Droplet).select_related_generic().select_related_generic())
        query_count = len(connection.queries)
        
        for droplet in all:
            droplet.content_object
        self.assertEqual(len(connection.queries), query_count)


class QuerySetTimeTestCase(GeyserTestCase):
    fixtures = ['users.json', 'manyobjects.json']
    
    def setUp(self):
        settings.DEBUG = True
        reset_queries()
    
    def tearDown(self):
        settings.DEBUG = False
     
    def test_execution_time(self):
        # this might be a bad test
        
        TARGET_RATIO = .5
        # something is probably wrong if it's not at least 50% faster
        
        start = now()
        for i in range(10):
            all = GenericQuerySet(Droplet).all()
            for droplet in all:
                droplet.content_object
        normal_time = now() - start
        
        start = now()
        for i in range(10):
            all = GenericQuerySet(Droplet).select_related_generic()
            for droplet in all:
                droplet.content_object
        select_generic_time = now() - start
        
        ratio = select_generic_time / normal_time
        self.assertTrue(ratio <= TARGET_RATIO, '%s > %s' % (ratio, TARGET_RATIO))


__all__ = ('QuerySetTestCase', 'QuerySetTimeTestCase',)
