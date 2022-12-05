from django.shortcuts import render

# Create your views here.
from sch.models import *

from django.http import HttpResponse, JsonResponse, HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse, reverse_lazy
from django import forms
from django.views.generic.base import TemplateView, RedirectView, View




class  EmployeeSortShiftPreferences  (View):
        template_name = 'flow/alpine--drag-and-drop.html'
    
        def  get (self, request, slug, **kwargs):
            context = {
                    'employee': Employee.objects.get(slug=slug)
                    }
            return render(request, self.template_name, context) 
    
        def  post (self, request, **kwargs):
            print (request.POST)
            employee = instance = Employee.objects.get(slug=kwargs['slug'])
            shifts = request.POST.getlist('shifts')
            employee.shift_sorts.all().delete()
            i = 1
            for shift in shifts:
                ShiftSortPreference.objects.create(employee=employee, shift_id=shift, sort_order=i)
            return HttpResponseRedirect( employee.url() )
    
        
    



        