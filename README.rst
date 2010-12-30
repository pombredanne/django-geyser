Publishing with per-object permissions. Support for feeds, aggregation, and
"lifestream" concepts.

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
value for each key is another dictionary which specifies more information
about how to publish objects of this type.

The ``'auto_perms'`` option specifies an iterable of fields on the publishable
model which are foreign keys to `User`. When an object of this type is
created, if the value of this field (if any) will automatically be given
permission to publish the new object. This is useful for making sure that the
creator of an object has permission to publish it.

The ``'unique_for_date'`` option specifies an iterable of fields on the
publishable model which should have a unique canonical publish date. The
canonical date is the first date on which the object was published. If fields
are given here, they will be checked for uniqueness when the publishable is
first published, raising a `ValidationError` if the publishing fails.
