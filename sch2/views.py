from django.shortcuts import render
from django.urls import path
from sch2.models import *
import datetime as dt
# Create your views here.



def index (request) :
    
    html_template = 'sch2/index.html'
    
    wd = Workday.objects.filter(date=dt.date.today()).first()
    
    currentSchedule = wd.schedule
    url_employees   = '/sch/employees/'
    url_shifts      = '/sch/shifts/'
    context = {
        'currentSchedule'   : currentSchedule,
        'urlEmployees'      : url_employees,
        'urlShifts'         : url_shifts,
    }
    return render (request, html_template, context)