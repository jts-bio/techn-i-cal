from sch.models import *
from django.http import HttpResponse
import json




def empl_can_fill (request, wdSlug, empSlug):
    wd = Workday.objects.get(slug=wdSlug)
    empl = Employee.objects.get(slug=empSlug)
    fillable_slots = []
    for slot in wd.slots.all():
        if empl.slug in list(slot.fillable_by().values_list('slug',flat=True)) :
            fillable_slots += [f"{slot.shift.name} "]
    
    return HttpResponse(fillable_slots)