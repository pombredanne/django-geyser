from django.db import models

from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic
from django.contrib.auth.models import User


class GeyserPermission(models.Model):
    """Abstract base model for Geyser per-object permissions."""
    content_type = models.ForeignKey(ContentType)
    object_id = models.PositiveIntegerField()
    content_object = generic.GenericForeignKey()
    
    user = models.ForeignKey(User)
    
    class Meta:
        app_label = 'geyser'
        unique_together = ('content_type', 'object_id', 'user')
        abstract = True


class PublishablePermission(GeyserPermission):
    """Permission to publish an object."""
    pass


class PublicationPermission(GeyserPermission):
    """Permission to publish a specific type of object to an object."""
    publishable_type = models.ForeignKey(ContentType, related_name='publishable_to_set')
    
    class Meta(GeyserPermission.Meta):
        unique_together = ('publishable_type', 'content_type', 'object_id', 'user')