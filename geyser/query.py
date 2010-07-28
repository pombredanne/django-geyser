from django.db.models.query import QuerySet

from django.contrib.contenttypes.generic import GenericForeignKey


class GenericQuerySet(QuerySet):
    """
    A queryset that can retrieve generically related objects in bulk queries.
    
    A `GenericQuerySet` preserves the "lazy evaluation" of a normal `QuerySet`
    while providing the benefits of bulk queries for generically related
    objects. It waits until it is evaluated to retrieve the related objects.
    This retrieval does cause the entire queryset to be cached, which could
    cause performance issues if the queryset is not sliced.
    
    The `iterator()` method behaves as it does in a normal `QuerySet`, thus
    bypassing the caching of related objects entirely.
    
    """
    
    def __init__(self, *args, **kwargs):
        super(GenericQuerySet, self).__init__(*args, **kwargs)
        self._model_generic_fields = []
        self._select_related_fields = []
    
    def _clone(self, *args, **kwargs):
        clone = super(GenericQuerySet, self)._clone(*args, **kwargs)
        clone._model_generic_fields = self._model_generic_fields
        clone._select_related_fields = self._select_related_fields
        return clone
    
    def select_related_generic(self):
        """
        Returns a new `GenericQuerySet` instance that will fetch and cache
        generically related objects when evaluated.
        
        """
        
        if self._model_generic_fields:
            return self
        else:
            model_generic_fields = []
            for field in self.model._meta.virtual_fields:
                if isinstance(field, GenericForeignKey):
                    model_generic_fields.append(field)
            if self.query.select_related is True:
                clone = self._clone()
                clone._model_generic_fields = model_generic_fields
                return clone
            else:
                fields = self._select_related_fields + \
                    [f.ct_field for f in model_generic_fields]
                clone = super(GenericQuerySet, self).select_related(*fields)
                clone._model_generic_fields = model_generic_fields
                return clone
    
    def select_related(self, *fields, **kwargs):
        #  guarantees that content type fields for generic foreign keys are
        # included if select_related_generic has been called
        fields = list(fields)
        select_fields = fields[:]
        if self._model_generic_fields and fields and not kwargs:
            for generic_field in self._model_generic_fields:
                select_fields.append(generic_field.ct_field)
        clone = super(GenericQuerySet, self).select_related(*select_fields, **kwargs)
        clone._select_related_fields = fields
        return clone
    
    def __iter__(self):
        if self._model_generic_fields:
            # fill the cache completely before fetching related objects
            if self._result_cache is None:
                self._iter = self.iterator()
                self._result_cache = []
            if self._iter:
                attach_related = True
                try:
                    while True:
                        self._result_cache.append(self._iter.next())
                except StopIteration:
                    self._iter = None
            else:
                attach_related = False
            
            # this is the select_related_generic part
            if attach_related:
                ids_by_type = {}
                for item in self._result_cache:
                    for field in self._model_generic_fields:
                        content_type = getattr(item, field.ct_field)
                        ids_for_type = ids_by_type.setdefault(content_type, set())
                        ids_for_type.add(getattr(item, field.fk_field))
                
                objects_by_type = {}
                for (type, ids) in ids_by_type.items():
                    objects_by_type[type] = type.model_class().objects.in_bulk(ids)
                
                for item in self._result_cache:
                    for field in self._model_generic_fields:
                        content_type = getattr(item, field.ct_field)
                        object_id = getattr(item, field.fk_field)
                        related_object = objects_by_type[content_type][object_id]
                        setattr(item, field.cache_attr, related_object)
            
            return iter(self._result_cache)
        else:
            return super(GenericQuerySet, self).__iter__()
    
    def __contains__(self, item):
        # always fill the cache completely if select_generic_related was called
        if self._model_generic_fields and self._result_cache is None:
            iter(self)
            return item in self._result_cache
        else:
            return super(GenericQuerySet, self).__contains__(item)