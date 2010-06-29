from datetime import datetime

from django.db.models import Manager, Q
from django.conf import settings
from django.contrib.contenttypes.models import ContentType


class DropletManager(Manager):
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
        year = kwargs.get('year')
        month = kwargs.get('month')
        day = kwargs.get('day')
        include_old = kwargs.get('include_old', False)
        include_future = kwargs.get('include_future', False)
 
        if publishable:
            queries.append(Q(publishable_id=publishable.id))
            publishable_models = publishable
        
        if publishable_models:
            if hasattr(publishable_models, '__iter__'):
                publishable_types = []
                for publishable_model in publishable_models:
                    publishable_types.append(ContentType.objects.get_for_model(publishable_model))
                queries.append(Q(publishable_type__in=publishable_types))
            else:
                queries.append(Q(publishable_type=ContentType.objects.get_for_model(publishable_models)))
        
        if publications:
            if hasattr(publications, '__iter__'):
                publications_by_type = {}
                for publication in publications:
                    publication_type = ContentType.objects.get_for_model(publication)
                    publication_pks = publications_by_type.setdefault(publication_type, [])
                    publication_pks.append(publication.pk)
                publication_q = Q(pk__isnull=True)
                for publication_type in publications_by_type:
                    publication_q = publication_q | Q(
                        publication_type=publication_type,
                        publication_id__in=publications_by_type[publication_type]
                    )
                queries.append(publication_q)
            else:
                queries.append(Q(
                    publication_type=ContentType.objects.get_for_model(publications),
                    publication_id=publications.id
                ))
        
        if year:
            queries.append(Q(published__year=year))
        if month:
            queries.append(Q(published__month=month))
        if day:
            queries.append(Q(published__day=day))
        if not include_old:
            filters['is_newest'] = True
        if not include_future:
            filters['published__lte'] = datetime.now()
        
        return self.filter(*queries, **filters)