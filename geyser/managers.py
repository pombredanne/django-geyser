from datetime import datetime

from django.db.models import Manager, Q, get_model
from django.conf import settings
from django.core.exceptions import FieldError, ImproperlyConfigured
from django.contrib.contenttypes.models import ContentType

from rubberstamp.models import AppPermission, AssignedPermission
from geyser.query import GenericQuerySet


class DropletManager(Manager):
    """
    Custom manager for published objects, to support lookups by types, objects,
    streams, and other filters.
    
    """
    
    def get_query_set(self):
        """Returns a `GenericQuerySet` with related fields pre-selected."""
        return GenericQuerySet(self.model, using=self.db) \
            .select_related('first', 'stream').select_related_generic()
    
    def get_list(self, **kwargs):
        """
        Returns a list of `Droplet` instances, allowing for special filters.
        
        Accepts the following filters as keyword arguments:
        
        * `obj`: An instance of a publishable model. Returns publishings of
          this object only.
        * `models`: One or more (in a list or tuple) model classes. Returns
          publishings of these models only. Overridden by `obj` if both are
          given.
        * `stream`: One or more (in a list or tuple) stream instances. Only
          publishings to these streams will be returned.
        * `year`: Return only publications in the given year.
        * `month`: Similar to year. To get publishings in a specific month of
          a specific year, pass both.
        * `day`: Similar to year and month.
        * `obj_filters`: Filters to apply to the published model(s). Only
          publishings of objects matching these filters will be returned.
        * `include_unpublished`: Boolean indicating whether to include
          `Droplet`s that have been unpublished. Default is `False`.
        * `include_future`: Boolean, whether to include `Droplet`s with a
          publish date in the future. Default is `False`.
        
        """
        
        obj = kwargs.get('obj', None)
        models = kwargs.get('models', None)
        stream = kwargs.get('stream', None)
        queries = kwargs.get('queries', [])
        filters = kwargs.get('filters', {})
        obj_filters = kwargs.get('obj_filters', {})
        year = kwargs.get('year')
        month = kwargs.get('month')
        day = kwargs.get('day')
        include_unpublished = kwargs.get('include_unpublished', False)
        include_future = kwargs.get('include_future', False)
        
        if obj:
            queries.append(Q(object_id=obj.id))
            models = obj.__class__
            # if publishable is given, filter on its model
        
        if obj_filters and models is None:
            # if publishable filters is given, we must populate the model list
            models = []
            for app_model in settings.GEYSER_PUBLISHABLES:
                models.append(get_model(*app_model.split('.')))
        
        if models is not None:
            if not hasattr(models, '__iter__'):
                models = [models]
            model_q = Q(pk__isnull=True)
            for Model in models:
                try:
                    objs = Model.objects.filter(**obj_filters)
                    # if no filters were given, this will simply return all
                    # objects of this type
                except FieldError:
                    pass
                else:
                    model_q = model_q | Q(
                        content_type=ContentType.objects.get_for_model(Model),
                        object_id__in=objs.values_list('id', flat=True)
                    )
                    # add an OR for each publishable type
            queries.append(model_q)
        
        if stream is not None:
            if not hasattr(stream, '__iter__'):
                stream = [stream]
            queries.append(Q(stream__in=stream))
        
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
    
    def get_allowed_publications(self, obj, as_user=None, filter_from=None):
        """
        Returns a list of streams to which the given object can be published.
        
        `as_user`, if given, specifies a user whose permissions should be
        considered when determining where the object can be published. If not
        given, the object will be considered allowed to publish to any stream.
        
        `filter_from`, if given, specifies the "starting list" of streams which
        will be filtered by settings and user permissions.
        
        """
        
        model_str = '%s.%s' % (
            obj._meta.app_label, obj._meta.module_name)
        if model_str not in settings.GEYSER_PUBLISHABLES:
            raise ImproperlyConfigured('Object type must be in GEYSER_PUBLISHABLES.')
        if as_user and not as_user.is_superuser and \
                not as_user.has_perm('geyser.publish.%s' % model_str) and \
                not as_user.has_perm('geyser.publish', obj=obj):
            return None
        
        if as_user and not as_user.is_superuser and \
                not as_user.has_perm('geyser.publish_to.geyser.stream'):                
            allowed_streams = AppPermission.objects.get_permission_targets(
                'geyser.publish_to.geyser.stream', as_user)
        else:
            Stream = get_model('geyser', 'stream')
            allowed_streams = Stream.objects.all()
        
        if filter_from is None:
            return allowed_streams
        else:
            if not hasattr(filter_from, '__iter__'):
                filter_from = [filter_from]
            return filter(lambda p: p in allowed_streams, filter_from)
    
    def publish(self, obj, streams=None, as_user=None,
            **droplet_dict):
        """
        Publishes the given object.
        
        Where the object is published is determined by the `stream` and
        `as_user` keyword arguments (see below), and is filtered by the the
        `get_allowed_publications` method.
        
        `streams` can be given as a list of streams to which the object should
        be published. If omitted, the objects is published to all streams
        available for it.
        
        `as_user` specifies a user whose permissions should be taken into
        account when publishing. The object will only be published to
        streams to which the user is allowed to publish it, and the
        published_by attribute will be set to this user if not otherwise
        given. This can further restrict the list of publications, even if
        they are given explicitly.
        
        Any additional keyword arguments are passed to the `Droplet`
        constructor to specify explicit values for `Droplet` fields.
        
        """
        
        streams = self.get_allowed_publications(obj, as_user, streams)
        droplet_dict['content_object'] = obj
        if as_user and 'published_by' not in droplet_dict:
            droplet_dict['published_by'] = as_user
        
        droplets = []
        if streams:
            for stream in set(streams):
                droplet_dict['stream'] = stream
                droplets.append(self.create(**droplet_dict))
        
        return droplets
    
    def unpublish(self, obj, streams=None, as_user=None):
        """
        Un-publishes the given publishable.
        
        Sets the is_current flag to False so that (by default) queries do not
        find these droplets anymore.
        
        `streams` and `as_user` work exactly as they do for `publish()`,
        restricting the list of objects which are affected.
        
        """
        
        streams = self.get_allowed_publications(obj, as_user, streams)
        droplets = self.get_list(obj=obj, stream=streams)
        
        update_dict = {'is_current': False, 'updated': datetime.now()}
        if as_user:
            update_dict['updated_by'] = as_user
        
        droplets.update(**update_dict)
        
        return droplets
