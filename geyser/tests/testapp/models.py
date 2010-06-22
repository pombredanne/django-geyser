from django.db import models

from django.contrib.auth.models import User

class TestModel1(models.Model):
    name = models.CharField(max_length=50)
    owner = models.ForeignKey(User)
    def __unicode__(self):
        return self.name

class TestModel2(models.Model):
    name = models.CharField(max_length=50)
    def __unicode__(self):
        return self.name

class TestModel3(models.Model):
    name = models.CharField(max_length=50)
    def __unicode__(self):
        return self.name