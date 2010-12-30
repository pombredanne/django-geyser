from datetime import datetime

from django.db import models
from django.db.models.signals import pre_save, post_save
from django.conf import settings
from django.core.exceptions import ValidationError

from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic
from django.contrib.auth.models import User

from geyser.managers import DropletManager


class Stream(models.Model):
    """
    Where Droplets are published. Intended to be subclassed.
    """
    pass


class Droplet(models.Model):
    """
    An individual publishing of an object somewhere.
    
    Attributes:
    
    * `publishable`: The object which is published.
    * `publication`: The object which the publishable in published to.
    * `first`: The `Droplet` corresponding to the first time the publishable
      was published. Can be self.
    * `is_current`: Whether this publishing is current (has not been
      unpublished).
    * `published`: The datetime that this `Droplet` was created.
    * `update`: The datetime that this `Droplet` was updated (probably means
      it was unpublished).
    * `published_by`: The user who created this `Droplet`.
    * `updated_by`: The user who updated this `Droplet` (likely unpublished).
    
    """
    
    first = models.ForeignKey('self', null=True, editable=False)
    
    content_type = models.ForeignKey(ContentType,
        related_name='published_of_this_type')
    object_id = models.PositiveIntegerField()
    content_object = generic.GenericForeignKey()
    
    stream = models.ForeignKey(Stream, related_name='droplets')
    
    is_current = models.BooleanField(default=True, editable=False)
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
        return 'Droplet: "%s" (%s)' % (self.content_object, self.content_type)
    
    def clean(self):
        app_model = '%s.%s' % (self.content_type.app_label, self.content_type.model)
        try:
            unique_for_date_fields = settings.GEYSER_PUBLISHABLES[app_model]['unique_for_date']
        except KeyError:
            return
        for field_name in unique_for_date_fields:
            filter = {field_name: getattr(self.content_object, field_name)}
            matching = self.content_object.__class__.objects.filter(**filter)
            matching_ids = matching.values_list('id', flat=True)
            if self.__class__.objects.filter(
                content_type=self.content_type,
                object_id__in=matching_ids,
                published__year=self.published.year,
                published__month=self.published.month,
                published__day=self.published.day,
                first=models.F('pk') # only worry about "canonical" publishing
            ).exists():
                raise ValidationError('%s.%s must be unique for date' %
                    (self.content_type.model, field_name))


def add_first(sender, **kwargs):
    instance = kwargs['instance']
    first_dict = {
        'content_type': instance.content_type,
        'object_id': instance.object_id
    }
    try:
        instance.first = Droplet.objects.filter(**first_dict).order_by('published')[0]
    except IndexError:
        instance.full_clean()

pre_save.connect(add_first, sender=Droplet)


def add_self_first(sender, **kwargs):
    instance = kwargs['instance']
    if not instance.first:
        # this should only happen if this instance is first
        instance.first = instance
        instance.save()

post_save.connect(add_self_first, sender=Droplet)


def unpublish_previous(sender, **kwargs):
    instance = kwargs['instance']
    current_list = sender.objects.get_list(
        obj=instance.content_object,
        stream=instance.stream
    )
    current_list.update(
        is_current=False,
        updated=datetime.now()
    )

pre_save.connect(unpublish_previous, sender=Droplet)
