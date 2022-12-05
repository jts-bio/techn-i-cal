from django.urls import path
from .views import *


app_name = 'flow'

urlpatterns = [
    path ('v2/sort-shift-prefs/<str:slug>/', EmployeeSortShiftPreferences.as_view(), name='employee-sort-shift-prefs'),
]
