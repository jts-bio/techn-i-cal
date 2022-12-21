from django.urls import path
from .views import *


app_name = 'flow'

urlpatterns = [
    path('api/schedule/weekly-hours/employee/<str:schId>/<str:empName>/', 
         Api.schedule__get_weekly_hours__employee, name='schedule__get_weekly_hours__employee')
]
