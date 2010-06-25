from django.db import models

from django.contrib.contenttypes.models import ContentType


class DropletManager(models.Manager):
    """
    Custom manager for published objects, to support lookups by types and
    instances of publishables and publications.
    """
    
    def get_list(self, **kwargs):
        """Get a list of Droplet instance, filtered in useful ways."""
        queries = []
        filters = {}
        
        publications = kwargs.get('publications', None)
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
                filters['publication_type'] = ContentType.objects.get_for_model(publications)
                filters['publication_id'] = publications.id
        
        publishable_models = kwargs.get('publishable_models', None)
        if publishable_models:
            if hasattr(publishable_models, '__iter__'):
                publishable_types = []
                for publishable_model in publishable_models:
                    publishable_types.append(ContentType.objects.get_for_model(publishable_model))
                filters['publishable_type__in'] = publishable_types
            else:
                filters['publishable_type'] = ContentType.objects.get_for_model(publishable_models)
        
        return self.filter(*queries, **filters)