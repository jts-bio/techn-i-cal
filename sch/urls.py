from django.urls import path, include
from django.contrib import admin
from . import views, actions, views2


urlpatterns = [
    path('', views.index, name='index'),
    #? ==== PTO Requests ==== ?#
    path('pto-requests/all/', views.PTO.PtoManagerView.as_view(), name='pto-request-list'),
    #? ==== DOCS ==== ?#
    path('docs/week/', views.DOCUMENTATION.weekly, name='docs-week'),  
]

user_patterns = [
    path('user/register/',
         views.registerView,        name='user-register-form'),
    path('user/login/', 
         views.registerView,        name='user-login-form')
]
urlpatterns += user_patterns

workday_patterns = [
    #? ==== Workday ==== ?#
    path('day/all/', views.WORKDAY.WorkdayListView.as_view(), name='workday-list'),
    path('day/<int:schid>/<slug:slug>/', views.WORKDAY.WorkDayDetailView.as_view(), name='workday'),
    path('day/<slug:date>/fill-template/', views.workdayFillTemplate, name='workdayFillTemplate'),
    path('day/<slug:date>/add-pto/', views.WORKDAY.WorkdayPtoRequest.as_view(), name='workdayAddPTO'),
    path('days/new/', views.WORKDAY.WorkdayBulkCreateView.as_view(), name='workday-new'),
    path('day/<slug:date>/run-swaps/', views.WORKDAY.runSwaps, name='run-swaps'),
]
urlpatterns += workday_patterns

week_patterns = [
    #? ==== Week ==== ?#
    path('week/<int:year>/<int:week>/', views.WEEK.WeekView.as_view(), name='week'),
    path('week/day-table-frag/<str:workday>/', views.WEEK.dayTableFragment, name='dayTableFragment'),
    path('week/<int:year>/<int:week>/unfilled-slots/', views.WEEK.WeeklyUnfilledSlotsView.as_view(), name='week-unfilled-slots'),
    path('week/<int:year>/<int:week>/fill-template/', views.WEEK.weekFillTemplates, name='weekFillTemplate'),
    path('week/<int:year>/<int:week>/solve/', views.WEEK.solve_week_slots, name='solve-week'),
    path('week/<int:year>/<int:week>/swap-bot/', views.WEEK.make_preference_swaps, name="make-swaps-week"),
    path('week/<int:year>/<int:week>/clear-low-score-slots/', views.WEEK.clearWeekSlots_LowPrefScoresOnly, name='week-clear-low-score-slots'),
    path('week/<int:year>/<int:week>/clear-slots-form/', views.WEEK.ClearWeekSlotsView.as_view(), name='clear-week-slots-form'),
    path('week/all-weeks/', views.WEEK.all_weeks_view, name='weeks-all'),
    path('week/weekly-hours/', views.WEEK.weeklyHoursView, name='weeks-weekly-hours'),
    path('week/<int:year>/<int:week>/table/', views.WEEK.weekHoursTable, name='weeks-table'),
    path('week/<int:year>/<int:iweek>/get-empty-slots/', views.WEEK.GET.solvableUnfilledWeekSlots, name='get-empty-slots'),
    
    path('<int:schid>/week/<int:week>/', views2.weekView, name='xweek'),
    path('<int:schid>/week/<int:week>/fill-templates/', views2.weekView__set_ssts, name='xweekFillTemplate'),
]
urlpatterns += week_patterns

pay_period_patterns = [
    #? ==== Pay Period ==== ?#
    path('pay-period/<int:year>/<int:period>/', views.PERIOD.period_view, name='pay-period'),
    path('pay-period/<int:year>/<int:period>/fill-template/', views.PERIOD.periodFillTemplates, name='periodFillTemplate'),
    path('pay-period/<int:year>/<int:period>/preferences/', views.PERIOD.periodPrefBreakdown, name='prefs-pay-period'),
]
urlpatterns += pay_period_patterns

shift_patterns = [
    
    #? ==== Shifts ==== ?#
    path('shifts/all/', views.SHIFT.ShiftListView.as_view(), name='shift-list'),
    path('shifts/all/overview/', views.SHIFT.shiftOverview, name='shift-overview'),
    path('shift/<str:name>/', views.SHIFT.ShiftDetailView.as_view() , name='shift'),
    path('shift/<str:name>/update/', views.SHIFT.ShiftUpdateView.as_view(), name='shift-update'),
    path('shift/<str:name>/trained/update', views.SHIFT.trainedShiftView,name='shift-trained-update'), 
    path('shifts/new/', views.SHIFT.ShiftCreateView.as_view(), name='shift-new'),
    path('shift/<str:shift>/template/', views.shiftTemplate, name='shift-template'),
    path('shift/<str:shift>/upcoming/',views.SHIFT.shiftComingUpView, name='shift-coming-up'),
    path('shift/<str:name>/tallies/', views.SHIFT.shiftTalliesView , name='shift-tallies-view'),
]
urlpatterns += shift_patterns

slot_patterns = [
    
    #? ==== Slots ==== ?#
    path('slot/sch-<int:sch>/<slug:date>/<str:shift>/', views.SLOT.slotView, name='slot-view'),
    path('day/<slug:date>/<str:shift>/new/ot-allowed/', views.SLOT.SlotCreateView_OtOveride.as_view(), name='slot-new-ot-override'),
    path('day/<slug:date>/<str:shift>/add/post', views.slotAdd_post, name='slot-add-post'),  # type: ignore
    path('day/<slug:date>/<str:shift>/delete/', views.SLOT.SlotDeleteView.as_view(), name='slot-delete'),
    path('day/<slug:date>/<str:employee>/resolve-pto-request/', views.WORKDAY.ResolvePtoRequestFormView.as_view(), name='resolve-pto-request'),
    path('day/<slug:date>/<str:shift>/resolve-turnaround/',views.SLOT.resolveTurnaroundSlot, name='resolve-turnaround-inside-day' ),
    path('turnarounds/', views.SLOT.SlotTurnaroundsListView.as_view(), name='turnarounds'),
    path('turnarounds/delete/', views.SLOT.deleteTurnaroundsView, name='turnarounds-delete'),
    path('sst-by-day/', views.SST.sstDayView, name="sst-day-view"),
    
]
urlpatterns += slot_patterns

employee_patterns = [
    
    #? ==== Employees ==== ?#
    path("employees/all/", views.EMPLOYEE.EmployeeListView.as_view(), name='employee-list'),
    path("employees/cpht/", views.EMPLOYEE.EmployeeListViewCpht.as_view(), name='cpht-list'),
    path("employees/rph/", views.EMPLOYEE.EmployeeListViewRph.as_view(), name='rph-list'),
    path("employees/new/", views.EMPLOYEE.EmployeeCreateView.as_view(), name='employee-new'),
    path('employee/<str:name>/', views.EMPLOYEE.EmployeeDetailView.as_view(), name='employee-detail'),
    path('employee/<str:name>/shift-tallies/', views.EMPLOYEE.EmployeeShiftTallyView.as_view(), name='employee-shift-tallies'),
    path('employee/<str:name>/shift-preferences/', views.EMPLOYEE.shift_preference_form_view, name='shift-preferences-form'),
    path('employee/<str:name>/update/', views.EMPLOYEE.EmployeeUpdateView.as_view(), name='employee-update'),
    path('employee/<str:name>/ssts/', views.EMPLOYEE.employeeSstsView, name='employee-edit-ssts'),   
    path('employee/<str:nameA>/coworker/<str:nameB>/', views.EMPLOYEE.coWorkerView, name='employee-coworker'),
    path('employee/<str:name>/coworker/', views.EMPLOYEE.coWorkerSelectView, name='coworker-select'),
    path('employee/<str:nameA>/coworker/<str:nameB>/', views.EMPLOYEE.coWorkerView, name='coworker'),
    path('employee/<str:name>/template-days-off/', views.EMPLOYEE.employeeTemplatedDaysOffView, name='employee-tdos'),
    path('employee/<str:name>/template-days-off/match/', views.EMPLOYEE.employeeMatchCoworkerTdosView, name='employee-days-off'),
    path('employee/<str:name>/pto-request/add/', views.EMPLOYEE.EmployeeAddPtoView.as_view(), name='employee-add-pto'),
    path('employee/<str:name>/pto-request/add-range/', views.EMPLOYEE.EmployeeAddPtoRangeView.as_view(), name='employee-add-pto-range'),
    path('employee/<str:name>/generate-schedule/', views.EMPLOYEE.EmployeeScheduleFormView.as_view(), name='employee-schedule-form'),
    path('employee/<str:name>/generate-schedule/<slug:date_from>/<slug:date_to>/', views.EMPLOYEE.EmployeeScheduleView.as_view(), name='employee-schedule'),
    path('day-off-breakdown/', views.EMPLOYEE.tdoBreakdownView, name='day-off-breakdown'),
    path('evening-fractions/', views.EMPLOYEE.eveningFractionView,name='pm-fractions'),
    
    path('employee/<str:name>/sort-shift-prefs/', views.EMPLOYEE.sortShiftPreferences, name='employee-shifts'),
    
]
urlpatterns += employee_patterns

schedule_patterns = [
    #? ==== SCHEDULE ==== ?#
    path('schedule/all/',
         views.SCHEDULE.scheduleListView,           name='schedule-list'),
    path('schedule/<int:year>-<int:number>/',
         views.SCHEDULE.scheduleDetailView,         name='schedule-detail'),
    path('schedule/<int:year>-<int:number>-<str:version>/modal/<slug:workday>/<str:shift>/',
         views.SCHEDULE.scheduleSlotModalView,      name='schedule-slot-modal'),
    path('schedule/current-schedule/', 
         views.SCHEDULE.currentScheduleView,        name='current-schedule'),
    path('schedule/<int:year>/<int:sch>/', 
         views.SCHEDULE.scheduleView,               name='schedule'),
    path('schedule/<int:year>/<int:sch>/solve/', 
         views.SCHEDULE.solveScheduleLoader,        name='schedule-print'),
    path('schedule/<int:year>/<int:sch>/start/',
         views.HTMX.scheduleActiveLoad,             name='sch-active-loading'),
    path('schedule/<int:year>/<int:sch>/delete-all-slots/', 
        views.SCHEDULE.scheduleDelSlots,            name='sch-del-slots'),
    path('schedule/<int:year>/<int:sch>/solve-slots/', 
        views.SCHEDULE.solveScheduleSlots,          name='solve-sch-slots'),  
    path('schedule/<int:year>/<int:sch>/generate-random-pto/',
        views.SCHEDULE.DO.generateRandomPtoRequest, name='random-employee-pto'),
    path('schedule/<int:year>/<int:sch>/weekly-ot/', 
        views.SCHEDULE.weeklyOTView,                name='weekly-ot'),
    path('schedule/<int:year>/<int:sch>/del-pto-conflict-slots/', 
        views.SCHEDULE.FX.removePtoConflictSlots,   name='remove-pto-conflict-slots'),
    
    path('v2/schedule/list/', 
         views2.schListView,                       name='sch-list'),
    path('v2/S<int:year>-<int:num><str:ver>/',
         views2.schDetailView,                     name='sch'),
    path('v2/S<int:year>-<int:num><str:ver>/<str:day>/as-popover/',
         views2.schDayPopover, name="sch-day-popover"),
]
urlpatterns += schedule_patterns

test_patterns = [
    path('test/<slug:workday>/<str:shift>/',
         views.TEST.allOkIntraWeekSwaps,            name="test1"),
    path('test/<slug:workday>/<str:shift>/i-s/',
        views.TEST.possibleInterWeekSlotSwaps,      name="test2"),
    path('test/<slug:slotA>/<slug:slotB>/make-swap/',
        views.TEST.makeSwap,                        name="InterWeek Swap"),
    path('spinner/',
        views.TEST.spinner,                         name="spinner"),
    path('predict-streak/<str:employee>/<slug:workday>/', 
        actions.PredictBot.predict_createdStreak,   name="predict-streak"),
]
urlpatterns += test_patterns

htmx_patterns = [
    path('htmx/alert/<str:title>/<str:msg>/', 
         views.HTMX.alertView ,         name="htmxAlert"),
    path('htmx/spinner/', 
         views.HTMX.spinner,            name='spinner-view'),
    path('htmx/prog/<int:progress>/', 
         views.HTMX.radProgress ,       name= 'radial-progress'),
    path('htmx/form/rphShift-choices/', 
         views.HTMX.rphShiftChoices,    name = "rph-shift-choices"),
    path('htmx/form/cphtShift-choices/', 
         views.HTMX.cphtShiftChoices,   name = "cpht-shift-choices"),
]
urlpatterns += htmx_patterns

hyperPatterns = [
    path('hyper/hilight/',
         views.HYPER.hilight , name='hyperscript-hilight',)
    
]
urlpatterns += hyperPatterns
