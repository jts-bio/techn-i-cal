from django.urls import path, include
from django.contrib import admin
from . import views




urlpatterns = [
    
    path('letters/',views.PREPMODE.letterView , name="letter-list"),
        
    
]