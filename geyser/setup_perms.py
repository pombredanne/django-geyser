from django.db.models.signals import post_save
from django.conf import settings

from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType

from geyser.models import Droplet
from geyser.permission_models import PublishablePermission


droplet_type = ContentType.objects.get_for_model(Droplet)
for (publishable, options) in settings.GEYSER_PUBLISHABLES.items():
    Permission.objects.get_or_create(
        name='Can publish a(n) %s' % publishable,
        content_type=droplet_type,
        codename='publish_%s' % publishable
    )
    Permission.objects.get_or_create(
        name='Can publish any %s' % publishable,
        content_type=droplet_type,
        codename='publish_any_%s' % publishable
    )
    for publication in options['publish_to']:
        Permission.objects.get_or_create(
            name='Can publish a(n) %s to a(n) %s' % (publishable, publication),
            content_type=droplet_type,
            codename='publish_%s_to_%s' % (publishable, publication)
        )
        Permission.objects.get_or_create(
            name='Can publish a(n) %s to any %s' % (publishable, publication),
            content_type=droplet_type,
            codename='publish_%s_to_any_%s' % (publishable, publication)
        )


for (app_model, pub_settings) in settings.GEYSER_PUBLISHABLES.items():
    auto_perm_fields = pub_settings.get('auto_perms')
    if auto_perm_fields:
        (app_name, model_name) = tuple(app_model.split('.'))
        publishable_type = ContentType.objects.get(
            app_label=app_name, model=model_name)
        def add_publish_permissions(sender, **kwargs):
            if kwargs['created']:
                instance = kwargs['instance']
                for field_name in auto_perm_fields:
                    user = getattr(instance, field_name, None)
                    if user:
                        PublishablePermission.objects.create(
                            content_type=publishable_type,
                            object_id=instance.id,
                            user=user)
        add_publish_permissions.__name__ = 'add_%s_publish_permissions' % model_name
        post_save.connect(add_publish_permissions, sender=publishable_type.model_class())