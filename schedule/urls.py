from django.urls import path, include
from .views import Sections, schDetailView, schListView, Actions, groupedScheduleListView
from sch.views2 import schDetailAllEmptySlots
from flow.views import ApiViews, ApiActionViews
from sch.viewsets import EmpViews


"""
URLS.PY - SCHEDULE APP
======================
"""

__author__ = "Josh Steinbecker"


app_name = 'schd'

urlpatterns = [
    
    path('', schListView, name="list"),
    path('grouped/', groupedScheduleListView, name="list-grouped"),
    path('detail/<schId>/', schDetailView, name="detail"),
    path('detail/<schId>/wd/<wd>/', Actions.wd_redirect, name="wd-redirect"),
    path('detail/<schId>/modal/', Sections.modal, name='modal'),
    path('partials/<schId>/stats/', Sections.schStats, name="stats"),
    path('partials/<schId>/empty/', schDetailAllEmptySlots, name="all-empty"),
    path('partials/<schId>/mistemplated/', Sections.sch_mistemplated, name="mistemplated"),
    path('partials/<schId>/unfavorables/', Sections.schUnfavorables, name="unfavorables"),
    path('partials/<schId>/untrained/', Sections.schUntrained, name="untrained"),
    path('partials/<schId>/emusr/', ApiViews.schedule__get_emusr_range, name="emusr"),
    path('partials/<schId>/empty-list/', Sections.schEmptyList, name="empty-actionable-list"),
    path('partials/<schId>/pto-conflicts/', Sections.schPtoConflicts, name="pto-conflicts"),
    path('partials/<schId>/pto-conflicts/<emp>/', Sections.schPtoGrid, name="pto-grid"),
    path('partials/<schId>/turnarounds/', Sections.schTurnarounds, name="turnarounds"),
    path('partials/<schId>/log/', Sections.schLogView, name="log"),
    path('detail/<schId>/emusr-page/', Sections.schEmusrPage, name="emusr-page"),
    path('detail/<schId>/employees/', Sections.sch_employee_summary, name="employees"),
    path('detail/<schId>/emusr-page/<emp>/', Sections.schEmployeeEmusrSlots, name="emusr-empl"),
    path('detail/<schId>/set-sch-maxes/', Sections.sch_prn_empl_maxes, name="maxes"),
    path('detail/<schId>/version-compare/', Sections.version_compare, name="version-compare"),
    path('detail/<schId>/pto-requests/', Sections.schPtoRequests, name="pto-requests"),
    path('detail/<schId>/tdo-conflicts/', Sections.schTdoConflicts, name="tdo-conflicts"),
    path('detail/<schId>/undertime-view/', Sections.schUndertimeList, name="undertime-view"),
    path('detail/<schId>/manual-input/', Sections.sch_manual_data_entry, name="manual-input"),
    path('detail/<schId>/get-ut-data/<empl>/<prd>/', Sections.empl_prd_undertime_table, name="undertime-partial"),

    
    #~~ ACTIONS ~~#
    path('detail/<schId>/actions/set-templates/', Actions.set_templates, name="set-templates"),
    path('detail/<schId>/actions/clear-all/', Actions.clear_all, name="clear-all"),
    path('detail/<schId>/actions/clear-all-pto-conflicts/', Actions.clear_all_pto_conflicts, name="clear-all-ptoc"),
    path('detail/<schId>/actions/clear-all-unfavorables/', Actions.clear_unfavorables, name="clear-all-unfavorables"),
    path('detail/<schId>/actions/solve-tca/', Actions.solve_with_tca, name="solve-tca"),
    path('detail/<schId>/actions/solve-signal-opti/', Actions.solve_with_signal_optimization, name="solve-signal-opti"),
    path('detail/<schId>/actions/solve-beta/', Actions.beta_solving_model, name="solve-beta"),
    path('detail/<schId>/actions/clear-slot/<wd>/<sft>/', Actions.clear_slot, name="clear-slot"),
    path('detail/<schId>/actions/override-slot/<wd>/<sft>/<empId>/', Actions.override_slot, name="override-slot"),
    path('detail/<schId>/actions/update/<wd>/<sft>/<empl>/', Actions.update_slot, name="update-slot"),
    path('detail/<schId>/actions/update-fills-with/', Actions.Updaters.update_fills_with, name="update-fills-with-data"),
    path('detail/<schId>/actions/retemplate-all/', Actions.retemplate_all, name="retemplate-all-mistemplated"),
    path('detail/<schId>/actions/clear-untrained/', Actions.clear_untrained, name="clear-untrained"),
    path('detail/<schId>/actions/fill-with-favorables/', Actions.fill_with_favorables, name="fill-with-favorables"),
    path('detail/<schId>/actions/step=balance-emusr/', Actions.EmusrBalancer.get_tradable_slots, name="step-balancing-emusr"),
    path('detail/<schId>/build-alt-draft/', ApiActionViews.build_alternate_draft, name='sch__build_alt_draft'),
    path('detail/<schId>/delete/', ApiActionViews.delete_schedule, name='sch__delete'),
    path('detail/<schId>/actions/clear-prn-slots/', Actions.clearPrnEmployeeSlots, name="clear-prn-slots"),
    path('detail/<schId>/actions/clear-ot-slots/', Actions.clearOvertimeSlotsByRefillability, name="clear-ot-slots"),
    path('detail/<schId>/actions/clear-over-fte-maxes/', Actions.sch_clear_over_empl_maxes, name="clear-overFte"),
    path('detail/<schId>/actions/publish/', Actions.publish_view, name="publish"),
    path('detail/<schId>/actions/unpublish/', Actions.unpublish_view, name="unpublish"),
    path('detail/<schId>/actions/remove-employee/<empId>/', Actions.remove_prn_employee, name="remove-employee"),
    path('detail/<schId>/actions/resolve-all-tdo/', Actions.resolve_all_tdo_conflicts, name="resolve-tdo-conflicts"),
    path('detail/<schId>/actions/attempt-underhours-solve/', Actions.fill_undertime_slots, name="attempt-underhours-solve"),
    

    
] 