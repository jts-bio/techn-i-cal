from django.urls import path, include
from .views import Sections, schDetailView, schListView
from sch.views2 import schDetailAllEmptySlots


app_name = 'schd'

urlpatterns = [
    path('', schListView, name="list"),
    path('detail/<schId>/', schDetailView, name="detail"),
    path('partials/<schId>/stats/', Sections.schStats, name="stats"),
    path('partials/<schId>/empty/', schDetailAllEmptySlots, name="all-empty"),
]