from django.conf import settings
from django.db.models import get_model
from django.db.models.signals import post_save

from rubberstamp.models import AppPermission

from geyser.models import Stream


def _get_geyser_publish_permissions():
    types = set()
    for app_model in settings.GEYSER_PUBLISHABLES:
        types.add(get_model(*app_model.split('.')))
    return [
        ('publish', 'Publish this', types),
        ('publish_to', 'Publish to this', Stream),
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
