===============
 django-geyser
===============

Publishing. Intended primarily for a "wall" or "life stream" concept.

Depends on the `auth` and `contenttypes` apps from `contrib`, and `jlecker`'s
`django-rubberstamp <http://github.com/jlecker/django-rubberstamp>`_.



Settings
========

Settings are contained in a single dictionary called ``GEYSER_PUBLISHABLES``.
As an example, here are the settings used in the test suite (explanation
follows)::

    GEYSER_PUBLISHABLES = {
        'testapp.testmodel1': {
            'auto_perms': ('owner',),
        },
        'testapp.testmodel2': {
            'unique_for_date': ('name',),
        }
        'testapp.testmodel3': {},
    }

Each key is a type of object that can be published, given as a string in the
format ``'app_name.model_name'``. This specifies that the models `TestModel1`
and `TestModel2` from the app `testapp` can be published using Geyser. The
value for each key is another dictionary which specifies more information about
how to publish objects of this type.

The ``'auto_perms'`` option specifies an iterable of fields on the publishable
model which are foreign keys to `User`. When an object of this type is created,
if the value of this field (if any) will automatically be given permission to
publish the new object. This is useful for making sure that the creator of an
object has permission to publish it.

The ``'unique_for_date'`` option specifies an iterable of fields on the
publishable model which should have a unique canonical publish date. The
canonical date is the first date on which the object was published. If fields
are given here, they will be checked for uniqueness when the publishable is
first published, raising a `ValidationError` if the publishing fails.



Models
======

Publishing in `Geyser` is based around two concepts: a `Stream` and a
`Droplet`. A `Stream` is where items are published, i.e. something like a
user's "wall" or "life stream". A `Droplet` is an individual item published to
a `Stream`, like a blog post on a user's profile stream.


Droplet
-------

* `content_object`: The object which is published.
* `stream`: The stream which the object is published to.
* `first`: The `Droplet` corresponding to the first time the content_object
  was published. Can be self.
* `is_current`: Whether this publishing is current (has not been
  unpublished).
* `published`: The datetime that this `Droplet` was created.
* `update`: The datetime that this `Droplet` was updated (probably means
  it was unpublished).
* `published_by`: The user who created this `Droplet`.
* `updated_by`: The user who updated this `Droplet` (likely unpublished).



Manager Methods
===============

Most of the action in `Geyser` happens in manager methods on the Droplet model,
which can be used like so::
    
    from geyser.models import Droplet
    
    Droplet.objects.publish(some_object, some_stream)

This would publish the object `some_object` to the stream `some_stream`.


publish
-------

Publishes the given object::
    
    publish(self, obj, streams=None, as_user=None, **droplet_dict)
    
Where the object is published is determined by the `stream` and `as_user`
keyword arguments (see below), and is filtered by the the
`get_allowed_publications` method.

`streams` can be given as a list of streams to which the object should be
published. If omitted, the objects is published to all streams available for
it.

`as_user` specifies a user whose permissions should be taken into account when
publishing. The object will only be published to streams to which the user is
allowed to publish it, and the published_by attribute will be set to this user
if not otherwise given. This can further restrict the list of publications,
even if they are given explicitly.

Any additional keyword arguments are passed to the `Droplet` constructor to
specify explicit values for `Droplet` fields.


unpublish
---------

Un-publishes the given publishable::

    unpublish(self, obj, streams=None, as_user=None)
    
Sets the is_current flag to False so that (by default) queries do not find
these droplets anymore.

`streams` and `as_user` work exactly as they do for `publish()`, restricting
the list of objects which are affected.


get_list
--------

Returns a queryset of `Droplet` instances, allowing for special filters::

    get_list(self, **kwargs)

Accepts the following filters as keyword arguments:

* `obj`: An instance of a publishable model. Returns publishings of this object
  only.
* `models`: One or more (in a list or tuple) model classes. Returns publishings
  of these models only. Overridden by `obj` if both are given.
* `stream`: One or more (in a list or tuple) stream instances. Only publishings
  to these streams will be returned. If you already have a `Stream` instance,
  and would like to get the `Droplet`s published to it, you can also use
  ``stream_instance.droplets.get_list()`` to access this method, filtered for
  the `Stream` instance.
* `year`: Return only publications in the given year.
* `month`: Similar to year. To get publishings in a specific month of a
  specific year, pass both.
* `day`: Similar to year and month.
* `obj_filters`: Filters to apply to the published model(s). Only publishings
  of objects matching these filters will be returned.
* `include_unpublished`: Boolean indicating whether to include `Droplet`s that
  have been unpublished. Default is `False`.
* `include_future`: Boolean, whether to include `Droplet`s with a publish date
  in the future. Default is `False`.



GenericQuerySet
===============

`DropletManager` methods (including ``get_list``) return a special type of
queryset that will fetch any generically-related objects in bulk queries, so
that iterating through a queryset of `Droplet`'s will not perform an extra
query for each one.

This `GenericQuerySet` preserves the "lazy evaluation" of a normal `QuerySet`
while providing the benefits of bulk queries for generically related objects.
It waits until it is evaluated to retrieve the related objects. This retrieval
does cause the entire queryset to be cached, which could cause performance
issues if the queryset is large.

The `iterator()` method behaves as it does in a normal `QuerySet`, thus
bypassing the caching of related objects entirely.
