from django.urls import path, include
from .views import Sections, schDetailView


app_name = 'schd'

urlpatterns = [
    path('detail/<schId>/', schDetailView, name="detail"),
    path('partials/<schId>/stats/', Sections.schStats, name="stats"),
]