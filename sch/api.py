from .models import *
from django.http import HttpResponse, JsonResponse
from django.db.models import Sum, Case, When, FloatField, Count, IntegerField

class WeekApi: 
    
    class GET:
    
        def employeeHours (request, weekId, empId=None):
            week = Week.objects.get(pk=weekId)
            if empId:
                emp = week.total_hours().filter(pk=empId)
                if emp.exists():
                    hrs = emp.first().hours
                    if hrs == None:
                        hrs = 0
                else:
                    hrs = 0 
            else:
                hrs = week.total_hours()
            return HttpResponse(f"({hrs} hours in week)")
  


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
        def percent (request, schid):
            sch = Schedule.objects.get(slug=schid)
            return HttpResponse(sch.percent())
        
        