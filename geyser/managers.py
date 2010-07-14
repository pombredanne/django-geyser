from datetime import datetime

from django.db.models import Manager, Q
from django.conf import settings
from django.core.exceptions import FieldError
from django.contrib.contenttypes.models import ContentType

from geyser.permission_models import PublishablePermission, PublicationPermission


class DropletManager(Manager):
    """
    Custom manager for published objects, to support lookups by types and
    instances of publishables and publications.
    """
    
    def get_query_set(self):
        return super(DropletManager, self).get_query_set().select_related('first')
    
    def get_list(self, **kwargs):
        """Get a list of Droplet instances, filtered in useful ways."""
        
        publishable = kwargs.get('publishable', None)
        publishable_models = kwargs.get('publishable_models', None)
        publications = kwargs.get('publications', None)
        queries = kwargs.get('queries', [])
        filters = kwargs.get('filters', {})
        publishable_filters = kwargs.get('publishable_filters', {})
        year = kwargs.get('year')
        month = kwargs.get('month')
        day = kwargs.get('day')
        include_old = kwargs.get('include_old', False)
        include_future = kwargs.get('include_future', False)
        
        if publishable:
            queries.append(Q(publishable_id=publishable.id))
            publishable_models = publishable.__class__
        
        if publishable_filters and publishable_models is None:
            publishable_models = []
            for publishable_app_model in settings.GEYSER_PUBLISHABLES:
                (app_name, model_name) = publishable_app_model.split('.')
                publishable_type = ContentType.objects.get(app_label=app_name, model=model_name)
                publishable_models.append(publishable_type.model_class())
        
        if publishable_models is not None:
            if not hasattr(publishable_models, '__iter__'):
                publishable_models = [publishable_models]
            publishable_q = Q(pk__isnull=True)
            for Model in publishable_models:
                try:
                    publishables = Model.objects.filter(**publishable_filters)
                except FieldError:
                    pass
                else:
                    publishable_q = publishable_q | Q(
                        publishable_type=ContentType.objects.get_for_model(Model),
                        publishable_id__in=publishables.values_list('id', flat=True)
                    )
            queries.append(publishable_q)
        
        if publications is not None:
            if not hasattr(publications, '__iter__'):
                publications = [publications]
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
    
    def get_allowed_publications(self, publishable, as_user=None, filter_from=None):
        """
        Return a list of publications to which the given user is allowed to
        publish the given object.
        
        """
        
        Publishable = publishable.__class__
        publishable_type = ContentType.objects.get_for_model(Publishable)
        
        if as_user and not as_user.is_superuser:
            if not as_user.has_perm('geyser.add_droplet'):
                return None
            if not PublishablePermission.objects.filter(
                    content_type=publishable_type,
                    object_id=publishable.id,
                    user=as_user).exists():
                return None
        
        allowed_publications = []
        publishable_key = '%s.%s' % (publishable_type.app_label, publishable_type.model)
        for app_model in settings.GEYSER_PUBLISHABLES[publishable_key]['publish_to']:
            (publication_app, publication_model) = app_model.split('.')
            publication_type = ContentType.objects.get(
                app_label=publication_app, model=publication_model)
            Publication = publication_type.model_class()
            if as_user and not as_user.is_superuser:
                publication_perms = PublicationPermission.objects.filter(
                    content_type=publication_type,
                    publishable_type=publishable_type,
                    user=as_user)
                allowed_of_type = Publication.objects.filter(
                    id__in=publication_perms.values_list('object_id', flat=True))
                allowed_publications.extend(allowed_of_type)
            else:
                allowed_publications.extend(Publication.objects.all())
        
        if filter_from is None:
            return allowed_publications
        else:
            if not hasattr(filter_from, '__iter__'):
                filter_from = [filter_from]
            return filter(lambda p: p in allowed_publications, filter_from)
    
    
    def publish(self, publishable, publications=None, as_user=None, **droplet_dict):
        publications = self.get_allowed_publications(publishable, as_user, publications)
        droplet_dict['publishable'] = publishable
        if as_user and 'published_by' not in droplet_dict:
            droplet_dict['published_by'] = as_user
        
        droplets = []
        for publication in set(publications):
            droplet_dict['publication'] = publication
            droplets.append(self.create(**droplet_dict))
        
        return droplets
    
    
    def unpublish(self, publishable, publications=None, as_user=None):
        publications = self.get_allowed_publications(publishable, as_user, publications)
        droplets = self.get_list(publishable=publishable, publications=publications)
        
        update_dict = {'is_newest': False, 'updated': datetime.now()}
        if as_user:
            update_dict['updated_by'] = as_user
        
        droplets.update(**update_dict)
        
        return droplets