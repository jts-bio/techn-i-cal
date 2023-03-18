from .views import * 
from django.urls import set_urlconf, path 


app_name = 'prd'

urlpatterns = [
    path("<schId>/<int:n>/", prd_detail, name="detail"),
    
    # TESTS :::
    path("preline-table/", preline_table, name="preline-table"),
]