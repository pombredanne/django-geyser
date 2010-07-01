from django.db import models

from django.contrib.auth.models import User

class TestModel(models.Model):
    name = models.CharField(max_length=50)
    class Meta:
        abstract = True
        ordering = ['id']
    def __unicode__(self):
        return self.name

class TestModel1(TestModel):
    owner = models.ForeignKey(User)

class TestModel2(TestModel):
    pass

class TestModel3(TestModel):
    pass
