from django.urls import path, include
from django.contrib import admin
from . import views


urlpatterns = [
    
            path(route='', view= views.index,  name= "index"),
    
        ]
