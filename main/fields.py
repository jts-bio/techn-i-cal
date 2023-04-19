from django.db import models
from re import sub

def slugify (self, string, allow_unicode=False):
    return sub (r'[\s-]', '_', string.strip ().lower ())
    
class AutoSlugField (models.SlugField):
    
    def __init__ (self, populate_from, slugify_function=None, populate_unique=True, *args, **kwargs):
        self.populate_from      = populate_from
        self.slugify_function   = slugify_function if slugify_function else slugify
        self.populate_unique    = populate_unique
        kwargs['max_length']    = kwargs.get ('max_length', 150)
        kwargs['blank']         = kwargs.get ('blank', True)
        kwargs['allow_unicode'] = kwargs.get ('allow_unicode', True)
        
        super ().__init__ (*args, **kwargs)
        