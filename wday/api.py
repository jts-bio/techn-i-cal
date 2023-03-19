from sch.models import *
from django.http import HttpResponse, JsonResponse
import json



def workday_context (request, wdSlug):
    context = {}
    workday = Workday.objects.get(slug=wdSlug)
    
    context['employees__working']   = [ empl for empl in workday.slots.values('employee') ]
    context['employees__pto']       = [ empl.slug for empl in workday.on_pto() ]
    context['employees__tdo']       = [ empl.slug for empl in workday.on_tdo() ]
    context['employees__on_deck']   = [ empl.slug for empl in workday.on_deck() ]
    context['employees__hours']     = { empl.slug : {
                                            'week_hours':   empl.weekHours (workday), 
                                            'period_hours': empl.periodHours (workday)
                                        } for empl in workday.schedule.employees.all() 
                                    }
    return JsonResponse(context, safe=False)
    
    
    
def empl_can_fill (request, wdSlug, empSlug):
    wd   = Workday.objects.get(slug=wdSlug)
    empl = Employee.objects.get(slug=empSlug)
    fillable_slots = []
    for slot in wd.slots.all():
        if empl.slug in list(slot.fillable_by().values_list('slug',flat=True)) :
            fillable_slots += [f"{slot.shift.name} "]
    
    return HttpResponse(fillable_slots)



def check_empl_surrounding (request, wdSlug, empSlug):
    wd = Workday.objects.get(slug=wdSlug)
    output= ""
    slotsBefore = wd.prevWD().slots.filter(employee__slug=empSlug)
    slotsAfter = wd.nextWD().slots.filter(employee__slug=empSlug)
    if slotsBefore.exists():
        if slotsBefore.first().shift.group == "PM":
            output +="""<span id="{{employee.pk}}-ind-prev-am" 
                              class="hidden bg-yellow-400 text-xs font-medium text-amber-800 text-center p-0.5 leading-none rounded-full 
                                     px-2 absolute -translate-y-1/2 -translate-x-1/2 right-auto top-0 left-0"> 
                            <i id="Prev-AM-Arrow" class="fa-duotone fa-arrow-circle-left text-black"></i>
                        </span>"""
        if slotsBefore.first().shift.group == "AM":
            output +="""<span id="{{employee.pk}}-ind-prev-am" class="hidden bg-yellow-400 text-xs font-medium text-amber-800 text-center p-0.5 leading-none rounded-full 
               px-2 absolute -translate-y-1/2 -translate-x-1/2 right-auto top-0 left-0"> <i id="Prev-AM-Arrow" class="fa-duotone fa-arrow-circle-left text-black"></i></span>"""
    if slotsAfter.exists():
        pass
    return HttpResponse(output)


def empl_check_hours (request, wdSlug, empSlug):
    wd = Workday.objects.get(slug=wdSlug)
    empl = Employee.objects.get(slug=empSlug)
    slots = wd.week.slots.filter(employee=empl)
    wk_hours = int(sum(list(slots.values_list('shift__hours', flat=True))))
    slots = wd.period.slots.filter(employee=empl)
    pd_hours = int(sum(list(slots.values_list('shift__hours', flat=True))))
    return HttpResponse(f"({wk_hours}/ {pd_hours} hrs)")