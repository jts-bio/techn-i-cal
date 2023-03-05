from django.urls import path, include
from .views import ApiViews, ApiActionViews
from sch.viewsets import SchViews


app_name = 'flow'

schedule_urls = [
    path('<schId>/n-empty/', ApiViews.schedule__get_n_empty, name='sch__get_n_empty'),
    path('<schId>/empty-list/', ApiViews.schedule__get_empty_list, name='sch__get_empty_list'),
    path('<schId>/weekly-hours/', ApiViews.schedule__get_weekly_hours, name='sch__get_weekly_hours'),
    path('<schId>/emusr/', ApiViews.schedule__get_emusr_range, name='sch__get_emusr'),
    path('<schId>/emusr-stdev/', SchViews.Calc.uf_distr, name='sch__get_emusr_stdev'),
    path('<schId>/percent/', ApiViews.schedule__get_percent, name='sch__get_percent'),
    path('<schId>/n-pto-conflicts/', ApiViews.schedule__get_n_pto_conflicts, name='sch__get_n_pto_conflicts'), 
    path('<schId>/n-mistemplated/', ApiViews.schedule__get_n_mistemplated, name='sch__get_n_mistemplated'),
    path('<schId>/mistemplated-list/', ApiViews.schedule__get_mistemplated_list, name='mistemplated'),
    path('<schId>/n-unfavorables/', ApiViews.schedule__get_n_unfavorables, name='sch__get_n_unfavorables'),
    path('<schId>/n-untrained/', ApiViews.schedule__get_n_untrained, name='sch__get_n_untrained'),
    path('<schId>/untrained-list/', ApiViews.schedule__get_untrained_list, name='sch__get_untrained_list'),
    path('<schId>/n-turnarounds/', ApiViews.schedule__get_n_turnarounds, name='sch__get_n_turnarounds'),
    path('<schId>/fill-by-period/', ApiActionViews.payPeriodFiller, name='sch__fill_by_period'),
    path('<schId>/week-excess/<empId>/<wk>/', ApiViews.schedule__employee_excess_week_hours, name='sch__get_week_excess'),
    
]

shift_urls = [
    path('<shiftName>/actions/set-img/', ApiActionViews.set__shift_img, name='shift__set_img'),
]

pto_urls = [
    path('<day>/<emp>/actions/delete/', ApiActionViews.ptoreq__delete, name='del-ptoreq'),
    path('<day>/<emp>/actions/create/', ApiActionViews.ptoreq__create, name='create-ptoreq'),
]

emp_urls = [
    path('<empId>/week-hours/<sch>/<wd>/', ApiViews.employee__week_hours, name='week-hours'),
    path('<empId>/period-hours/<sch>/<wd>/', ApiViews.employee__period_hours, name='period-hours'),
]

urlpatterns = [
    path('build-schedule/<int:year>/<int:num>/<version>/', ApiActionViews.build_dict, name='build-schedule'),
    path('schedule/', include(schedule_urls)),
    path('shift/',    include(shift_urls)),
    path('ptoreq/',   include(pto_urls)),
    path('employee/', include(emp_urls)),
]


