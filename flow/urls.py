from django.urls import path, include
from .views import ApiViews, ApiActionViews
from sch.viewsets import SchViews


app_name = 'flow'

schedule_urls = [
    path('<schId>/n-empty/', ApiViews.schedule__get_n_empty, name='sch__get_n_empty'),
    path('<schId>/weekly-hours/', ApiViews.schedule__get_weekly_hours, name='sch__get_weekly_hours'),
    path('<schId>/emusr/', ApiViews.schedule__get_emusr, name='sch__get_emusr'),
    path('<schId>/emusr-stdev/', SchViews.Calc.uf_distr, name='sch__get_emusr_stdev'),
    path('<schId>/percent/', ApiViews.schedule__get_percent, name='sch__get_percent'),
    path('<schId>/n-pto-conflicts/', ApiViews.schedule__get_n_pto_conflicts, name='sch__get_n_pto_conflicts'), 
    path('<schId>/n-mistemplated/', ApiViews.schedule__get_n_mistemplated, name='sch__get_n_mistemplated'),
    path('<schId>/mistemplated-list/', ApiViews.schedule__get_mistemplated_list, name='mistemplated'),
    path('<schId>/n-unfavorables/', ApiViews.schedule__get_n_unfavorables, name='sch__get_n_unfavorables'),
    
]

shift_urls = [
    path('<shiftName>/actions/set-img/', ApiActionViews.set__shift_img, name='shift__set_img'),
]

urlpatterns = [
    path('schedule/', include(schedule_urls)),
    path('shift/', include(shift_urls)),
]


