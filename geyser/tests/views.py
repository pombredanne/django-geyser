from django.conf import settings
from django.forms.formsets import BaseFormSet, Form

from django.contrib.auth.models import User, Permission
from django.contrib.contenttypes.models import ContentType

import authority

from geyser.tests.base import GeyserTestCase
from geyser.tests.testapp.models import TestModel1, TestModel2, TestModel3


class ViewTest(GeyserTestCase):
    fixtures = ['users.json', 'objects.json', 'permissions.json']
    urls = 'geyser.tests.testurls'
    
    def setUp(self):
        self.user = User.objects.get(pk=2)
        add_perm = Permission.objects.get(codename='add_droplet')
        self.user.user_permissions.add(add_perm)
        
        self.type3 = ContentType.objects.get_for_model(TestModel3)
        self.t1a = TestModel1.objects.get(pk=1)
        self.t1b = TestModel1.objects.get(pk=2)
        self.t2a = TestModel2.objects.get(pk=1)
        self.t3a = TestModel3.objects.get(pk=1)
        self.t3b = TestModel3.objects.get(pk=2)
    
    def test_get_view(self):
        unauth_response = self.client.get('/t1/1/')
        self.assertEqual(unauth_response.status_code, 302)
        
        self.client.login(username='user', password='')
        
        t1b_response = self.client.get('/t1/2/')
        self.assertEqual(t1b_response.status_code, 404)
        
        t1z_response = self.client.get('/t1/26/')
        self.assertEqual(t1z_response.status_code, 404)
        
        t1a_response = self.client.get('/t1/1/')
        self.assertEqual(t1a_response.status_code, 200)
        self.assertEqual(t1a_response.context['object'], self.t1a)
        self.assertTrue(isinstance(t1a_response.context['publication_formset'], BaseFormSet))
        
        forms = t1a_response.context['publication_formset'].forms
        self.assertEqual(len(forms), 2)
        self.assertTrue(all([isinstance(form, Form) for form in forms]))
        self.assertEqual(forms[0].initial['id'], 1)
        self.assertEqual(forms[0].initial['type'], self.type3.id)
        self.assertEqual(forms[1].initial['id'], 2)
        self.assertEqual(forms[1].initial['type'], self.type3.id)
        self.assertEqual(forms[0].publication, self.t3a)
        self.assertEqual(forms[0].publication_type, self.type3)
        self.assertEqual(forms[1].publication, self.t3b)
        self.assertEqual(forms[1].publication_type, self.type3)
    
    def test_post_view(self):
        unauth_response = self.client.post('/t1/1/')
        self.assertEqual(unauth_response.status_code, 302)
        
        self.client.login(username='user', password='')
        
        t1b_response = self.client.post('/t1/2/')
        self.assertEqual(t1b_response.status_code, 404)
        
        t1z_response = self.client.post('/t1/26/')
        self.assertEqual(t1z_response.status_code, 404)
        
        t1a_response = self.client.post('/t1/1/')
        self.assertEqual(t1a_response.status_code, 200)


__all__ = ('ViewTest',)