from django import forms
from django.forms.formsets import formset_factory

class PublishForm(forms.Form):
    type = forms.IntegerField(widget=forms.HiddenInput)
    id = forms.IntegerField(widget=forms.HiddenInput)
    publish = forms.BooleanField(initial=False, required=False)

PublishFormSet = formset_factory(PublishForm, extra=0)