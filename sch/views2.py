from django.shortcuts import render, HttpResponse, HttpResponseRedirect
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Count
from django.urls import reverse_lazy
from django.views.generic.detail import DetailView
from django.views.generic.list import ListView
from django.views.generic.edit import UpdateView, DeleteView, FormView
from django.forms import formset_factory
from django.contrib import messages, admin
from django.contrib.auth.forms import UserCreationForm 
from django.http import JsonResponse


from .models import *
from .xviews.week import *
from .forms import *
from .formsets import *
from .actions import *
from .tables import *
from django.db.models import Q, F, Sum, Subquery, OuterRef, Count
from django_tables2 import RequestConfig
import datetime as dt

#-------------------------#
#### LIST OF SCHEDULES ####
#-------------------------#
def schListView (request):
    schedules = Schedule.objects.all()
    context = {
        'schedules': schedules
    }
    return render(request, 'sch2/schedule/sch-list.html', context)

def schDetailView (request, year, num, ver):
    
    schedule = Schedule.objects.get(year=year, number=num, version=ver)
    
    context = {
        'schedule': schedule,
    }
    return render(request, 'sch2/schedule/sch-detail.html', context)

def schDayPopover (request, dayid):
    workday = Workday.objects.get(pk=dayid)
    schedule = workday.schedule
    slots = workday.slots.all()
    
    context = {
        'workday' : workday,
    }
    return render(request, 'sch2/schedule/sch-day-popover2.html', context)    

def schActionSolveSlots (request, sched):
    schedule = Schedule.objects.get(pk=sched)
    schedule.setSsts()
    schedule.fillSlots()
    if schedule.slots.empty().count() > 30:
        schedule.fillSlots()
    return HttpResponseRedirect(schedule.url())

def weekListView (request):
    weeks = Week.objects.all()
    context = {
        'weeks': weeks,
    }
    return render(request, 'sch2/week/wk-list.html', context)

def weekView (request, sch, prd, wk):
    week = Week.objects.filter(schedule__slug=sch, number=wk).first()
    week.save()
    context = {
        'week'  : week,
        'workdays': week.workdays.all(),
    }
    return render(request, 'sch2/week/wk-detail.html', context)


def weekView__set_ssts (request, weekid):
    """
    If SST exists and filling employee is appropriate, Slot is filled.
    Exceptions that will result in no change:
        - empl has ptoreq
        - empl would go overtime 
        - empl in conflicting slot
    """
    
    log = []
    
    week = Week.objects.get(pk=weekid)
    for slot in week.slots.all():
        msg = slot.set_sst()
        slot.save()
        log += [msg]
    print(log)
    return HttpResponseRedirect (week.url())

def dayView (request, sch, prd, wk, day):
    """
    DAY DETAIL VIEW
    """
    workday = Workday.objects.get(schedule__slug=sch, slug=day)
    context = {
        'wd' : workday,
    }
    return render(request, 'sch/workday/workday_detail.html', context)