from django.urls import path, include
from .views import Sections, schDetailView, schListView, Actions
from sch.views2 import schDetailAllEmptySlots


app_name = 'schd'

urlpatterns = [
    path('', schListView, name="list"),
    path('detail/<schId>/', schDetailView, name="detail"),
    path('partials/<schId>/stats/', Sections.schStats, name="stats"),
    path('partials/<schId>/empty/', schDetailAllEmptySlots, name="all-empty"),
    path('partials/<schId>/mistemplated/', Sections.schMistemplated, name="mistemplated"),
    path('partials/<schId>/unfavorables/', Sections.schUnfavorables, name="unfavorables"),
    path('partials/<schId>/emusr/', Sections.schEmusr, name="emusr"),
    
    #~~ ACTIONS ~~#
    path('detail/<schId>/actions/clear-all/', Actions.clearAll, name="clear-all"),
    path('detail/<schId>/actions/solve-tca/', Actions.solveTca, name="solve-tca"),
    path('detail/<schId>/actions/clear-slot/<wd>/<sft>/', Actions.clearSlot, name="clear-slot"),
    
]