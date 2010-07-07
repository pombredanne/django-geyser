from datetime import datetime

from django.db.models import Manager, Q
from django.conf import settings
from django.contrib.contenttypes.models import ContentType

from authority.sites import site as auth_site
from authority.models import Permission

class DropletManager(Manager):
    """
    Custom manager for published objects, to support lookups by types and
    instances of publishables and publications.
    """
    
    def get_query_set(self):
        #this select_related doesn't actually do anything
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
        
        if publishable_models is not None:
            if hasattr(publishable_models, '__iter__'):
                publishable_types = []
                for publishable_model in publishable_models:
                    publishable_types.append(ContentType.objects.get_for_model(publishable_model))
                queries.append(Q(publishable_type__in=publishable_types))
            else:
                queries.append(Q(publishable_type=ContentType.objects.get_for_model(publishable_models)))
        
        if publications is not None:
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
    
    def get_allowed_publications(self, publishable, as_user=None, filter_from=None):
        """
        Return a list of publications to which the given user is allowed to
        publish the given object.
        
        """
        
        Publishable = publishable.__class__
        publishable_model = Publishable.__name__.lower()
        
        if as_user:
            if not as_user.has_perm('geyser.add_droplet'):
                return None
            PublishablePermission = auth_site.get_permissions_by_model(Publishable)[0]
            if not PublishablePermission(as_user).has_perm('%s_permission.publish_%s'
                    % (publishable_model, publishable_model), publishable):
                return None
        
        allowed_publications = []
        publishable_key = '%s.%s' % (Publishable._meta.app_label, publishable_model)
        for app_model in settings.GEYSER_PUBLISHABLES[publishable_key]['publish_to']:
            (publication_app, publication_model) = app_model.split('.')
            publication_type = ContentType.objects.get(
                app_label=publication_app, model=publication_model)
            Publication = publication_type.model_class()
            if as_user and not as_user.is_superuser:
                perm_name = '%s_permission.publish_%s_to_%s' % \
                    (publication_model, publishable_model, publication_model)
                publication_perms = Permission.objects.user_permissions(
                    as_user, perm_name, Publication)
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
        
        update_dict = {'is_newest': False}
        if as_user:
            update_dict['updated_by'] = as_user
        
        droplets.update(is_newest=False)
        
        return droplets