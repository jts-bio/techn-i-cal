from django.shortcuts import render, HttpResponse, HttpResponseRedirect
from django.views.generic.detail import DetailView
from django.forms import formset_factory

from .models import Shift, Employee, Workday, Slot, ShiftManager, ShiftTemplate
from .forms import SlotForm, TemplateSlotForm
from .actions import WorkdayActions
from django.db.models import Q, F, Sum

import datetime as dt


# Create your views here.

def index(request):
    today = dt.date.today()
    wd = Workday.objects.get(date=today)
    shifts = wd.shifts()
    context = {
        'wd': wd, 
        'shifts': shifts,
    }
    return render(request, 'sch2/index.html', context)

class WorkDayDetailView (DetailView):

    model           = Workday
    template_name   = 'sch2/workday.html'

    def get_context_data(self, **kwargs):
        context             = super().get_context_data(**kwargs)
        context['wd']       = self.object
        context['today']    = dt.date.today()
        context['shifts']   = Shift.objects.on_weekday(weekday=self.object.iweekday) 
        context['sameWeek'] = Workday.objects.same_week(self.object)
        context['slots']    = Slot.objects.filter(workday=self.object)
        context['slotdeet'] = Slot.objects.on_workday(self.object)
        # Context = wd, shifts, sameWeek, slots, slotdeet
        return context
    
    def get_object(self):
        return Workday.objects.get(slug=self.kwargs['slug'])

def workdayFillTemplate(request, date):
    # URL : /sch2/day/<date>/fill/
    workday = Workday.objects.get(date=date)
    WorkdayActions.fillDailyTSS(workday)
    return HttpResponseRedirect(f'/sch2/day/{date}/')

def weekView (request, year, week):
    week_num = week
    week_yr  = year
    week = Workday.objects.in_week(year, week)
    slots = Slot.objects.filter(workday__in=week)
    shifts = Shift.objects.all()
    # annotate each day in week, so that it has a list of shifts that occur on that workday, and the slot employee if one is assigned
    for day in week:
        day.getshifts = Shift.objects.on_weekday(day.iweekday)
        day.slots     = slots.filter(workday=day)

    employees = Employee.objects.all()
    employees = employees.annotate(weekly_hours=Sum(F('slot__shift__duration')-dt.timedelta(minutes=30), filter=Q(slot__workday__iweek=week_num, slot__workday__date__year=week_yr)))
    
    context = {
        'week': week,
        'slots': slots,
        'shifts': shifts,
        'week_num': week_num,
        'week_yr': week_yr,
        'employees': employees,
    }
    return render(request, 'sch2/week.html', context)


class EmployeeDetailView (DetailView):

    model           = Employee
    template_name   = 'sch2/employee.html'

    def get_context_data(self, **kwargs):
        context             = super().get_context_data(**kwargs)
        context['employee'] = self.object
        context['slots']    = Slot.objects.filter(employee=self.object)
        context['shifts']   = self.object.shifts_trained.all()
        context['next7']    = Workday.objects.filter(date__gte=dt.date.today())[:7]
        # use templateTags to get the next 7 days : 
        #                     EMPL_GETSHIFT(wd,empl)
        return context
    
    def get_object(self):
        return Employee.objects.get(name=self.kwargs['name'])


def slotAdd (request, date, shift):
    if request.method == 'POST':
        form = SlotForm(request.POST)
        if form.is_valid():
            employee = form.cleaned_data['employee']
            workday  = Workday.objects.get(slug=date)
            shift    = Shift.objects.get(name=shift)
            slot = Slot.objects.create(workday=workday, shift=shift,employee=employee)
            slot.save()
            return HttpResponseRedirect(f'/sch2/day/{workday.slug}/')
    workday = Workday.objects.get(date=date)
    shift   = Shift.objects.get(name=shift)

    employees_available = Employee.objects.filter(shifts_available=shift)

    othershifts = Shift.objects.exclude(name=shift)
    empls_on_day = Slot.objects.filter(workday=workday, shift__in=othershifts).values('employee')
    employees_on_day = Employee.objects.filter(pk__in=empls_on_day)

    employees = employees_available.exclude(pk__in=employees_on_day)

    if shift.start < dt.time(12,0):
        if Workday.objects.filter(date=workday.date - dt.timedelta(days=1)).exists():
            daybefore = Workday.objects.get(date=workday.date - dt.timedelta(days=1))
            empls_on_dayb = Slot.objects.filter(workday=daybefore, shift__start__gte=dt.time(12,0)).values('employee')
            employees = employees.exclude(pk__in=empls_on_dayb)
    
    if shift.start > dt.time(12,0):
        if Workday.objects.filter(date=workday.date + dt.timedelta(days=1)).exists():
            dayafter = Workday.objects.get(date=workday.date + dt.timedelta(days=1))
            empls_on_daya = Slot.objects.filter(workday=dayafter, shift__start__lte=dt.time(12,0)).values('employee')
            employees = employees.exclude(pk__in=empls_on_daya)

    week_num = workday.iweek
    week_yr  = workday.date.year
    employees_hrs_available = employees.annotate(weekly_hours=Sum(F('slot__shift__duration')-dt.timedelta(minutes=30), filter=Q(slot__workday__iweek=week_num, slot__workday__date__year=week_yr)))
    print(employees_hrs_available.values('name','weekly_hours'))
    employees_no_hrs_avaliable = employees_hrs_available.filter(weekly_hours__gt=(dt.timedelta(hours=40)-shift.duration + dt.timedelta(minutes=30))) 
    
    employees = employees.exclude(pk__in=employees_no_hrs_avaliable)

    context = {
        'workday':   workday,
        'shift':     shift,
        'employees': employees,
    }
    return render(request, 'sch2/slot/slotAdd.html', context)
    
def slotAdd_post (request, date, shift):
    if request.method == 'POST':
        form = SlotForm(request.POST)
        if form.is_valid():
            employee = form.cleaned_data['employee']
            slot = Slot.objects.create(workday=workday.slug, shift=shift,employee=employee)
            slot.save()
            return HttpResponseRedirect(f'/sch2/day/{workday.slug}/')
    else:
        return HttpResponse('Error: Not a POST request')

def slot(request, date, shift):
    if Slot.objects.filter(workday__slug=date, shift__name=shift).exists():
        slot = Slot.objects.get(workday__slug=date, shift__name=shift)
        context = {
            'slot': slot,
        }
        return render(request, 'sch2/slot.html', context)
    else:
        wd = Workday.objects.get(slug=date)
        context = {
            'wd': wd,
            'shift': Shift.objects.get(name=shift),
            'wdURL': wd.get_absolute_url(),
            'fillURL': f'/sch2/day/{date}/{shift}/add/',
        }
        return render(request, 'sch2/slot/noSlot.html', context)

def slotDelete(request, date, shift):
    slot = Slot.objects.get(workday__slug=date, shift__name=shift)
    slot.delete()
    return HttpResponseRedirect(f'/sch2/day/{date}/')

def shift (request, shift):
    shift = Shift.objects.get(name=shift)
    weekdaynames = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    
    context = {
        'shift': Shift.objects.get(name=shift),
        'employees': Employee.objects.trained_for(shift),
        'tss': ShiftTemplate.objects.filter(shift=shift),
        'weekdaynames': weekdaynames,
    }
    return render(request, 'sch2/shift.html', context)

def shiftTemplate (request, shift):
    context               = {}
    shift                 = Shift.objects.get(name=shift)
    context['shift']      = shift
    context['dayrange']   = range(14)
    context['wd']         = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat']
    on_days = shift.ppd_ids 
    TmpSlotFormSet = formset_factory(TemplateSlotForm, extra=0)

    

    if request.method == 'POST':
        TmpSlotFormSet = formset_factory(TemplateSlotForm)
        formset = TmpSlotFormSet(request.POST)
        for form in formset:
            if form.is_valid():
                print('valid')
                if form.cleaned_data['employee'] != None:
                    print(form.cleaned_data)
                    employee = form.cleaned_data['employee']
                    ppd_id  = form.cleaned_data['ppd_id']
                    weekAB = "AB"[ppd_id//7-1]
                    if ShiftTemplate.objects.filter(shift=shift, employee=employee, ppd_id=ppd_id).exists()==False:
                        slot = ShiftTemplate.objects.create(ppd_id=ppd_id,shift=shift, employee=employee)
                        slot.save()
            else:
                print(form.errors)
                    
        return HttpResponseRedirect(f'/sch2/shift/{shift.name}/')

    initData = [
        {'ppd_id': i, 'shift': shift } for i in on_days
        ]

    formset = TmpSlotFormSet(initial=initData)

    context = {
        'shift': Shift.objects.get(name=shift),
        'employees': Employee.objects.trained_for(shift),
        'formset': formset,
        'idata': initData,

    }
    return render(request, 'sch2/shift/shiftTemplate.html', context)


    
