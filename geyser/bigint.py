from django.core import exceptions
from django.conf import settings
from django.db import connection
from django.db.models import fields
from django.utils.translation import ugettext as _


__version__ = "1.0"
__author__ = "Florian Leitner"


class BigAutoField(fields.AutoField):
        
    def db_type(self):
        if settings.DATABASE_ENGINE == 'mysql':
            return "bigint AUTO_INCREMENT"
        elif settings.DATABASE_ENGINE == 'oracle':
            return "NUMBER(19)"
        elif settings.DATABASE_ENGINE[:8] == 'postgres':
            return "bigserial"
        elif settings.DATABASE_ENGINE == 'sqlite3':
            return "integer"
        else:
            raise NotImplemented
    
    def get_internal_type(self):
        return "BigAutoField"
    
    def to_python(self, value):
        if value is None:
            return value
        try:
            return long(value)
        except (TypeError, ValueError):
            raise exceptions.ValidationError(
                _("This value must be a long integer."))