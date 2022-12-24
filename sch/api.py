from .models import *
from django.http import JsonResponse
from django.db.models import Sum

class WeekApi: 
    
    class GET:
    
        def employeeHours (request, weekid):
            week = Week.objects.get(pk=weekid)
            slots = week.workdays.slots.all().order_by('employee')
            employees = slots.values('employee').distinct()
            employees.annotate(hours=Sum('shift__hours'))
            return employees
        
