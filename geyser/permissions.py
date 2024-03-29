from django.conf import settings
from django.db.models import get_model
from django.db.models.signals import post_save

from rubberstamp.models import AppPermission


def _get_geyser_publish_permissions():
    publishable_types = set()
    publication_types = set()
    for (publishable_type, options) in settings.GEYSER_PUBLISHABLES.items():
        publishable_types.add(get_model(*publishable_type.split('.')))
        for publication_type in options['publish_to']:
            publication_types.add(get_model(*publication_type.split('.')))
    return [
        ('publish', 'Publish this', publishable_types),
        ('publish_to', 'Publish to this', publication_types),
    ]

permissions = _get_geyser_publish_permissions()


for (app_model, pub_settings) in settings.GEYSER_PUBLISHABLES.items():
    auto_perm_fields = pub_settings.get('auto_perms')
    if auto_perm_fields:
        def add_publish_permissions(sender, **kwargs):
            if kwargs['created']:
                instance = kwargs['instance']
                for field_name in auto_perm_fields:
                    user = getattr(instance, field_name, None)
                    if user:
                        AppPermission.objects.assign(
                            'geyser.publish', user, obj=instance)
        add_publish_permissions.__name__ = 'add_publish_permissions'
        Publishable = get_model(*app_model.split('.'))
        post_save.connect(add_publish_permissions, sender=Publishable)