from django import forms
from django.forms.formsets import formset_factory


class PublishForm(forms.Form):
    type = forms.IntegerField(widget=forms.HiddenInput)
    id = forms.IntegerField(widget=forms.HiddenInput)
    publish = forms.BooleanField(initial=False, required=False)

PublishFormSet = formset_factory(PublishForm, extra=0)


class PublishDateTimeForm(forms.Form):
    publish_datetime = forms.SplitDateTimeField(
        required=False,
        label='Publish when?',
        help_text='Affects new publishings only. Leave blank to publish now.'
    )