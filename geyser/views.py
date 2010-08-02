from datetime import datetime

from django.http import Http404
from django.shortcuts import render_to_response, get_object_or_404
from django.core.exceptions import ValidationError
from django.contrib.contenttypes.models import ContentType

from geyser.forms import PublishFormSet, PublishDateTimeForm
from geyser.models import Droplet


class PublishObject(object):
    """
    A view used to publish the given model.
    
    
    This class should be passed a model class when instantiated, which is the
    class of any objects that will published (a "publishable"). It also
    accepts a keyword argument, `template`, which will be used when rendering
    the response. The default template is ``'geyser/publish.html'``.
    
    
    Instances of this class are callable, requiring a request object and a
    primary key to be passed. The primary key is that of the object to be
    published. It returns a rendered response, using the specified template,
    including the following in the context:
    
    * `object`: The object to be published.
    * `publication_formset`: A formset containing a form for each publication
      to which the object can be published. More details below.
    
    
    Each form in the publication_formset has the following fields:
    
    * `type`: Hidden, the id of the `ContentType` for the publication.
    * `id`: Hidden, the id of the publication object.
    * `publish`: Boolean, whether the publishable is currently published to
      this publication.
    
    
    Each form also has two extra attributes added, which can be helpful for
    customizing the publish page:
    
    * `form.publication_type`: The `ContentType` instance which corresponds to
      the publication.
    * `form.publication`: The publication object itself.
    
    
    Typical usage would be something like the following line in urlpatterns::
    
        (r'^posts/(\d+)/publish/$', PublishObject(BlogPost)),
    
    Here, `BlogPost` is the `Model` class to be published, and the id of the
    post to be published is captured by the regular expression.
    
    """
    
    def __init__(self, Model, **kwargs):
        self.Model = Model
        self.with_date = kwargs.get('with_date', False)
        self.template = kwargs.get('template', 'geyser/publish.html')
    
    def __call__(self, request, object_pk):
        publishable = get_object_or_404(self.Model, pk=object_pk)
        
        allowed = Droplet.objects.get_allowed_publications(publishable, request.user)
        if allowed is None:
            raise Http404
        allowed_pairs = []
        for publication in allowed:
            allowed_pairs.append(
                (ContentType.objects.get_for_model(publication), publication))
        
        current_droplets = Droplet.objects.get_list(publishable=publishable, include_future=True)
        current_id_pairs = current_droplets.values_list('publication_type_id', 'publication_id')
        
        formset_data = []
        for (type, publication) in allowed_pairs:
            formset_data.append({
                'type': type.id,
                'id': publication.id,
                'publish': (type.id, publication.id) in current_id_pairs
            })
        
        if request.method == 'POST':
            publication_formset = PublishFormSet(request.POST, initial=formset_data)
            if self.with_date:
                datetime_form = PublishDateTimeForm(request.POST)
        else:
            publication_formset = PublishFormSet(initial=formset_data)
            if self.with_date:
                datetime_form = PublishDateTimeForm()
        
        for (form, pair) in zip(publication_formset.forms, allowed_pairs):
            (form.publication_type, form.publication) = pair
        
        publish_error = None
        if publication_formset.is_valid():
            to_publish = []
            to_unpublish = []
            for form in publication_formset.forms:
                if form.changed_data == ['publish']:
                    if form.cleaned_data['publish']:
                        to_publish.append(form.publication)
                    else:
                        to_unpublish.append(form.publication)
            if self.with_date:
                if datetime_form.is_valid():
                    publish_datetime = datetime_form.cleaned_data['publish_datetime']
                    if not publish_datetime:
                        publish_datetime = datetime.now()
                    try:
                        Droplet.objects.publish(publishable, to_publish,
                            request.user, published=publish_datetime)
                    except ValidationError, exception:
                        publish_error = str(exception)
                    else:
                        Droplet.objects.unpublish(publishable, to_unpublish,
                            request.user)
                        datetime_form = PublishDateTimeForm()
            else:
                try:
                    Droplet.objects.publish(publishable, to_publish,
                        request.user)
                except ValidationError, exception:
                    publish_error = str(exception)
                else:
                    Droplet.objects.unpublish(publishable, to_unpublish,
                        request.user)
        
        context_dict = {
            'object': publishable,
            'publication_formset': publication_formset,
            'publish_error': publish_error
        }
        if self.with_date:
            context_dict['datetime_form'] = datetime_form
        
        return render_to_response(
            self.template,
            context_dict
        )