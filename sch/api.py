from .models import *
from django.http import JsonResponse


class WeekApi: 
    
    class GET:
    
        def employeeHours (request, weekid):
            week = Week.objects.get(pk=weekid)
            slots = week.workdays.slots.all().order_by('employee')
            return sum(list(slots.values_list('shift__hours')))
        
