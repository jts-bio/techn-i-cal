from django.shortcuts import render

# Create your views here.
from sch.models import *
from sch.serializers import SlotSerializer

from django.http import HttpResponse, JsonResponse, HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse, reverse_lazy
from django import forms
from django.views.generic.base import TemplateView, RedirectView, View
from django.db.models import SlugField, SlugField, Sum, Case, When, FloatField, IntegerField, F, Value
from django.db.models.functions import Cast
from django.views.decorators.csrf import csrf_exempt
from sch.viewsets import SchViews
    
        
class ApiViews :
    
    def schedule__get_n_empty (request, schId ):
        sch = Schedule.objects.get (slug = schId )
        return JsonResponse ( sch.slots.empty().count(), safe=False )
    
    def schedule__get_weekly_hours (request, schId ):
        sch = Schedule.objects.get (slug = schId )
        # on each employee, annotate the sum of thier weekly hours from slots assigned to them. Each
        # employee will have a list of 6 numbers, one for each week.
        for sch in Schedule.objects.all():
            for employee in sch.employees.all():
                employee.weekBreakdown = [ sum(list(week.slots.filter(
                    employee=employee).values_list(
                        'shift__hours',flat=True))) for week in sch.weeks.all() ]
    
        return JsonResponse ( sch.employees.values_list('name','weekBreakdown'), safe=False )
    
    def schedule__get_weekly_hours__employee ( request, schId, empName ):
        employee     = Employee.objects.filter ( name__contains= empName ).first()
        sch          = Schedule.objects.get ( slug = schId )
        employee.weekBreakdown = [ sum(list(week.slots.filter(
                    employee=employee).values_list(
                        'shift__hours',flat=True))) for week in sch.weeks.all() ]
        
        return JsonResponse ( employee.weekBreakdown, safe=False )
    
    def schedule__get_emusr ( request, schId ):
        sch = Schedule.objects.get (slug = schId )
        fig = SchViews.Calc.emusr_distr(request,sch).contentP
        return JsonResponse (dict(sch=fig))
    
    def schedule__get_percent (request, schId):
        sch = Schedule.objects.get(slug=schId)
        calculatedPercent = int(sch.slots.filled().count()/ sch.slots.count() * 100)
        if sch.percent != calculatedPercent:
            sch.percent = calculatedPercent
        return JsonResponse ( int(sch.slots.filled().count()/ sch.slots.count() * 100), safe=False)
    
    def schedule__get_n_pto_conflicts (request, schId ):
        sch = Schedule.objects.get( slug=schId)
        return JsonResponse ( sch.slots.conflictsWithPto().count(), safe=False )
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
    def schedule__get_emusr_list (request, schId ):
        sch = Schedule.objects.get(slug=schId)
        return JsonResponse ( EmployeeSerializer(sch.employees.all(), many=True).data, safe=False )
    

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
    

# <a href="" class="rounded hover:transition hover:bg-slate-700 hover:scale-110">
#           <p class="text-3xl font-semibold 
#                   {% if uf_stdev_diff < 0 %}  text-red-600
#                   {% else %}                  text-emerald-300   
#                   {% endif %}"
#               hx-get="{% url 'sch:sch-calc-uf-distr' schedule.slug %}"
#               hx-target="#uf-stdev-diff"
#               hx-trigger="load">
                
#               <!-- SWAP AREA FOR UF-DISTR -->
#                 <span id="uf-stdev-diff">
#                           <i class="fa-loader fa-duotone fa-spin fa-beat opacity-60"></i>
#                 </span>
#                 <span class="opacity-80 text-sm">SDfµ</span>
#               <!-- icon ECLIPSE -->
#               <i class="fa-duotone fa-moon-over-sun"></i>
                
#           </p>
#           <p class="mt-1 text-xs font-light text-gray-500">
#               Unfavorable Slots
#               <span class="italic text-xs font-light opacity-80">(n={{ schedule.slots.unfavorables.count }} slots) </span>
#           </p> 
#       </a>