from django.urls import path, include
from django.contrib import admin
from . import views, actions, views2, viewsets
from . import api
from .api import WeekApi, WdApi, ScheduleApi, SlotApi
from rest_framework import routers
from .viewsets import EmpViews



"""
URLS FOR THE SCHEDULE APP WITHIN FLOWRATE

``site.com/sch/ ...`
"""

app_name = "sch"

router = routers.DefaultRouter()
router.register(r'employees', viewsets.EmployeeViewSet)
router.register(r'shifts', viewsets.ShiftViewSet)
router.register(r'workdays', viewsets.WorkdayViewSet)
router.register(r'slots', viewsets.SlotViewSet)
router.register(r'weeks', viewsets.WeekViewSet)
router.register(r'periods', viewsets.PeriodViewSet)
router.register(r'schedules',  viewsets.ScheduleViewSet)
router.register(r'pto-requests', viewsets.PtoRequestViewSet)

# ========================================================= #

urlpatterns = [
    path("", views.index, name="index"),
    path("rest/", include(router.urls)),
    path("pto-requests/all/", views.PTO.PtoManagerView.as_view(), name="pto-request-list"),
    path("docs/week/", views.DOCUMENTATION.weekly, name="docs-week"),
]

user_patterns = [
    path("user/<uname>/", viewsets.UserViews.userDetailView, name="user-detail"),
]

workday_patterns = [
    # ? ==== Workday ==== ?#
    path("days/new/", views.WORKDAY.WorkdayBulkCreateView.as_view(), name="workday-new"),
    path("workday-list-view/all/",views.WORKDAY.WorkdayListView.as_view(),name="v2-workday-list",),
    path("v1/workday-detail/<slug>/",views.WORKDAY.WorkDayDetailView.as_view(),name="v1-workday-detail"),
    path("day/<date>/fill-template/",views.WORKDAY.workdayFillTemplate,name="workdayFillTemplate"),
    path("day/<date>/add-pto/",views.WORKDAY.WorkdayPtoRequest.as_view(),name="workdayAddPTO"),
    path("day/<date>/run-swaps/", views.WORKDAY.runSwaps, name="run-swaps"),
    path("v2/workday-detail/<slug>/", views2.workdayDetail, name="v2-workday-detail"),
    path("v2/workday-detail/<slug>/<sft>/", viewsets.SlotViews.slotStreakView, name="v2-slot-detail"),
    path('v2/workday-detail/<str:wdSlg>/api/fill-slot/<shiftSlg>/<empId>/', WdApi.Post.fillSlotWithApi, name='api-fill-slot'),
    path('v2-beta/workday-detail/<slug>/detail/', viewsets.WdViews.wdayDetailBeta, name='beta-day'),
]

week_patterns = [
    # ? ==== Week ==== ?#
    path("week/<int:year>/<int:week>/", views.WEEK.WeekView.as_view(), name="week"),
    path("week/day-table-frag/<str:workday>/", views.WEEK.dayTableFragment, name="dayTableFragment"),
    path("week/<int:year>/<int:week>/unfilled-slots/", views.WEEK.WeeklyUnfilledSlotsView.as_view(), name="week-unfilled-slots"),
    path("week/<int:year>/<int:week>/fill-template/", views.WEEK.weekFillTemplates, name="weekFillTemplate"),
    path("week/<int:year>/<int:week>/solve/", views.WEEK.solve_week_slots, name="solve-week"),
    path("week/<int:year>/<int:week>/swap-bot/",views.WEEK.make_preference_swaps,name="make-swaps-week"),
    path("week/<int:year>/<int:week>/clear-low-score-slots/",views.WEEK.clearWeekSlots_LowPrefScoresOnly, name="week-clear-low-score-slots"),
    path("week/<int:year>/<int:week>/clear-slots-form/",views.WEEK.ClearWeekSlotsView.as_view(),name="clear-week-slots-form",),
    path("week/all-weeks/", views.WEEK.all_weeks_view, name="weeks-all"),
    path("week/weekly-hours/", views.WEEK.weeklyHoursView, name="weeks-weekly-hours"),
    path("week/<int:year>/<int:week>/table/", views.WEEK.weekHoursTable, name="weeks-table"),
    path("v2/week-detail/<int:week>/", views2.weekView, name="v2-week-detail"),
    path("v2/week/<int:week>/fill-templates/",views2.weekView__set_ssts,name="v2-week-fill-templates"),
    path("v2/week-detail/<int:week>/delete-all-slots/", views2.weekView__clear_slots, name="v2-week-clear-slots"),
    path("v2/current-week/", views2.currentWeek, name="v2-current-week"),
    path("v2/week-fillable-by-view/<int:weekId>/", viewsets.WeekViews.all_slots_fillable_by_view, name="week-fillable-by"),
    path('v2/week-hrs-empl-form/week/<int:weekpk>/empl/<str:emplpk>/', views2.weekView__employee_possible_slots, name='week-hrs-empl-form'),
    path('v2/week/next-week/<int:weekId>/', viewsets.WeekViews.nextWeek, name='next-week'),
    path('v2/week/prev-week/<int:weekId>/', viewsets.WeekViews.prevWeek, name='prev-week'),
    path('api/week/week-total-hours/<int:weekId>/employee/<str:empId>/', WeekApi.GET.employeeHours, name='api-week-empl-hours'),
]

pay_period_patterns = [
    # ? ==== Pay Period ==== ?#
    path("v2/period/<str:prdId>/", views2.PeriodViews.detailView, name="period-detail"),
    path("pay-period/<int:year>/<int:period>/fill-template/",views.PERIOD.periodFillTemplates,name="periodFillTemplate"),
    path("pay-period/<int:year>/<int:period>/preferences/",views.PERIOD.periodPrefBreakdown,name="prefs-pay-period"),
]

shift_patterns = [
    # ? ==== Shifts ==== ?#
    path("shifts/all/", views.SHIFT.ShiftListView.as_view(), name="shift-list"),
    path("shifts/all/overview/", views.SHIFT.shiftOverview, name="shift-overview"),
    path("v2/shift/<str:cls>/<str:name>/", views2.shiftDetailView, name="shift-detail"),
    path("shift/<str:name>/update/", views.SHIFT.ShiftUpdateView.as_view(), name="shift-update"),
    path("v2/shift/<str:cls>/<str:sft>/trained/update/", views.SHIFT.trainedShiftView, name="shift-training-update"),
    path("shifts/new/", views.SHIFT.ShiftCreateView.as_view(), name="shift-new"),
    path("shift/<str:shift>/upcoming/",views.SHIFT.shiftComingUpView,name="shift-coming-up",),
    path("shift-tallies/<str:shiftpk>/tallies/",views.SHIFT.shiftTalliesView,name="shift-tallies-view",),
    path("shift-templates/<int:sftId>/",views.SHIFT.shiftTemplateView,name="shift-template-view",),
    path("v2/shift-pref-scores/<sft>/",views.SHIFT.shiftPrefScores,name="shift-pref-scores"),
    path("v2/shift-sort-scores/<sft>/", viewsets.ShiftViews.sortPrefView, name='shift-sort-scores'),
    path('v2/shift/sst/<str:shiftId>/shift-sst/', viewsets.ShiftViews.sstFormView, name='shift-sst-form'),
    path('shift/<sft>/prefs/update/', views.SHIFT.shiftPrefUpdate, name='shift-prefs-update'),
    path('v2/shift/<cls>/<sft>/coverage/', viewsets.ShiftViews.coverageFormView, name='shift-coverage-form'),
    path('shifts/all/partial/summary/',viewsets.ShiftViews.fteSummaryView,name="shifts-all-total-hours",),
]

slot_patterns = [
    # ? ==== Slots ==== ?#
    path(
        "slot/sch-<int:sch>/<slug:date>/<str:shift>/",
        views.SLOT.slotView,
        name="slot-view",
    ),
    path(
        "day/<slug:date>/<str:shift>/new/ot-allowed/",
        views.SLOT.SlotCreateView_OtOveride.as_view(),
        name="slot-new-ot-override",
    ),
    path("day/<slug:date>/<str:shift>/add/post", views.slotAdd_post, name="slot-add-post"),  # type: ignore
    path(
        "day/<slug:date>/<str:employee>/resolve-pto-request/",
        views.WORKDAY.ResolvePtoRequestFormView.as_view(),
        name="resolve-pto-request",
    ),
    path(
        "day/<slug:date>/<str:shift>/resolve-turnaround/",
        views.SLOT.resolveTurnaroundSlot,
        name="resolve-turnaround-inside-day",
    ),
    path(
        "turnarounds/", 
        views.SLOT.SlotTurnaroundsListView.as_view(), name="turnarounds"
    ),
    path(
        "turnarounds/delete/",
        views.SLOT.deleteTurnaroundsView,
        name="turnarounds-delete",
    ),
    path("sst-by-day/", views.SST.sstDayView, name="sst-day-view"),
    path("v2/slot/slot-admin/<str:slotId>/",views.SLOT.slot_admin_detail_view,name="v2-slot-detail",
    ),
    path(
        "v2/slot/slot-clear-assignment/<str:slotId>/action/",
        viewsets.Actions.SlotActions.clear_employee,
        name="v2-clear-slot",
    ),
    path(
        "v2/slot/slot-fill-with-best/<str:slotId>/action/",
        viewsets.Actions.SlotActions.fill_with_best,
        name="slot-action-fill-with-best",
    ),
    path(
        "v2/schedule-time-pref-aware-fill/<int:pk>/",
        views.SCHEDULE.DO.fillSlotsWithPrefTime,name="sch-time-pref-fill",
    ),
    path('v2/slot/slot-streak-view/<int:slotId>/', viewsets.SlotViews.slotStreakView, name='slot-as-streak-view'),
    path('v2/slot/slot-clear-action/<int:slotId>/clear/', viewsets.SlotViews.slotClearActionView, name="slot-clear-action"),
    path('v2/slot/slot-check-emp-fillability/<str:slotId>/<str:empId>/', SlotApi.checkEmpFillability, name='checkEmpFillability'),
]

employee_patterns = [
    # ? ==== Employees ==== ?#
    path("employees/all/",  views.EMPLOYEE.EmployeeListView.as_view(), name="employee-list"),
    path("employees/cpht/",  views.EMPLOYEE.EmployeeListViewCpht.as_view(), name="cpht-list"),
    path("employees/rph/",  views.EMPLOYEE.EmployeeListViewRph.as_view(), name="rph-list"),
    path("employees/new-pharmacist/",  views.EMPLOYEE.PharmacistCreateView.as_view(), name="create-rph"),
    path("employees/new-technician/",  views.EMPLOYEE.TechnicianCreateView.as_view(), name="create-cpht"),
    path("employee/<str:empId>/",  views.EMPLOYEE.EmployeeDetailView.as_view(), name="empl"),
    path("employee/<str:empId>/set-image/",  views.EMPLOYEE.setEmployeeImage, name="set-employee-image"),
    path("employee/<str:empId>/shift-tallies/",  views.EMPLOYEE.EmployeeShiftTallyView.as_view(), name="employee-shift-tallies"),
    path("employee/<empl>/shift-tallies/data/", views.EMPLOYEE.empl_shift_tallies_csv, name="employee-shift-tallies-csv"),
    path("employee/<str:empId>/shift-preferences/",  views.EMPLOYEE.shift_preference_form_view, name="shift-preferences-form"),
    path("employee/<str:empId>/update/",  views.EMPLOYEE.EmployeeUpdateView.as_view(), name="employee-update"),
    path("employee/<str:empId>/ssts/",  views.EMPLOYEE.employeeSstsView, name="employee-edit-ssts"),
    path("employee/<str:nameA>/coworker/<str:nameB>/",  views.EMPLOYEE.coWorkerView, name="employee-coworker"),
    path("employee/<str:name>/coworker/",  views.EMPLOYEE.coWorkerSelectView, name="coworker-select"),
    path("employee/<str:nameA>/coworker/<str:nameB>/",  views.EMPLOYEE.coWorkerView, name="coworker" ),
    path("employee/<str:empId>/template-days-off/",  views.EMPLOYEE.employeeTemplatedDaysOffView, name="employee-tdos"),
    path("employee/<str:name>/template-days-off/match/",  views.EMPLOYEE.employeeMatchCoworkerTdosView, name="emp-match-tdos"),
    path("employee/<str:name>/pto-request/add/",  views.EMPLOYEE.EmployeeAddPtoView.as_view(), name="employee-add-pto"),
    path("employee/<str:name>/pto-request/add-range/",  views.EMPLOYEE.EmployeeAddPtoRangeView.as_view(), name="employee-add-pto-range"),
    path("employee/<str:name>/generate-schedule/",  views.EMPLOYEE.EmployeeScheduleFormView.as_view(), name="employee-schedule-form"),
    path("v2/employee/<empId>/generate-schedule/<sch>/",  views.EMPLOYEE.EmployeeScheduleView.as_view(), name="v2-employee-schedule"),
    path("day-off-breakdown/",  views.EMPLOYEE.tdoBreakdownView, name="day-off-breakdown"),
    path("evening-fractions/",  views.EMPLOYEE.eveningFractionView, name="pm-fractions"),
    path("employee/<str:name>/sort-shift-prefs/",  views.EMPLOYEE.sortShiftPreferences, name="employee-sortable",),
    path("v2/sort-shift-prefs/<str:slug>/",  views2.EmployeeSortShiftPreferences.as_view(),name="employee-sort-shift-prefs"),
    path("v2/employee/pto-form/<str:empl>/<int:year>/<int:num>/",  views.EMPLOYEE.EmployeePtoFormView.as_view(), name="employee-sortable-down"),
    path('v2/employee/choose-schedule/<empId>/',  views2.EmployeeChooseSchedule.as_view(), name="employee-choose-schedule"),
    path('v2/employee/choose-schedule/<empId>/<schId>/',  views2.schDetailSingleEmployeeView, name="empl-schedule-detail"),
    path('empl/shift-sort/<str:empId>/',  viewsets.EmpViews.empShiftSort, name="emp-shift-sort"),
    path('empl/shift-tallies/<empId>/',  viewsets.EmpViews.empShiftTallies, name="emp-shift-tallies"),
    
    #*__________EMPLOYEE API PATHS__________*
    path("api/match-tdo/<str:empPk>/preview/",  viewsets.EmpPartials.tdoPreview, name="emp-tdo-match-preview"),
    path("api/employee/<str:empPk>/checkPrevWd/<str:wdId>/",  viewsets.EmpPartials.workPrevDay, name="emp-check-prev-wd"),
    path("api/employee/<str:empPk>/checkNextWd/<str:wdId>/",  viewsets.EmpPartials.workNextDay, name="emp-check-next-wd"),
]

schedule_patterns = [   
    #*__________SCHEDULE DETAIL__________*
    path("v2/schedule/<str:schId>/", viewsets.SchViews.schDetail, name="v2-schedule-detail"),
    path("v2/generate-schedule/<int:year>/<int:n>/", views2.generate_schedule_view, name="v2-generate-schedule"),
    path("schedule/<int:year>-<int:number>-<str:version>/modal/<slug:workday>/<str:shift>/",views.SCHEDULE.scheduleSlotModalView, name="schedule-slot-modal"),
    path("schedule/current-schedule/", views2.currentSchedule, name="v2-current-schedule"),
    path("schedule/<int:year>/<int:sch>/solve/", views.SCHEDULE.solveScheduleLoader, name="schedule-print"),
    path("schedule/<int:year>/<str:slug>/", views.HTMX.scheduleActiveLoad, name="sch-active-loading"),
    path("schedule/<int:year>/<int:sch>/delete-all-slots/",views.SCHEDULE.scheduleDelSlots, name="sch-del-slots"),
    path("schedule/<int:year>/<int:sch>/solve-slots/",views.SCHEDULE.solveScheduleSlots,name="solve-sch-slots"),
    path("v2/schedule/generate-random-pto/<int:schpk>/",views.SCHEDULE.DO.generateRandomPtoRequest,name="gen-rand-pto"),
    path("schedule/<int:year>/<int:sch>/weekly-ot/",views.SCHEDULE.weeklyOTView,name="weekly-ot"),
    path("schedule/<int:year>/<int:sch>/del-pto-conflict-slots/",views.SCHEDULE.FX.removePtoConflictSlots,name="remove-pto-conflict-slots"),
    path('v2/schedule/<str:schId>/get-sch-empty-count/', viewsets.SchViews.getSchEmptyCount, name="get-sch-empty-count"),
    path("v2/schedule-as-empl-grid/<str:schId>/",views2.schDetailEmplGridView,name="v2-schedule-as-empl-grid"),
    path("v2/schedule-as-shift-grid/<str:schId>/",views2.schDetailShiftGridView, name='v2-schedule-as-shift-grid'),
    path("v2/schedule/<str:schId>/clearSlots/",views2.scheduleClearAllView, name="v2-schedule-clear"),
    path("v2/S<int:year>-<int:num><str:ver>/<str:day>/as-popover/",views2.schDayPopover, name="sch-day-popover"),
    path("v2/schedule-solve/<str:schId>/", views2.scheduleSolve, name="v2-schedule-solve" ),
    path("v2/schedule-solve-alg-2/<str:schId>/",views.SCHEDULE.solveScheduleSlots, name="v2-schedule-solve-alg2"),
    path('v2/schedule-detail/<str:schId>/empty-slots/', views2.schDetailAllEmptySlots, name='all-empty'),
    path("v2/lazy-popover-load/<str:schSlug>/<str:wdSlug>/",views.SCHEDULE.FX.lazy_popover_load, name="lazy-popover-load",),
    path("v2/generate-new-schedule/",views2.generate_schedule_form, name="generate-new-schedule",),
    path("v2/schedule-empl-pto/<str:schId>/<str:empl>/", views2.pto_schedule_form, name="v2-schedule-empl-pto"),
    path("v2/schedule/slot-table-view/<str:schId>/", views2.schDetailSlotTableView, name="sch-detail-slot-table"),
    path("v2/schedule/tdo-conflicts-table/<str:schId>/", viewsets.SchViews.schTdoConflictsView,name="sch-tdo"),
    path("v2/schedule/pto-conflicts/<str:schId>/", views2.schDetailPtoConflicts, name="sch-pto-conflicts"),
    path("v2/compare-schedules/<schId1>/<schId2>/", viewsets.SchViews.compareSchedules, name="compare-schedules"),
    path("v2/schedule/fte-percents/<str:schId>/", viewsets.SchViews.schFtePercents, name="sch-fte-percents"),
    path('api/schedule/emusr/<str:schId>/', viewsets.SchViews.schEMUSR, name='api-sch-emusr'),
    path('v2/schedule/<str:schId>/emusr/', viewsets.SchViews.schEMUSRView, name='sch-emusr'),
    path('v2/schedule/<str:schId>/get-emusr-distr/', viewsets.SchViews.Calc.emusr_distr, name='sch-emusr-distr'),
    path('v2/schedule/emusr/<str:schId>/employee/<str:empl>/', viewsets.SchViews.schEMUSRView, name='sch-emusr-empl'),
    path('v2/schedule/maintain/clearFteOverages/<str:schId>/', viewsets.SchViews.clearOverFteSchView, name='sch-clear-over-fte'),
    path('v2/schedule/maintain/syncDb/<str:schId>/', viewsets.SchViews.syncDbSchView, name='sch-sync-db'),
    path('create-menu/', viewsets.SchViews.newSchView, name='create-menu-sch'),
    
    #*__________SCHEDULE PARTIALS__________*
    path('schedule-partials/<schId>/complex-table/', viewsets.SchPartials.schComplexTablePartial, name='sch-partial-cx-table'),
    path('schedule-partials/<schId>/compare-and-select/', viewsets.SchPartials.schCompareSelectPartial, name='sch-partial-compare-select'),
    path('schedule-partials/<schId>/view-select/', viewsets.SchPartials.schViewSelectPartial, name='sch-partial-view-select'),
    path('schedule-partials/<schId>/empl-grid/', viewsets.SchPartials.schEmployeeGridPartial, name='sch-partial-empl-grid'),
    path('schedule-partials/<schId>/shift-grid/', viewsets.SchPartials.schShiftGridPartial, name='sch-partial-shift-grid'),
    path('schedule-partials/<schId>/fte-ratios/', viewsets.SchPartials.schFteRatioPartial, name='sch-partial-fte-ratios'),
    path('schedule-partials/<schId>/stat-bar/', viewsets.SchPartials.schStatBarPartial, name='sch-partial-stat-bar'),
    path('schedule-partials/<schId>/week-breakdown/', viewsets.SchPartials.schWeeklyBreakdownPartial, name='sch-week-brkd'),
    path('schedule-partials/<schId>/mistemplated/', viewsets.SchPartials.schMistemplatedPartial, name='sch-mistemplated'),
    
    path('schedule-calcs/<schId>/uf-distr/', viewsets.SchViews.Calc.uf_distr, name='sch-calc-uf-distr'),
    path('schedule-calcs/<schId>/n-empty/', viewsets.SchViews.Calc.n_empty, name='sch-calc-n-empty'),
    path('schedule-calcs/<schId>/n-mistemplated/', viewsets.SchViews.Calc.n_mistemplated, name="sch-n-mistemplated"),
    path('schedule-calcs/<schId>/all-calcs/', viewsets.SchViews.Calc.all_calcs, name="sch-all-calcs"),
]

test_patterns = [
    path("test/<slug:workday>/<str:shift>/", views.TEST.allOkIntraWeekSwaps, name="test" ),
    path(
        "test/<slug:workday>/<str:shift>/i-s/",
        views.TEST.possibleInterWeekSlotSwaps,
        name="test2",
    ),
    path(
        "test/<slug:slotA>/<slug:slotB>/make-swap/",
        views.TEST.makeSwap,
        name="InterWeek Swap",
    ),
    path("spinner/", views.TEST.spinner, name="spinner"),
    path(
        "predict-streak/<str:employee>/<slug:workday>/",
        actions.PredictBot.predict_createdStreak,
        name="predict-streak",
    ),
    path("api/workday/n-days-away/<str:wdaySlg>/", api.get_n_days_away, name="n-days-away")
]

htmx_patterns = [
    path("htmx/alert/<str:title>/<str:msg>/", views.HTMX.alertView, name="htmxAlert"),
    path("htmx/spinner/", views.HTMX.spinner, name="spinner-view"),
    path("htmx/prog/<int:progress>/", views.HTMX.radProgress, name="radial-progress"),
    path("v2/employee/rank-shift-preferences/<str:empl>/",views.HTMX.rank_shift_prefs, name="rank-shift-prefs"),
    path("htmx/form/cphtShift-choices/", views.HTMX.cphtShiftChoices, name="cpht-shift-choices"),
]

hyperPatterns = [
    path("hyper/hilight/", views.HYPER.hilight, name="hyperscript-hilight"),
    path("testing/layout/", views2.mytest, name="test-layout"),
]

pto_patterns = [
    path('pto/pto-request-instance/<int:pk>/', views.PTO.ptoRequestDetailView, name='pto-request-detail'),
    path('pto/pto-request-instance/<int:pk>/delete/', views.PTO.ptoRequestDetailView__delete, name='pto-request-delete'),
]

urlpatterns += user_patterns
urlpatterns += workday_patterns
urlpatterns += week_patterns
urlpatterns += pay_period_patterns
urlpatterns += shift_patterns
urlpatterns += slot_patterns
urlpatterns += employee_patterns
urlpatterns += schedule_patterns
urlpatterns += test_patterns
urlpatterns += htmx_patterns
urlpatterns += hyperPatterns
urlpatterns += pto_patterns
