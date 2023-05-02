from .models import *
from django.urls import path
from django.shortcuts import render
import datetime as dt
from .views import *



def index(request):
      profile        = Profile.objects.get(user=request.user)
      organization   = profile.organization
      return render(request, 'pages/index.pug', {'organization': organization})


urlpatterns = [

      path('', index, name='index'),
      path('schedules/', ScheduleViews.dept_schedules_list, name='sch-list'),
      path('schedules/<dept>/<yr>/<n>/', ScheduleViews.sch_detail, name='sch-detail'),
      path('schedules/<dept>/<yr>/<n>/v<v>/', VersionViews.ver_detail, name='ver-detail'),

      path('schedules/<dept>/<yr>/<n>/v<v>/<wd>/<s>/', SlotViews.slot_detail, name='slt-detail'),

      path('employee/', EmployeeViews.emp_list, name='emp-list'),
      path('employee/<pk>/', EmployeeViews.shift_pref_view, name='emp-shift-pref'),
]


urlpatterns += [
      path('schedules/<dept>/<yr>/<n>/v<v>/solve/', VersionViews.ver_solve, name='ver-solve'),
      path('schedules/<dept>/<yr>/<n>/v<v>/clear/', VersionViews.ver_clear, name='ver-clear'),
      path('schedules/<dept>/<yr>/<n>/v<v>/delete/', VersionViews.ver_delete, name='ver-delete'),
]