
from .models import *
from  django.http import JsonResponse, HttpResponse, HttpResponseRedirect, HttpRequest
from django.shortcuts import render, get_object_or_404, get_list_or_404, redirect



def listEmployees (request):
    html_template = 'sch2/employees.html'
    
    employees = Employee.objects.all()
    
    context = {
        'employees' : employees,
    }
    return render(request, html_template, context)
