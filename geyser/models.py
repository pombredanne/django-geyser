from datetime import datetime

from django.db import models
from django.db.models.signals import pre_save, post_save
from django.conf import settings
from django.core.exceptions import ValidationError

from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic
from django.contrib.auth.models import User

from geyser.managers import DropletManager
from geyser.bigint import BigAutoField
from geyser.permission_models import *

#Droplet uses a custom Field that South won't recognize unless this is added
if 'south' in settings.INSTALLED_APPS:
    from south.modelsinspector import add_introspection_rules
    add_introspection_rules([], ["^geyser\.bigint"])


class Droplet(models.Model):
    """
    An individual publishing of an object somewhere.
    """
    
    id = BigAutoField(primary_key=True)
    first = models.ForeignKey('self', null=True, editable=False)
    
    publishable_type = models.ForeignKey(ContentType,
        related_name='published_of_this_type')
    publishable_id = models.PositiveIntegerField()
    publishable = generic.GenericForeignKey(
        'publishable_type', 'publishable_id')
    
    publication_type = models.ForeignKey(ContentType,
        related_name='published_to_this_type')
    publication_id = models.PositiveIntegerField()
    publication = generic.GenericForeignKey(
        'publication_type', 'publication_id')
    
    is_newest = models.BooleanField(default=True, editable=False)
    published = models.DateTimeField(default=datetime.now, editable=False)
    updated = models.DateTimeField(auto_now=True, editable=False)
    
    published_by = models.ForeignKey(User, null=True, blank=True,
        editable=False, related_name='published_droplets')
    updated_by = models.ForeignKey(User, null=True, blank=True,
        editable=False, related_name='updated_droplets')
    
    objects = DropletManager()
    
    class Meta:
        ordering = ['-published']
    
    def __unicode__(self):
        return '"%s" (%s) on "%s" (%s)' % (self.publishable,
            self.publishable_type, self.publication, self.publication_type)
    
    def clean(self):
        app_model = '%s.%s' % (self.publishable_type.app_label, self.publishable_type.model)
        try:
            unique_for_date_fields = settings.GEYSER_PUBLISHABLES[app_model]['unique_for_date']
        except KeyError:
            return
        for field_name in unique_for_date_fields:
            publishable_filter = {field_name: getattr(self.publishable, field_name)}
            matching_publishable_ids = self.publishable.__class__.objects.filter(**publishable_filter).values_list('id', flat=True)
            if self.__class__.objects.filter(
                publishable_type=self.publishable_type,
                publishable_id__in=matching_publishable_ids,
                published__year=self.published.year,
                published__month=self.published.month,
                published__day=self.published.day,
                first=models.F('pk')
            ).exists():
                raise ValidationError('publishable.%s must be unique for date' % field_name)


def add_first(sender, **kwargs):
    instance = kwargs['instance']
    first_dict = {
        'publishable_type': instance.publishable_type,
        'publishable_id': instance.publishable_id
    }
    try:
        instance.first = Droplet.objects.filter(**first_dict).order_by('published')[0]
    except IndexError:
        instance.full_clean()

pre_save.connect(add_first, sender=Droplet)


def add_self_first(sender, **kwargs):
    instance = kwargs['instance']
    if not instance.first:
        instance.first = instance
        instance.save()

post_save.connect(add_self_first, sender=Droplet)


def remove_previous_newest(sender, **kwargs):
    instance = kwargs['instance']
    current_list = sender.objects.get_list(
        publishable=instance.publishable,
        publications=instance.publication
    )
    current_list.update(
        is_newest=False,
        updated=datetime.now()
    )

pre_save.connect(remove_previous_newest, sender=Droplet)