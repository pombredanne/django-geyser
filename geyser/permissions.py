from django.conf import settings
from django.db.models import get_model
from django.db.models.signals import post_save

from rubberstamp.models import AppPermission

from geyser.models import Stream


publish_types = []
for (app_model, pub_settings) in settings.GEYSER_PUBLISHABLES.items():
    Model = get_model(*app_model.split('.'))
    publish_types.append(Model)
    auto_perm_fields = pub_settings.get('auto_perms')
    if not auto_perm_fields:
        continue
    def add_publish_permissions(sender, **kwargs):
        if not kwargs['created']:
            return
        instance = kwargs['instance']
        for field_name in auto_perm_fields:
            user = getattr(instance, field_name, None)
            if not user:
                continue
            AppPermission.objects.assign('geyser.publish', user, obj=instance)
    post_save.connect(add_publish_permissions, sender=Model)


permissions = [
    ('publish', 'Publish this', publish_types),
    ('publish_to', 'Publish to this', Stream),
]
