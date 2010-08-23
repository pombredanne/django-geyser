from datetime import datetime

from django.db.models import Manager, Q, get_model
from django.conf import settings
from django.core.exceptions import FieldError, ImproperlyConfigured
from django.contrib.contenttypes.models import ContentType

from rubberstamp.models import AppPermission, AssignedPermission
from geyser.query import GenericQuerySet


class DropletManager(Manager):
    """
    Custom manager for published objects, to support lookups by types and
    instances of publishables and publications.
    
    """
    
    def get_query_set(self):
        """Returns a `GenericQuerySet` with related fields pre-selected."""
        return GenericQuerySet(self.model, using=self.db) \
            .select_related('first').select_related_generic()
    
    def get_list(self, **kwargs):
        """
        Returns a list of `Droplet` instances, allowing for special filters.
        
        Accepts the following filters as keyword arguments:
        
        * `publishable`: An instance of a publishable model. Returns
          publishings of this object only.
        * `publishable_models`: One or more (in a list or tuple) publishable
          model classes. Returns publishings of these models only. Overridden
          by `publishable` if both are given.
        * `publications`: One or more (in a list or tuple) publication
          instances. Only publishings to these objects will be returned.
        * `year`: Return only publications in the given year.
        * `month`: Similar to year. To get publishings in a specific month of
          a specific year, pass both.
        * `day`: Similar to year and month.
        * `publishable_filters`: Filters to apply to the publishable model(s).
          Only publishings of objects matching these filters will be returned.
        * `include_unpublished`: Boolean indicating whether to include
          `Droplet`s that have been unpublished. Default is `False`.
        * `include_future`: Boolean, whether to include `Droplet`s with a
          publish date in the future. Default is `False`.
        
        """
        
        publishable = kwargs.get('publishable', None)
        publishable_models = kwargs.get('publishable_models', None)
        publications = kwargs.get('publications', None)
        queries = kwargs.get('queries', [])
        filters = kwargs.get('filters', {})
        publishable_filters = kwargs.get('publishable_filters', {})
        year = kwargs.get('year')
        month = kwargs.get('month')
        day = kwargs.get('day')
        include_unpublished = kwargs.get('include_unpublished', False)
        include_future = kwargs.get('include_future', False)
        
        if publishable:
            queries.append(Q(publishable_id=publishable.id))
            publishable_models = publishable.__class__
            # if publishable is given, filter on its model
        
        if publishable_filters and publishable_models is None:
            # if publishable filters is given, we must populate the model list
            publishable_models = []
            for publishable_app_model in settings.GEYSER_PUBLISHABLES:
                (app_name, model_name) = publishable_app_model.split('.')
                publishable_type = ContentType.objects.get(
                    app_label=app_name, model=model_name)
                publishable_models.append(publishable_type.model_class())
        
        if publishable_models is not None:
            if not hasattr(publishable_models, '__iter__'):
                publishable_models = [publishable_models]
            publishable_q = Q(pk__isnull=True)
            for Model in publishable_models:
                try:
                    publishables = Model.objects.filter(**publishable_filters)
                    # if no filters were given, this will simply return all
                    # publishables of this type
                except FieldError:
                    pass
                else:
                    publishable_q = publishable_q | Q(
                        publishable_type=ContentType.objects.get_for_model(Model),
                        publishable_id__in=publishables.values_list('id', flat=True)
                    )
                    # add an OR for each publishable type
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
                # add an OR for each type, similar to the publishable query
            queries.append(publication_q)
        
        if year:
            queries.append(Q(published__year=year))
        if month:
            queries.append(Q(published__month=month))
        if day:
            queries.append(Q(published__day=day))
        if not include_unpublished:
            filters['is_current'] = True
        if not include_future:
            filters['published__lte'] = datetime.now()
        
        return self.filter(*queries, **filters)
    
    def get_allowed_publications(self, publishable, as_user=None, filter_from=None):
        """
        Returns a list of publications to which the given publishable object
        can be published.
        
        `as_user`, if given, specifies a user whose permissions should be
        considered when determining where the object can be published. If not
        given, the object will be considered allowed to publish to any related
        publications from the `GEYSER_PUBLISHABLES` setting.
        
        `filter_from`, if given, specifies the "starting list" of publications
        which will be filtered by settings and user permissions.
        
        """
        
        publishable_str = '%s.%s' % (
            publishable._meta.app_label, publishable._meta.module_name)        
        if publishable_str not in settings.GEYSER_PUBLISHABLES:
            raise ImproperlyConfigured('Publishable type must be in GEYSER_PUBLISHABLES.')
        if as_user and not as_user.is_superuser and \
                not as_user.has_perm('geyser.publish.%s' % publishable_str) and \
                not as_user.has_perm('geyser.publish', obj=publishable):
            return None
        
        allowed_publications = []
        to_types = settings.GEYSER_PUBLISHABLES[publishable_str]['publish_to']
        for publication_str in to_types:
            (publication_app, publication_model) = publication_str.split('.')
            Publication = get_model(publication_app, publication_model)
            
            to_perm = 'geyser.publish_to.%s' % publication_str
            if as_user and not as_user.is_superuser and \
                    not as_user.has_perm(to_perm):                
                allowed = AppPermission.objects.get_permission_targets(
                    'geyser.publish_to.%s' % publication_str, as_user)
                allowed_publications.extend(allowed)
            else:
                allowed_publications.extend(Publication.objects.all())
        
        if filter_from is None:
            return allowed_publications
        else:
            if not hasattr(filter_from, '__iter__'):
                filter_from = [filter_from]
            return filter(lambda p: p in allowed_publications, filter_from)
    
    def publish(self, publishable, publications=None, as_user=None,
            **droplet_dict):
        """
        Publishes the given publishable object.
        
        Where the object is published is determined by the publications and
        as_user keyword arguments (see below), and is filtered by the the
        `get_allowed_publications` method.
        
        `publications` can be given as a list of publications to which the
        object should be published. If omitted, the publishable is published
        to all publications available for it.
        
        `as_user` specifies a user whose permissions should be taken into
        account when publishing. The object will only be published to
        publications to which the user is allowed to publish it, and the
        published_by attribute will be set to this user if not otherwise
        given. This can further restrict the list of publications, even if
        they are given explicitly.
        
        Any additional keyword arguments are passed to the `Droplet`
        constructor to specify explicit values for `Droplet` fields.
        
        """
        
        publications = self.get_allowed_publications(
            publishable, as_user, publications)
        droplet_dict['publishable'] = publishable
        if as_user and 'published_by' not in droplet_dict:
            droplet_dict['published_by'] = as_user
        
        droplets = []
        if publications:
            for publication in set(publications):
                droplet_dict['publication'] = publication
                droplets.append(self.create(**droplet_dict))
        
        return droplets
    
    def unpublish(self, publishable, publications=None, as_user=None):
        """
        Un-publishes the given publishable.
        
        Sets the is_current flag to False so that (by default) queries do not
        find these droplets anymore.
        
        `publications` and `as_user` work exactly as they do for `publish()`,
        restricting the list of objects which are affected.
        
        """
        
        publications = self.get_allowed_publications(
            publishable, as_user, publications)
        droplets = self.get_list(publishable=publishable,
            publications=publications)
        
        update_dict = {'is_current': False, 'updated': datetime.now()}
        if as_user:
            update_dict['updated_by'] = as_user
        
        droplets.update(**update_dict)
        
        return droplets