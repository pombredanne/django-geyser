from django.http import Http404
from django.shortcuts import render_to_response, get_object_or_404
from django.conf import settings

from django.contrib.contenttypes.models import ContentType

from authority.sites import site as auth_site
from authority.models import Permission

from geyser.forms import PublishFormSet
from geyser.models import Droplet

class PublishObject(object):
    """A view used to publish the given model."""
    
    def __init__(self, Model):
        self.Model = Model
    
    def __call__(self, request, object_pk):
        """The actual view function."""
        
        publishable = get_object_or_404(self.Model, pk=object_pk)
        publications = Droplet.objects.get_allowed_publications(publishable, request.user)
        if publications is None:
            raise Http404
        
        publication_types = []
        allowed_by_ids = []
        for publication in publications:
            publication_type = ContentType.objects.get_for_model(publication)
            publication_types.append(publication_type)
            allowed_by_ids.append({'type': publication_type.id, 'id': publication.id})
                
        publication_formset = PublishFormSet(initial=allowed_by_ids)
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