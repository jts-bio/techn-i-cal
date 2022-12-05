from django.shortcuts import render, HttpResponse, HttpResponseRedirect
from django.views.decorators.csrf import csrf_exempt
from django.core.serializers import serialize
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

def schDetailView (request, pk ):
    
    schedule = Schedule.objects.get(pk=pk)
    
    context = {
        'schedule' :  schedule,
    }
    return render(request, 'sch2/schedule/sch-detail.html', context)

def schDayPopover (request, year, num, ver, day):
    schedule = Schedule.objects.get(year=year, number=num, version=ver)
    workday = schedule.workdays.get(day=day)
    
    context = {
        'workday' : workday,
    }
    return render(request, 'sch2/schedule/sch-day-popover2.html', context)    

def weekView (request, week):
    week = Week.objects.filter(pk=week).first()
    week.save()
    context = {
        'week'  : week,
        'slots' : week.slots.filled().order_by('employee__name'),
        'workdays': week.workdays.all(),
    }
    return render(request, 'sch2/week/wk-detail.html', context)

def weekView__set_ssts (request, week):
    """
    If SST exists and filling employee is appropriate, Slot is filled.
    Exceptions that will result in no change:
        - empl has ptoreq
        - empl would go overtime 
        - empl in conflicting slot
    """
    if request.method == "POST":
        week = Week.objects.filter(pk=week).first()
        for day in week.workdays.all():
            for slot in day.slots.all():
                slot.set_sst()
        return HttpResponseRedirect(week.url())

def weekView__clear_slots (request, week):
    if request.method == "POST":
        week = Week.objects.filter(pk=week).first()
        week.slots.filled().update(employee=None)
    return HttpResponseRedirect(week.url())

def workdayDetail (request, slug):
    
    html_template = 'sch2/workday/wd-detail.html'
    workday = Workday.objects.get(slug=slug)
    
    context = {
        'workday': workday,
    }
    return render(request, html_template, context)

def shiftDetailView (request, cls, name):
    html_template = 'sch2/shift/shift-detail.html'
    
    shift = Shift.objects.get(cls=cls,name=name)
    _= [int(sft) for sft in shift.occur_days]
    days = ",".join(["SMTWRFS"[d] for d in _])
    
    context = {
        'shift' :shift,
        'days'  : days,
    }
    return render(request, html_template, context)

def shiftTrainingFormView (request, cls, sft):
    
    shift = Shift.objects.get (cls=cls, pk=sft)
    if request.method == 'POST':
        # if there is a dict key in the form of 'employee-trained' and it to the list trained:
        trained = []
        for i in request.POST:
            tagless = i[:-8]
            if i.replace("-trained","") == tagless:
                e = Employee.objects.get(slug=tagless)
                trained.append(e)
        available = []
        for i in request.POST:
            tagless = i[:-10]
            if i.replace("-available","") == tagless:
                e = Employee.objects.get(slug=tagless)
                available.append(e)
        for employee in Employee.objects.all():
            if employee in trained:
                if shift not in employee.shifts_trained.all():
                    employee.shifts_trained.add(shift)
            if employee not in trained:
                if shift in employee.shifts_trained.all():
                    employee.shifts_trained.remove(shift)
            if employee in available:
                if shift not in employee.shifts_available.all():
                    employee.shifts_available.add(shift)
            if employee not in available:
                if shift in employee.shifts_available.all():
                    employee.shifts_available.remove(shift)
        return HttpResponseRedirect (shift.url())
     
    html_template = 'sch2/shift/shift-training.html'
    empls = Employee.objects.filter(cls=shift.cls).order_by('name')
    context = {
        'shift': shift,
        'empls': empls,
    }
    return render(request, html_template, context)


def currentWeek (request):
    workday = Workday.objects.filter(date=dt.date.today()).first()
    week = Week.objects.filter(workdays=workday).first()
    return HttpResponseRedirect (week.url())

def currentSchedule (request):
    workday = Workday.objects.filter(date=dt.date.today()).first()
    schedule = Schedule.objects.filter(workdays=workday).first()
    return HttpResponseRedirect (schedule.url())

def scheduleSolve (request, schId):
    sch = Schedule.objects.get(id=schId)
    bot = sch.Actions()
    bot.fillSlots(sch)
    return HttpResponseRedirect(sch.url())

def scheduleClearAllView (request, schId):
    sch = Schedule.objects.get(pk=schId)
    sch.slots.filled().update(employee=None)
    return HttpResponseRedirect (sch.url())
class ScheduleMaker :
    
    def generate_schedule (self, year, number):
        """
        GENERATE SCHEDULE
        ===========================================
        args: 
            - ``year``
            - ``number``
        -------------------------------------------
        """
        yeardates = []
        for date in SCH_STARTDATE_SET:
            if date.year == year:
                yeardates.append(date)
        yeardates.sort()
        n = Schedule.objects.filter(year=year,number=number).count()
        version = "ABCDEFGHIJKLMNOPQRST"[n-1]
        print(yeardates)
        start_date = yeardates[number - 1]
        sch = Schedule.objects.create(start_date=start_date, version=version, number=number, year=year)
        sch.save()
        for slot in sch.slots.all():
            slot.save()
        return sch, f"Successful Creation of schedule {sch.slug}. Completed at [{dt.datetime.now()}] "
    
def mytest (request):
    return render(request, 'sch/test/layout.html', {})

def generate_schedule_view (request,year,num):
    generate_schedule(year,num)
    return HttpResponseRedirect (reverse('sch:schedule-list'))