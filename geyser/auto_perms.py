from django.db.models.signals import post_save
from django.conf import settings

from django.contrib.contenttypes.models import ContentType

from geyser.permission_models import PublishablePermission


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