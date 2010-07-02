from django.db.models.signals import post_save
from django.conf import settings

from django.contrib.contenttypes.models import ContentType

import authority
from authority.permissions import BasePermission


# For some reason authority adds generic checks to the base class whenever
# they are registered on a subclass. Saving the default list to restore it...
base_checks = BasePermission.generic_checks[:]


publications = {}
for (publishable, pub_settings) in settings.GEYSER_PUBLISHABLES.items():
    for publication in pub_settings['publish_to']:
        publish_here = publications.setdefault(publication, [])
        publish_here.append(publishable)


def register_permission(app_model):
    (app_name, model_name) = tuple(app_model.split('.'))
    Model = ContentType.objects.get(
        app_label=app_name, model=model_name).model_class()
    check_list = base_checks[:]
    if app_model in settings.GEYSER_PUBLISHABLES:
        check_list.append('publish')
    for publishable in publications.get(app_model, []):
        publishable_name =  publishable.split('.')[-1]
        check_list.append('publish_%s_to' % publishable_name)
    authority.register(Model, label='%s_permission' % model_name, generic_checks=check_list)
    # Reset the base class' generic checks. See comment on lines 9-10.
    BasePermission.generic_checks = base_checks


for publishable in settings.GEYSER_PUBLISHABLES:
    register_permission(publishable)

for publication in publications:
    if publication not in settings.GEYSER_PUBLISHABLES:
        register_permission(publication)

for (app_model, pub_settings) in settings.GEYSER_PUBLISHABLES.items():
    auto_perm_fields = pub_settings.get('auto_perms')
    if auto_perm_fields:
        (app_name, model_name) = tuple(app_model.split('.'))
        Model = ContentType.objects.get(
            app_label=app_name, model=model_name).model_class()
        model_perm = authority.sites.site.get_permissions_by_model(Model)[0]
        check = 'publish_%s' % model_name
        def add_publish_permissions(sender, **kwargs):
            if kwargs['created']:
                instance = kwargs['instance']
                for field_name in auto_perm_fields:
                    user = getattr(instance, field_name, None)
                    if user:
                        permission = model_perm(user)
                        permission.assign(check=check, content_object=instance)
        add_publish_permissions.__name__ = \
            'add_%s_publish_permissions' % model_name
        post_save.connect(add_publish_permissions, sender=Model)