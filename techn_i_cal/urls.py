from django.contrib import admin
from django.urls import include, path, reverse
from django.template import loader
from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect
from django.conf import settings
from django.conf.urls.static import static
from sch.models import Shift, Slot, Employee, Workday
from rest_framework import routers, serializers, viewsets

import datetime as dt
from django_require_login.decorators import  public
from django.contrib.auth.models import User

from .forms import LoginForm

from django.contrib import messages
from django.contrib.auth import login, authenticate, logout

import logging

"""__________________________________________________________________

    +=================================+
    | ROOT URLS FOR 'FLOWRATE' WEBAPP |
    +=================================+
    
    _________________________________________________________________
"""

__author__ = "JOSH STEINBECKER"




@public
def index(request):
    template = loader.get_template('index.pug')

    if request.method == "POST":
        print("post")
        if request.POST.get("token"):
            token_field = request.POST.get("token")
            print(token_field)
            return HttpResponseRedirect(reverse('index'))
    context = {}
    return HttpResponse(template.render(context, request))

@public
def mail (request):
    return render(request, 'mail.html', {'slots': Slot.objects.all()})
    
@public
def loginView (request):
    template = loader.get_template('sch/login.html')

    if request.method == "POST":
        if request.POST.get("username"): 
            logging 
            username = request.POST.get("username")
            password = request.POST.get("password")
            user     = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                return HttpResponseRedirect(reverse('index'))
            else:
                return HttpResponseRedirect(reverse('login'))

    # make Login form with attr: autocapitalize="none" autocomplete="off"
    form = LoginForm(auto_id=False)
    context = {
        'form': form
    }
    return HttpResponse(template.render(context, request))

@public
def logoutView (request):
    user = request.user
    logout(request)
    return HttpResponseRedirect(reverse('index'))



urlpatterns = [
    path('' ,           index,                    name='index'),
    path('login/',      loginView,                name='login-view'),
    path('logout/',     logoutView,               name='logout-view'),
    path('accounts/',   include('django.contrib.auth.urls')),
    path('grappelli/',  include('grappelli.urls')),
    path('admin/doc/',  include('django.contrib.admindocs.urls')),
    path('admin/',      admin.site.urls,          name='admin'),
    path('empl/',       include('empl.urls'),     name='empl'),
    path('sch/',        include('sch.urls'),      name='sch'),
    path('schedule/',   include('schedule.urls'), name='schedule'),
    path('wday/',       include('wday.urls'),     name='wday'),
    path('prd/',        include('prd.urls'),      name="prd"),
    path('pds/',        include('pds.urls'),      name="pds"),
    path('api/',        include('flow.urls'),     name='flow'),
    path('mail/',       mail,                     name='mail'),

] + static ( settings.STATIC_URL,  document_root = settings.STATIC_ROOT )

