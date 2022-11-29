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
from django.urls import include, path
from django.template import loader
from django.shortcuts import render
from django.http import HttpResponse
from django.conf import settings
from django.conf.urls.static import static
from sch2.models import Shift, Slot, Employee, Workday
from rest_framework import routers, serializers, viewsets

from flow.views import *

def index(request=0):
    template = loader.get_template('index.html')
    context = {
    }
    return HttpResponse(template.render(context, request))

urlpatterns = [
    path('' ,           index,  name='index'),
    path('admin/doc/',  include('django.contrib.admindocs.urls')),
    path('admin/',      admin.site.urls ),
    path('sch2/',        include('sch2.urls'),    name='sch2'),
    path('pds/',        include('pds.urls'),    name="pds"),
    path('flow/',       include('flow.urls'),   name='flow'),
    
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

