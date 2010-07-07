from datetime import datetime

from django.db import models
from django.db.models.signals import pre_save
from django.conf import settings

from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic
from django.contrib.auth.models import User

from geyser.bigint import BigAutoField
from geyser.managers import DropletManager

class Droplet(models.Model):
    """
    An individual publishing of an object somewhere.
    """
    
    id = BigAutoField(primary_key=True)
    
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
    published = models.DateTimeField(auto_now_add=True, editable=False)
    updated = models.DateTimeField(auto_now=True, editable=False)
    
    published_by = models.ForeignKey(User, null=True, blank=True, editable=False, related_name='published_droplets')
    updated_by = models.ForeignKey(User, null=True, blank=True, editable=False, related_name='updated_droplets')
    
    objects = DropletManager()
    
    class Meta:
        ordering = ['-published']
    
    def __unicode__(self):
        return '%s (%s) on %s (%s)' % (self.publishable,
            self.publishable_type, self.publication, self.publication_type)


def remove_previous_newest(sender, **kwargs):
    instance = kwargs['instance']
    current_list = Droplet.objects.get_list(
        publishable=instance.publishable,
        publications=instance.publication
    )
    current_list.update(
        is_newest=False,
        updated=datetime.now()
    )

pre_save.connect(remove_previous_newest, sender=Droplet)


if 'south' in settings.INSTALLED_APPS:
    from south.modelsinspector import add_introspection_rules
    add_introspection_rules([], ["^sprinkler\.bigint"])