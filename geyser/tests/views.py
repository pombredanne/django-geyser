from datetime import datetime

from django.forms.formsets import BaseFormSet, Form
from django.contrib.auth.models import User, Permission
from django.contrib.contenttypes.models import ContentType

from geyser.models import Droplet
from geyser.tests.base import GeyserTestCase
from geyser.tests.testapp.models import TestModel1, TestModel2, TestModel3


class PublishViewTest(GeyserTestCase):
    fixtures = ['users.json', 'objects.json', 'permissions.json']
    urls = 'geyser.tests.testurls'
    
    def setUp(self):
        self.user = User.objects.get(pk=2)
        
        self.type3 = ContentType.objects.get_for_model(TestModel3)
        self.t1a = TestModel1.objects.get(pk=1)
        self.t1b = TestModel1.objects.get(pk=2)
        self.t3a = TestModel3.objects.get(pk=1)
        self.t3b = TestModel3.objects.get(pk=2)
    
    def test_get(self):
        unauth_response = self.client.get('/t1/1/')
        self.assertEqual(unauth_response.status_code, 404)
        
        self.client.login(username='user', password='')
        
        t1z_response = self.client.get('/t1/26/')
        self.assertEqual(t1z_response.status_code, 404)
        
        t1a_response = self.client.get('/t1/1/')
        self.assertEqual(t1a_response.status_code, 200)
        self.assertEqual(t1a_response.context['object'], self.t1a)
        self.assertTrue(isinstance(t1a_response.context['publication_formset'], BaseFormSet))
        forms = t1a_response.context['publication_formset'].forms
        self.assertEqual(len(forms), 2)
        self.assertTrue(all([isinstance(form, Form) for form in forms]))
        self.assertFalse(t1a_response.context['publish_error'])
        
        self.assertEqual(forms[0].initial['id'], 1)
        self.assertEqual(forms[0].initial['type'], self.type3.id)
        self.assertEqual(forms[1].initial['id'], 2)
        self.assertEqual(forms[1].initial['type'], self.type3.id)
        self.assertEqual(forms[0].publication, self.t3a)
        self.assertEqual(forms[0].publication_type, self.type3)
        self.assertEqual(forms[1].publication, self.t3b)
        self.assertEqual(forms[1].publication_type, self.type3)
    
    def test_publish(self):
        unauth_response = self.client.post('/t1/1/')
        self.assertEqual(unauth_response.status_code, 404)
        
        self.client.login(username='user', password='')
        
        t1z_response = self.client.post('/t1/26/')
        self.assertEqual(t1z_response.status_code, 404)
        
        form_dict = {
            'form-TOTAL_FORMS': 2,
            'form-INITIAL_FORMS': 2,
            'form-0-publish': 'on',
            'form-0-type': self.type3.id,
            'form-0-id': self.t3a.id,
            'form-1-type': self.type3.id,
            'form-1-id': self.t3b.id
        }
        t1a_response = self.client.post('/t1/1/', form_dict)
        self.assertEqual(t1a_response.status_code, 200)
        self.assertEqual(t1a_response.context['object'], self.t1a)
        self.assertTrue(isinstance(t1a_response.context['publication_formset'], BaseFormSet))
        forms = t1a_response.context['publication_formset'].forms
        self.assertEqual(len(forms), 2)
        self.assertTrue(all([isinstance(form, Form) for form in forms]))
        self.assertFalse(t1a_response.context['publish_error'])
        
        self.assertEqual(forms[0].cleaned_data['id'], 1)
        self.assertEqual(forms[0].cleaned_data['type'], self.type3.id)
        self.assertEqual(forms[0].cleaned_data['publish'], True)
        self.assertEqual(forms[1].cleaned_data['id'], 2)
        self.assertEqual(forms[1].cleaned_data['type'], self.type3.id)
        self.assertEqual(forms[1].cleaned_data['publish'], False)
        
        self.assertEqual(forms[0].publication, self.t3a)
        self.assertEqual(forms[0].publication_type, self.type3)
        self.assertEqual(forms[1].publication, self.t3b)
        self.assertEqual(forms[1].publication_type, self.type3)
        
        published = Droplet.objects.get_list()
        self.assertTrue(all(d.publishable == self.t1a for d in published))
        self.assertTrue(any(d.publication == self.t3a for d in published))
        self.assertEqual(len(published), 1)
    
    def test_publish_with_date(self):
        self.client.login(username='user', password='')
        
        no_date_response = self.client.get('/t1/1/')
        self.assertRaises(KeyError, lambda c: c['datetime_form'], no_date_response.context)
        
        get_response = self.client.get('/t1d/1/')
        self.assertTrue(isinstance(get_response.context['datetime_form'], Form))
        
        form_dict = {
            'form-TOTAL_FORMS': 2,
            'form-INITIAL_FORMS': 2,
            'form-0-publish': 'on',
            'form-0-type': self.type3.id,
            'form-0-id': self.t3a.id,
            'form-1-type': self.type3.id,
            'form-1-id': self.t3b.id,
            'publish_datetime_0': '2010-07-01',
            'publish_datetime_1': '0:00:00'
        }
        post_response = self.client.post('/t1d/1/', form_dict)
        
        droplet = Droplet.objects.get_list()[0]
        self.assertEqual(droplet.published, datetime(2010, 7, 1))
        self.assertFalse(post_response.context['datetime_form'].is_bound)
    
    def test_publish_with_date_blank(self):
        self.client.login(username='user', password='')
        
        form_dict = {
            'form-TOTAL_FORMS': 2,
            'form-INITIAL_FORMS': 2,
            'form-0-publish': 'on',
            'form-0-type': self.type3.id,
            'form-0-id': self.t3a.id,
            'form-1-type': self.type3.id,
            'form-1-id': self.t3b.id,
            'publish_datetime_0': '',
            'publish_datetime_1': ''
        }
        post_response = self.client.post('/t1d/1/', form_dict)
        
        droplet = Droplet.objects.get_list()[0]
        self.assertFalse(post_response.context['datetime_form'].is_bound)
    
    def test_publish_with_date_invalid(self):
        self.client.login(username='user', password='')
        
        form_dict = {
            'form-TOTAL_FORMS': 2,
            'form-INITIAL_FORMS': 2,
            'form-0-publish': 'on',
            'form-0-type': self.type3.id,
            'form-0-id': self.t3a.id,
            'form-1-type': self.type3.id,
            'form-1-id': self.t3b.id,
            'publish_datetime_0': 'eee',
            'publish_datetime_1': 'a'
        }
        post_response = self.client.post('/t1d/1/', form_dict)
        
        self.assertEqual(len(Droplet.objects.get_list()), 0)
        self.assertTrue(post_response.context['datetime_form'].is_bound)
        self.assertFalse(post_response.context['datetime_form'].is_valid())
    
    def test_unpublish(self):
        droplet = Droplet.objects.publish(self.t1a, self.t3a, self.user)[0]
        self.assertNotEqual(droplet.updated_by, self.user)

        self.client.login(username='user', password='')
        
        form_dict = {
            'form-TOTAL_FORMS': 2,
            'form-INITIAL_FORMS': 2,
            'form-0-type': self.type3.id,
            'form-0-id': self.t3a.id,
            'form-1-type': self.type3.id,
            'form-1-id': self.t3b.id
        }
        t1a_response = self.client.post('/t1/1/', form_dict)
        
        self.assertEqual(t1a_response.status_code, 200)
        self.assertEqual(t1a_response.context['object'], self.t1a)
        self.assertTrue(isinstance(t1a_response.context['publication_formset'], BaseFormSet))
        forms = t1a_response.context['publication_formset'].forms
        self.assertEqual(len(forms), 2)
        self.assertTrue(all([isinstance(form, Form) for form in forms]))
        
        self.assertEqual(forms[0].cleaned_data['id'], 1)
        self.assertEqual(forms[0].cleaned_data['type'], self.type3.id)
        self.assertEqual(forms[0].cleaned_data['publish'], False)
        self.assertEqual(forms[1].cleaned_data['id'], 2)
        self.assertEqual(forms[1].cleaned_data['type'], self.type3.id)
        self.assertEqual(forms[1].cleaned_data['publish'], False)
        
        self.assertEqual(forms[0].publication, self.t3a)
        self.assertEqual(forms[0].publication_type, self.type3)
        self.assertEqual(forms[1].publication, self.t3b)
        self.assertEqual(forms[1].publication_type, self.type3)
        
        published = Droplet.objects.get_list()
        self.assertEqual(len(published), 0)
        
        droplet = Droplet.objects.all()[0]
        self.assertEqual(droplet.updated_by, self.user)


class PublishViewUniquenessTest(GeyserTestCase):
    fixtures = ['users.json', 'permissions.json']
    urls = 'geyser.tests.testurls'
    
    def setUp(self):
        self.user = User.objects.get(pk=8)
        self.t2a = TestModel2.objects.create(name='an object')
        self.t2b = TestModel2.objects.create(name='an object')
        self.type3 = ContentType.objects.get_for_model(TestModel3)
        self.t3 = TestModel3.objects.create(name='t3 object')
    
    def test_first_publish(self):
        da = Droplet.objects.publish(publishable=self.t2a)
        
        self.client.login(username='2to3user', password='')
        form_dict = {
            'form-TOTAL_FORMS': 1,
            'form-INITIAL_FORMS': 1,
            'form-0-publish': 'on',
            'form-0-type': self.type3.id,
            'form-0-id': self.t3.id,
            'publish_datetime_0': '',
            'publish_datetime_1': ''
        }
        post_response = self.client.post('/t2d/%s/' % self.t2b.id, form_dict)
        self.assertEqual(len(Droplet.objects.get_list()), 1)
        self.assertTrue(post_response.context['datetime_form'].is_bound)
        self.assertTrue(post_response.context['publish_error'])


__all__ = ('PublishViewTest', 'PublishViewUniquenessTest')