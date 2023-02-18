from django.shortcuts import render

# Create your views here.
from sch.models import *
from sch.serializers import SlotSerializer, EmployeeSerializer

from django.http import HttpResponse, JsonResponse, HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse, reverse_lazy
from django import forms
from django.views.generic.base import TemplateView, RedirectView, View
from django.db.models import SlugField, SlugField, Sum, Case, When, FloatField, IntegerField, F, Value
from django.db.models.functions import Cast
from django.views.decorators.csrf import csrf_exempt
import json

    
        
class ApiViews :
    def schedule__list (request):
        schs = Schedule.objects.all()
        page = request.GET.get('page', 1)
        page_size = 5
        return JsonResponse(schs[(page*page_size)-1:(page+1)*page_size])
    
    def schedule__get_n_empty (request, schId ):
        sch = Schedule.objects.get (slug = schId )
        return JsonResponse ( sch.slots.empty().count(), safe=False )
    
    def schedule__get_weekly_hours(request, schId):
        sch = Schedule.objects.get(slug=schId)
        employee_week_breakdowns = {}
        for employee in sch.employees.all():
            employee_week_breakdowns[employee.name] = [
                sum(list(week.slots.filter(employee=employee).values_list(
                    'shift__hours', flat=True))) for week in sch.weeks.all()
            ]
        return JsonResponse ( employee_week_breakdowns , safe=False )
    
    def schedule__get_weekly_hours__employee ( request, schId, empName ):
        employee     = Employee.objects.filter ( name__contains= empName ).first()
        sch          = Schedule.objects.get ( slug = schId )
        employee.weekBreakdown = [ sum(list(week.slots.filter(
                    employee=employee).values_list(
                        'shift__hours',flat=True))) for week in sch.weeks.all() ]
        return JsonResponse ( employee.weekBreakdown, safe=False )
    
    def schedule__get_emusr_list ( request, schId ):
        sch = Schedule.objects.get (slug = schId )
        emusrEmployees = sch.employees.emusr_employees()
        for e in emusrEmployees:
            n = sch.slots.unfavorables().filter(employee=e).count()
            e.n_unfavorables = n
        return JsonResponse ({f'{e.name}': e.n_unfavorables for e in emusrEmployees}, safe=False)
    
    def schedule__get_emusr_range ( request, schId ):
        sch = Schedule.objects.get (slug = schId )
        emusrEmployees = sch.employees.emusr_employees()
        for e in emusrEmployees:
            n = sch.slots.unfavorables().filter(employee=e).count()
            e.n_unfavorables = n
        data = {f'{e.name}': e.n_unfavorables for e in emusrEmployees}
        return JsonResponse ( max(data.values()) - min(data.values()), safe=False)
    
    def schedule__get_percent (request, schId):
        sch = Schedule.objects.get(slug=schId)
        calculatedPercent = int(sch.slots.filled().count()/ sch.slots.count() * 100)
        if sch.percent != calculatedPercent:
            sch.percent = calculatedPercent
        return JsonResponse ( int(sch.slots.filled().count()/ sch.slots.count() * 100), safe=False)
    def schedule__get_n_pto_conflicts (request, schId ):
        sch = Schedule.objects.get( slug=schId)
        return JsonResponse ( sch.slots.conflictsWithPto().count(), safe=False )
    def schedule__get_n_untrained (request, schId ):
        sch = Schedule.objects.get(slug=schId)
        return JsonResponse ( sch.slots.untrained().count(), safe=False )
    def schedule__get_untrained_list (request, schId ):
        sch = Schedule.objects.get(slug=schId)
        return JsonResponse ( SlotSerializer(sch.slots.untrained(), many=True).data, safe=False )
    def schedule__get_n_mistemplated ( request, schId ):
        sch = Schedule.objects.get(slug=schId)
        return JsonResponse ( sch.slots.mistemplated().count(), safe=False )
    def schedule__get_mistemplated_list (request, schId ):
        sch = Schedule.objects.get(slug=schId)
        return JsonResponse ( SlotSerializer(sch.slots.mistemplated(), many=True).data, safe=False )
    def schedule__get_n_unfavorables ( request, schId ):
        sch = Schedule.objects.get(slug=schId)
        return JsonResponse ( sch.slots.unfavorables().count(), safe=False )
    def schedule__get_unfavorables_list (request, schId ):
        sch = Schedule.objects.get(slug=schId)
        return JsonResponse ( SlotSerializer(sch.slots.unfavorables(), many=True).data, safe=False )
    def schedule__get_empty_list (request,schId):
        sch = Schedule.objects.get(slug=schId)
        return JsonResponse ( SlotSerializer(sch.slots.empty(), many=True).data, safe=False )
    def schedule__employee_excess_week_hours (request, schId, empId, wk):
        sch = Schedule.objects.get(slug=schId)
        emp = Employee.objects.get(slug=empId)
        slots = sch.slots.filter(workday__week__number=wk, employee=emp)
        data = {'slots': SlotSerializer(slots, many=True).data }
        return JsonResponse ( data, safe=False )
   
    def employee__week_hours (request, empId, sch, wd):
        emp = Employee.objects.get (slug = empId )
        day = Workday.objects.get (schedule= sch, slug__contains= wd)
        return HttpResponse(emp.weekHours(day))
    def employee__period_hours (request, empId, sch, wd):
        emp = Employee.objects.get ( slug = empId )
        day = Workday.objects.get (schedule= sch, slug__contains= wd)
        return HttpResponse(emp.periodHours(day))


class ApiActionViews:
    
    @csrf_exempt          
    def set__shift_img(request, shiftName):
        # get HX-PROMPT from headerp
        print(request.headers)
        url = request.session['Hx-Prompt'] = request.headers['Hx-Prompt']
        sft = Shift.objects.get(name=shiftName)
        sft.image_url = url
        sft.save()
        return HttpResponseRedirect(sft.url())
    
    @csrf_exempt
    def ptoreq__delete (request, day, emp):
        pto = PtoRequest.objects.get(workday=day,employee__slug=emp)
        pto.delete()
        return HttpResponse("<div class='text-sm text-sky-200'>DELETED</div>")
    @csrf_exempt
    def ptoreq__create (request, day, emp):
        emp = Employee.objects.get(slug=emp)
        pto = PtoRequest.objects.create(workday=day,employee=emp)
        return HttpResponse("<div class='text-sm'>CREATED</div>")
