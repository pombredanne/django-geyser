from django.http import Http404
from django.shortcuts import render_to_response, get_object_or_404
from django.conf import settings
from django.utils.decorators import method_decorator

from django.contrib.auth.decorators import permission_required
from django.contrib.contenttypes.models import ContentType

from authority.sites import site as auth_site
from authority.models import Permission

from geyser.forms import PublishFormSet


class PublishObject(object):
    """A view used to publish the given model."""
    
    def __init__(self, Model):
        self.Model = Model
        self.Permission = auth_site.get_permissions_by_model(self.Model)[0]
        self.model_name = self.Model.__name__.lower()
        
        self.publication_types = []
        publishable_key = '%s.%s' % (self.Model._meta.app_label, self.model_name)
        for app_model in settings.GEYSER_PUBLISHABLES[publishable_key]['publish_to']:
            (app_name, model_name) = app_model.split('.')
            self.publication_types.append(
                ContentType.objects.get(app_label=app_name, model=model_name))
    
    @method_decorator(permission_required('geyser.add_droplet'))
    def __call__(self, request, object_pk):
        """The actual view function."""
        
        publishable = get_object_or_404(self.Model, pk=object_pk)
        if not self.Permission(request.user).has_perm('%s_permission.publish_%s'
                % (self.model_name, self.model_name), publishable):
            raise Http404
        
        publications = []
        publication_types = []
        formset_data = []
        for publication_type in self.publication_types:
            publication_model = publication_type.model_class()
            perm_name = '%s_permission.publish_%s_to_%s' % \
                (publication_type.model, self.model_name, publication_type.model)
            publication_perms = Permission.objects.user_permissions(
                request.user, perm_name, publication_model)
            allowed_of_type = publication_model.objects.filter(
                id__in=publication_perms.values_list('object_id', flat=True))
            for publication in allowed_of_type:
                publications.append(publication)
                publication_types.append(publication_type)
                formset_data.append(
                    {'type': publication_type.id, 'id': publication.id})
                
        publication_formset = PublishFormSet(initial=formset_data)
        for (form, publication, publication_type) in \
                zip(publication_formset.forms, publications, publication_types):
            form.publication = publication
            form.publication_type = publication_type
        
        return render_to_response(
            'geyser/publish.html',
            {
                'object': publishable,
                'publication_formset': publication_formset
            }
        )