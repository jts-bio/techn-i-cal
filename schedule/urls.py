from django.urls import path, include
from .views import Sections, schDetailView, schListView, Actions
from sch.views2 import schDetailAllEmptySlots
from flow.views import ApiViews


app_name = 'schd'

urlpatterns = [
    path('', schListView, name="list"),
    path('detail/<schId>/', schDetailView, name="detail"),
    path('detail/<schId>/wd/<wd>/', Actions.wdRedirect, name="wd-redirect"),
    path('detail/<schId>/modal/', Sections.modal, name='modal'),
    path('partials/<schId>/stats/', Sections.schStats, name="stats"),
    path('partials/<schId>/empty/', schDetailAllEmptySlots, name="all-empty"),
    path('partials/<schId>/mistemplated/', Sections.schMistemplated, name="mistemplated"),
    path('partials/<schId>/unfavorables/', Sections.schUnfavorables, name="unfavorables"),
    path('partials/<schId>/untrained/', Sections.schUntrained, name="untrained"),
    path('partials/<schId>/emusr/', ApiViews.schedule__get_emusr, name="emusr"),
    path('partials/<schId>/empty-list/', Sections.schEmptyList, name="empty-actionable-list"),
    path('partials/<schId>/pto-conflicts/', Sections.schPtoConflicts, name="pto-conflicts"),
    path('partials/<schId>/pto-conflicts/<emp>/', Sections.schPtoGrid, name="pto-grid"),
    
    
    #~~ ACTIONS ~~#
    path('detail/<schId>/actions/clear-all/', Actions.clearAll, name="clear-all"),
    path('detail/<schId>/actions/solve-tca/', Actions.solveTca, name="solve-tca"),
    path('detail/<schId>/actions/clear-slot/<wd>/<sft>/', Actions.clearSlot, name="clear-slot"),
    path('detail/<schId>/actions/override-slot/<wd>/<sft>/<empId>/', Actions.overrideSlot, name="override-slot"),
    path('detail/<schId>/actions/update/<wd>/<sft>/<empl>/', Actions.updateSlot, name="update-slot"),
    path('detail/<schId>/actions/retemplate-all/', Actions.retemplateAll, name="retemplate-all-mistemplated"),
]