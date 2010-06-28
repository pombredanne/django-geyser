from datetime import datetime

from django.db import models
from django.conf import settings
from django.contrib.contenttypes.models import ContentType


class DropletManager(models.Manager):
    """
    Custom manager for published objects, to support lookups by types and
    instances of publishables and publications.
    """
    
    def get_query_set(self):
        return super(DropletManager, self).get_query_set().select_related('publishable', 'publication')
    
    def get_list(self, **kwargs):
        """Get a list of Droplet instances, filtered in useful ways."""
        
        publishable = kwargs.get('publishable', None)
        publishable_models = kwargs.get('publishable_models', None)
        publications = kwargs.get('publications', None)
        queries = kwargs.get('queries', [])
        filters = kwargs.get('filters', {})
        include_old = kwargs.get('include_old', False)
        include_future = kwargs.get('include_future', False)
 
        if publishable:
            queries.append(models.Q(publishable_id=publishable.id))
            publishable_models = publishable.__class__
        
        if publishable_models:
            if hasattr(publishable_models, '__iter__'):
                publishable_types = []
                for publishable_model in publishable_models:
                    publishable_types.append(ContentType.objects.get_for_model(publishable_model))
                queries.append(models.Q(publishable_type__in=publishable_types))
            else:
                queries.append(models.Q(publishable_type=ContentType.objects.get_for_model(publishable_models)))
        
        if publications:
            if hasattr(publications, '__iter__'):
                publications_by_type = {}
                for publication in publications:
                    publication_type = ContentType.objects.get_for_model(publication)
                    publication_pks = publications_by_type.setdefault(publication_type, [])
                    publication_pks.append(publication.pk)
                publication_q = models.Q(pk__isnull=True)
                for publication_type in publications_by_type:
                    publication_q = publication_q | models.Q(
                        publication_type=publication_type,
                        publication_id__in=publications_by_type[publication_type]
                    )
                queries.append(publication_q)
            else:
                queries.append(models.Q(
                    publication_type=ContentType.objects.get_for_model(publications),
                    publication_id=publications.id
                ))
        
        if not include_old:
            filters['is_newest'] = True
        if not include_future:
            filters['published__lte'] = datetime.now()
        
        return self.filter(*queries, **filters)
    
    def get_publishable_list(self, publishable_model, **kwargs):
        """
        Return a list of publishables of the given type which are published to
        the given publication(s).
        """
        
        if not issubclass(publishable_model, models.Model):
            raise TypeError('publishable_model must be a subclass of models.Model')
        publications = kwargs.get('publications', None)
        
        droplet_ids = self.get_list(publishable_models=publishable_model,
            publications=publications).values_list('id', flat=True)
        droplets_by_object_id = self.get_list(publishable_models=publishable_model,
            publications=publications).values_list('publishable_id', flat=True)
        droplets_with_object_annotations = droplets_by_object_id \
            .annotate(first_published=models.Min('published')) \
            .values('publishable_id', 'first_published', 'publication_type', 'publication_id')
        
        object_list = publishable_model.objects.filter(id__in=droplets_by_object_id)
        app_model = '%s.%s' % (publishable_model._meta.app_label, publishable_model.__name__.lower())
        annotation_name = settings.GEYSER_PUBLISHABLES[app_model].get('published_annotation', 'published')
        for object in object_list:
            annotations = droplets_with_object_annotations.get(publishable_id=object.id)
            setattr(object, annotation_name, annotations['first_published'])
                
        return object_list