from .models import *
from django.urls import path
from django.shortcuts import render

from .views import *
from django.http import HttpResponse, HttpResponseRedirect
from django.contrib.auth import authenticate, login
from django.views import View

import datetime as dt






def index(request):
      if not request.user.is_authenticated:
            return HttpResponseRedirect('/login/')
      profile        = Profile.objects.get(user=request.user)
      organization   = profile.organization
      return render(request, 'pages/index.pug', {'organization': organization})


class LoginView(View):
      
      template_name = 'pages/login.pug'
      
      def get (self, request):
            return render(request, 'pages/login.html')
      
      def post (self, request):
            username = request.POST.get('username')
            password = request.POST.get('password')
            user = authenticate(request, username=username, password=password)
            if user is not None:
                  if user.is_active:
                        login(request, user)
                        return HttpResponseRedirect('/schedules/')
            else:
                  return render(request, 'pages/login.html', {'error': 'Invalid username or password'})


urlpatterns = [

      path('', index, name='index'),
      path('login/', LoginView.as_view(), name='login'),
       
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