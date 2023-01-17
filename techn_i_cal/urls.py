"""pkpr URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""


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




@public
def index(request):
    template = loader.get_template('index.html')

    if request.method == "POST":
        print("post")
        if request.POST.get("token"):
            token_field = request.POST.get("token")
            print(token_field)
            return HttpResponseRedirect(reverse('index'))
        
    
    context = {
    }
    return HttpResponse(template.render(context, request))

@public
def loginView (request):
    template = loader.get_template('sch/login.html')

    if request.method == "POST":
        print("post")
        if request.POST.get("username"): 
            username = request.POST.get("username")
            password = request.POST.get("password")

            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                return HttpResponseRedirect(reverse('index'))
            else:
                return HttpResponseRedirect(reverse('login'))

    form = LoginForm()
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
    path('' ,           index,          name='index'),
    path('__debug__/', include('debug_toolbar.urls')),
    path('login/',      loginView,      name='login-view'),
    path('logout/',     logoutView,     name='logout-view'),
    path('accounts/',   include        ('django.contrib.auth.urls')),
    path('grappelli/',  include        ('grappelli.urls')),
    path('admin/doc/',  include        ('django.contrib.admindocs.urls')),
    path('admin/',      admin.site.urls,        name='admin'),
    path('sch/',        include('sch.urls'),    name='sch'),
    path('wday/',       include('wday.urls'),   name='wday'),
    path('pds/',        include('pds.urls'),    name="pds"),
    path('flow/',       include('flow.urls'),   name='flow'),

] + static( settings.STATIC_URL,  document_root=settings.STATIC_ROOT )

