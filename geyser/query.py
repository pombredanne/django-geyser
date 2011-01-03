from django.db.models.query import QuerySet

from django.contrib.contenttypes.generic import GenericForeignKey


class GenericQuerySet(QuerySet):
    """
    A queryset that can retrieve generically related objects in bulk queries.
    
    A `GenericQuerySet` preserves the "lazy evaluation" of a normal `QuerySet`
    while providing the benefits of bulk queries for generically related
    objects. It waits until it is evaluated to retrieve the related objects.
    This retrieval does cause the entire queryset to be cached, which could
    cause performance issues if the queryset is large.
    
    The `iterator()` method behaves as it does in a normal `QuerySet`, thus
    bypassing the caching of related objects entirely.
    
    """
    
    def __init__(self, *args, **kwargs):
        super(GenericQuerySet, self).__init__(*args, **kwargs)
        self._model_generic_fields = []
        self._select_related_fields = []
    
    def _clone(self, *args, **kwargs):
        clone = super(GenericQuerySet, self)._clone(*args, **kwargs)
        # copy the GenericQuerySet "private" attributes
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
        model_generic_fields = []
        for field in self.model._meta.virtual_fields:
            if isinstance(field, GenericForeignKey):
                model_generic_fields.append(field)
        if self.query.select_related is True:
            # select_related() has been called with no fields
            clone = self._clone()
        else:
            # add GFK content_type fields to select_related
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
        self._fill_for_generic()
        return super(GenericQuerySet, self).__iter__()
    
    def __contains__(self, item):
        self._fill_for_generic()
        return super(GenericQuerySet, self).__contains__(item)
    
    def _fill_for_generic(self):
        # fill the cache and attach related if select_related_generic
        # _model_generic_fields implies select_related_generic was called
        if self._model_generic_fields and self._result_cache is None:
            # fully populate the cache
            self._result_cache = []
            self._iter = self.iterator()
            while self._iter:
                self._fill_cache()
            
            # attach generically related objects
            ids_by_ct = {}
            for item in self._result_cache:
                # go through each field that is a GenericForeignKey
                for field in self._model_generic_fields:
                    # get the content type of the related object
                    content_type = getattr(item, field.ct_field)
                    ids_for_this_ct = ids_by_ct.setdefault(content_type, set())
                    # add the related object's id to the set
                    ids_for_this_ct.add(getattr(item, field.fk_field))
            objects_by_ct = {}
            for (ct, ids) in ids_by_ct.items():
                # fetch all the objects of this type by id
                objects_by_ct[ct] = ct.model_class().objects.in_bulk(ids)
            for item in self._result_cache:
                for field in self._model_generic_fields:
                    content_type = getattr(item, field.ct_field)
                    object_id = getattr(item, field.fk_field)
                    related_object = objects_by_ct[content_type][object_id]
                    # attach the related object to the GFK field
                    setattr(item, field.cache_attr, related_object)        
