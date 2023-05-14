from django.db import models
from re import sub

def slugify (self, string, allow_unicode=False):
    return sub (r'[\s-]', '_', string.strip ().lower ())


        
class AutoSlugFieldModel (models.Model):

    id = models.AutoField(primary_key=True)
    slug = models.SlugField (max_length=300, unique=True, blank=True, null=True)

    def save (self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify (self.name)
        super ().save (*args, **kwargs)