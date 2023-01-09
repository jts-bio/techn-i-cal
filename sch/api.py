from .models import *
from django.http import HttpResponse, JsonResponse, HttpResponseRedirect
from django.db.models import Sum, Case, When, FloatField, Count, IntegerField
from django.views.decorators.csrf import csrf_exempt
from django.contrib import messages
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
  

class WdApi:
    class Post:
        
        @csrf_exempt
        def fillSlotWithApi (request, wdSlg , shiftSlg, empId):
            """
            Fills a slot with an employee via their id"""
            if request.method == 'POST':
                wd = Workday.objects.get(slug=wdSlg)
                shift = Shift.objects.get(pk=shiftSlg)
                emp = Employee.objects.get(pk=empId)
                slot = Slot.objects.get(workday=wd, shift=shift)
                if slot.employee == emp:
                    messages.info(request,f"API rejected request, Employee already occupies that slot")
                    change = None
                elif slot.siblings_day.filter(employee=emp).exists():
                    messages.error(request,f"(API rejected request, Employee already occupies a sibling slot")
                    change = None
                else:
                    old_empl = slot.employee
                    slot.employee = emp
                    slot.save()
                    messages.success(request,f"(API filled slot {slot.shift} with {emp.name})")
                    change = f'{old_empl} -> {emp}'
            else:
                messages.error(request,f"(API rejected request, not POST)")
            
            return JsonResponse(
                                {'slot'    : slot.slug ,
                                 'employee': emp.name,
                                 'change'  : change } 
                                )

    
class ScheduleApi:
    
    class GET:
        
        def employee_unpref_count (request, schid):
            """
            Schedule-wide UNFAVORABLES COUNT by Employee
            ===========================================
            ex output:
                >>> 
            """
            sch = Schedule.objects.get(slug=schid)
            empls = Employee.objects.annotate(
                unpref_count = Avg( Case( 
                        When(
                            slots__in=sch.slots.unfavorables().filter(employee=F('pk'))),
                            then=1),  
                            output_field=IntegerField(),
                            default=0)).order_by('-unpref_count')
            return HttpResponse(empls.values('name','unpref_count','fte',))

        
        def percent (request, schid):
            sch = Schedule.objects.get(slug=schid)
            return HttpResponse(sch.percent())
        
class SlotApi:
    def checkEmpFillability (request, slotId, empId):
        slot = Slot.objects.get(pk=slotId)
        emp = Employee.objects.get(pk=empId)
        if emp in slot.fillable_by():
            return HttpResponse("True")
        else:
            return HttpResponse("False")