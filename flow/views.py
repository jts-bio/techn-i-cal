from django.shortcuts import render

# Create your views here.
from sch.models import *

from django.http import HttpResponse, JsonResponse, HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse, reverse_lazy
from django import forms
from django.views.generic.base import TemplateView, RedirectView, View





    
        
class Api :
    
    def schedule__get_weekly_hours__employee ( request, schId, empName ):
        employee     = Employee.objects.filter ( name__contains= empName ).first()
        sch          = Schedule.objects.get ( slug = schId )
        employee.weekBreakdown = [ sum(list(week.slots.filter(
                    employee=employee).values_list(
                        'shift__hours',flat=True))) for week in sch.weeks.all() ]
        
        return JsonResponse ( employee.weekBreakdown, safe=False )



        