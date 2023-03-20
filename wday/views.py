import datetime as dt
import logging

from django.db import models
from django.db.models import (
    Subquery,Case, F, FloatField, IntegerField, SlugField,
                              Sum, Value, When, F, Q, OuterRef)
from django.shortcuts import reverse, render
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse

from sch.models import Schedule, Workday, Employee, Slot, Shift, WorkdayViewPreference, WD_VIEW_PREF_CHOICES
from django.contrib import messages
from django.views.decorators.csrf import csrf_exempt


# LOGGING ================================
logging.basicConfig(
        filename='workday-logs.log',
        level=logging.INFO)
logging.root.handlers[0].setFormatter(logging.Formatter('%(message)s'))
# ========================================


def testing (request, wdSlug):
    context= {
        'workday': Workday.objects.get(slug=wdSlug),
    }
    return render(request, 'wday/testing.html', context)

class Partials:
    def spwdBreadcrumb (request, wdSlug):
        wd = Workday.objects.get(slug=wdSlug)
        context = {'workday': wd}
        return render(request, 'wday/partials/SPWD.html', context)
    
    def slotPopover (request, slotId):
        slot = Slot.objects.get(id=slotId)
        context = {'slot': slot}
        return render(request, 'wday/partials/popover.html', context)
    
    def events (request):
        return render(request, 'wday/partials/events.html')



def wdListView (request, schSlug='current'):
    if schSlug == 'current' :
        schedule = Schedule.objects.filter(workdays__date__contains=dt.date.today()).first()
    else:
        schedule = Schedule.objects.get(slug=schSlug)
        
    workdays = schedule.workdays.annotate(
                        bgColor=
                                Case(
                                    When(percent__lte=50, then=Value('bg-indigo-900 bg-opacity-70')),
                                    When(percent__lte=75, then=Value('bg-indigo-800 bg-opacity-80')),
                                    When(percent__lte=85, then=Value('bg-indigo-700 bg-opacity-90')),
                                    When(percent__lte=100,then=Value('bg-indigo-600 border-indigo-400')),
                                )            
                            )
    context = {'view_schedule': schedule, 'schedules': Schedule.objects.all(), 'workdays': workdays}
    return render(request, 'wday/wd-list.html', context)

def wdDetailView (request, slug:str):
    """
    WORKDAY DETAIL VIEW
    ----------------------------
    View for single workday. Individual Shift Slots and their assigned employees
    are visible. Based on users preferences, this view can utilize different templates.
    
    `for employee in workday.on_deck().all():`
    `employee.weekHours`
    >>> 40.0
    
    `workday.pto_list()`
    >>> ['Josh-S', 'Sabrina-B', 'Brittanie-S']
    """
    wd = Workday.objects.get(slug=slug) #type:Workday
    wd.save()
    
    for employee in wd.on_deck().all():
        employee.weekHours = Sum('slots__shift__hours', filter=Q(slots__workday__iweek=wd.iweek))
    for slot in wd.slots.all():
        if slot.employee:
            slot.employee.weekHours = Sum('slots__shift__hours', filter=Q(slots__workday__iweek=wd.iweek))
    
    logger = logging.getLogger('workdayLogger')
    logger.info (f'WORKDAY DETAIL VIEW ::: viewed by user='+str(request.user))
    logger.info (f'     workday: {wd}')
    logger.info (f'     weekHours : {[(empl.slug, empl.weekHours(wd)) for empl in wd.on_deck().all()]}')
    
    context = dict (
            workday =    wd, 
            slots =      wd.slots.all(),
            employees =  wd.schedule.employees.all().annotate(
                weekHours =     Sum('slots__shift__hours', filter=Q(slots__workday__iweek=wd.iweek))), 
                periodHours =   Sum('slots__shift__hours', filter=Q(slots__workday__period=wd.period)),
            )
    viewPref_template = WorkdayViewPreference.objects.get(user=request.user).view
    
    #   NOTE /
    #   THIS VIEW UTILIZES A USER PREFERENCE 
    #   TO DETERMINE TEMPLATE USED
    return render(request, WD_VIEW_PREF_CHOICES[int(viewPref_template)][1] , context)

class WdActions: 
    
    @staticmethod
    def empl_can_fill (request, slug:str ,empSlug:str):
        wd = Workday.objects.get(slug=slug)
        empl = Employee.objects.get(slug=empSlug)
        fillable_slots = ""
        for slot in wd.slots.all():
            if empl.slug in list(slot.fillable_by().values_list('slug',flat=True)) :
                fillable_slots += f"{slot.shift.name} "
        
        return HttpResponse(fillable_slots)
    
    @staticmethod
    def fill_with_template (request, wd, shift):
        slot = Slot.objects.get(workday__slug=wd,shift__name=shift)
        slot.actions.set_template_employee (slot)
        return HttpResponse (f"Slot {slot.shift} has been filled with template employee.")
            
def slotDetailView (request, slug, shiftId):
    pass

class SlotActions:
    
    @csrf_exempt
    def slotDeleteView (request, slug):
        print (request.headers)
        empId = request.headers['empId']
        if Slot.objects.filter(employee__pk=empId,workday__slug=slug).exists():
            slot = Slot.objects.get(employee__pk=empId, workday__slug=slug)
        slot.employee = None
        slot.save()
        messages.info (request, f"Slot {slot.shift} has been cleared successfully.")
        return HttpResponse (f"Slot {slot.shift} has been cleared successfully.")

    def slotUpdateView (request, slug, shiftId):
        # get the employee to update to from request header
        print(request.headers)
        empId = request.headers['empId']
        emp = Employee.objects.get(slug=empId)
        slot = Slot.objects.get(shift__name=shiftId, workday__slug=slug)
        if slot.siblings_day.filter(employee__slug=empId).exists():
            slot.siblings_day.filter(employee__slug=empId).update(employee=None)
        slot.employee = None
        slot.employee = Employee.objects.get(slug=empId)
        slot.save()
        messages.success(request, f"Slot {slot.shift} has been filled successfully.")
        return HttpResponseRedirect( reverse('wday:detail', kwargs={'slug': slug} ))
    
    def slotAssignView (request, wd, sft, empl):
        wd = Workday.objects.get(slug=wd)
        sft = Shift.objects.get(name=sft)
        empl = Employee.objects.get(slug=empl)
        slot = Slot.objects.get(workday=wd, shift=sft)
        if slot.siblings_day.filter(employee=empl).exists():
            slot.siblings_day.filter(employee=empl).update(employee=None)
        slot.employee = empl
        slot.save()
        return HttpResponse(f"SA200: {sft.name} SLOT ASSIGNMENT TO {empl.slug.upper()} SUCCESSFUL")
