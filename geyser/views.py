from django.http import Http404
from django.shortcuts import render_to_response, get_object_or_404

from django.contrib.contenttypes.models import ContentType

from geyser.forms import PublishFormSet
from geyser.models import Droplet


class PublishObject(object):
    """A view used to publish the given model."""
    
    def __init__(self, Model, **kwargs):
        self.Model = Model
        self.template = kwargs.get('template', 'geyser/publish.html')
    
    def __call__(self, request, object_pk):
        """The actual view function."""
        
        publishable = get_object_or_404(self.Model, pk=object_pk)
        publications = Droplet.objects.get_allowed_publications(publishable, request.user)
        if publications is None:
            raise Http404
        
        current_publications = Droplet.objects.get_list(
            publishable=publishable, include_future=True
        ).values_list('publication_type_id', 'publication_id')
        
        publication_types = []
        formset_data = []
        for publication in publications:
            publication_type = ContentType.objects.get_for_model(publication)
            publication_types.append(publication_type)
            formset_data.append({
                'type': publication_type.id,
                'id': publication.id,
                'publish': (publication_type.id, publication.id) in current_publications
            })
        
        if request.method == 'POST':
            publication_formset = PublishFormSet(request.POST, initial=formset_data)
        else:
            publication_formset = PublishFormSet(initial=formset_data)
        
        for (form, publication, publication_type) in \
                zip(publication_formset.forms, publications, publication_types):
            form.publication = publication
            form.publication_type = publication_type
        
        if publication_formset.is_valid():
            to_publish = []
            to_unpublish = []
            for form in publication_formset.forms:
                if form.changed_data == ['publish']:
                    if form.cleaned_data['publish']:
                        to_publish.append(form.publication)
                    else:
                        to_unpublish.append(form.publication)
            Droplet.objects.publish(publishable, to_publish, request.user)
            Droplet.objects.unpublish(publishable, to_unpublish, request.user)
                 
        return render_to_response(
            self.template,
            {
                'object': publishable,
                'publication_formset': publication_formset
            }
        )