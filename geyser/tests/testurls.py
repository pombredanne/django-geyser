from django.conf.urls.defaults import *

from geyser.tests.testapp.models import TestModel1

from geyser.views import PublishObject


urlpatterns = patterns('',
    (r'^t1/(\d+)/$', PublishObject(TestModel1)),
)