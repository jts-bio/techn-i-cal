from django.urls import path, include
from django.contrib import admin
from . import views


week_urls = [ 
             path('week/<slug:week>/view/', 
                  views.weekView, name='week-detail'),
             path('week/<slug:week>/view/set-ssts/',
                  views.weekView__set_ssts, name='week-set-ssts'),
        ]


urlpatterns = []