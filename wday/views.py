import datetime as dt
from django.db import models
from django.db.models import (
    Subquery,Case, F, FloatField, IntegerField, SlugField,
                              Sum, Value, When, F, Q, OuterRef)
from django.shortcuts import reverse, render
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse

from sch.models import Schedule, Workday, Employee, Slot, WorkdayViewPreference, WD_VIEW_PREF_CHOICES
from django.contrib import messages



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
                                    When(percent__lte=100, then=Value('bg-indigo-600 border-indigo-400')),
                                )            
                            )
    context = {'view_schedule': schedule, 'schedules': Schedule.objects.all(), 'workdays': workdays}
    return render(request, 'wday/wd-list.html', context)


def wdDetailView (request, slug):
    wd = Workday.objects.get(slug=slug)
    context = {'workday': wd } 
    viewPref_template = WorkdayViewPreference.objects.get(user=request.user).view
    
    # NOTE // THIS VIEW UTILIZES A USER PREFERENCE TO DETERMINE TEMPLATE USED
    return render(request, WD_VIEW_PREF_CHOICES[int(viewPref_template)][1] , context)

class WdActions:
    def empl_can_fill (request, slug,empSlug):
        wd = Workday.objects.get(slug=slug)
        empl = Employee.objects.get(slug=empSlug)
        fillable_slots = ""
        for slot in wd.slots.all():
            if empl.slug in list(slot.fillable_by().values_list('slug',flat=True)) :
                fillable_slots += f"{slot.shift.name} "
        
        return HttpResponse(fillable_slots)
    
            
def slotDetailView (request, slug, shiftId):
    pass

class SlotActions:
    
    def slotDeleteView (request, slug, shiftId):
        slot = Slot.objects.get(shift__pk=shiftId, workday__slug=slug)
        slot.employee = None
        slot.save()
        messages.info(request, f"Slot {slot.shift} has been cleared successfully.")
        return HttpResponseRedirect( reverse('wd-detail', kwargs={'slug': slug} ))
    
    def slotUpdateView (request, slug, shiftId, empId):
        slot = Slot.objects.get(shift__name=shiftId, workday__slug=slug)
        empl = Employee.objects.get(slug=empId)
        if slot.siblings_day.filter(employee__slug=empId).exists():
            slot.siblings_day.filter(employee__slug=empId).update(employee=None)
        slot.employee = None
        slot.employee = Employee.objects.get(slug=empId)
        slot.save()
        messages.success(request, f"Slot {slot.shift} has been filled successfully.")
        return HttpResponseRedirect( reverse('wday:wd-detail', kwargs={'slug': slug} ))
