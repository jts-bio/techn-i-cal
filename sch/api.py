from .models import *
from django.http import JsonResponse
from django.db.models import Sum, Case, When, FloatField, Count, IntegerField

class WeekApi: 
    
    class GET:
    
        def employeeHours (request, weekid):
            
            week      = Week.objects.get(pk=weekid)
            slots     = week.workdays.slots.all().order_by('employee')
            employees = slots.values('employee').distinct()
            employees.annotate(hours=Sum('shift__hours'))
            return employees
  


class ScheduleApi:
    
    class GET:
        
        def employee_unpref_count (request, schid):
            
            sch = Schedule.objects.get(slug=schid)
            empls = Employee.objects.annotate(
                unpref_count = Count( Case( 
                        When(
                            slots__in=sch.slots.unfavorables().filter(employee=F('pk'))),
                            then='slots__pk'),  
                        default=0, output_field=IntegerField())).order_by('-unpref_count')
            return empls
        
        