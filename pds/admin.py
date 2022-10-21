from django.contrib import admin
from .models import Drug, Diluent, Compound
# Register your models here.


admin.site.register(Drug)
admin.site.register(Diluent)
admin.site.register(Compound)
