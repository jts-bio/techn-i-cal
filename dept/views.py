from django.shortcuts import render
from django.http import HttpResponse
from django.template import loader
from sch.models import Schedule, Employee, Workday, Slot, PtoRequest, Department

# Create your views here.

def dept_detail(request, org, dept):
    template = loader.get_template('dept/dept-index.pug')
    dept = Department.objects.get(org__slug=org, slug=dept)
    context = {'dept': dept}
    return HttpResponse(template.render(context, request))


def new_employee_partial(request, org, dept):
    template = loader.get_template('dept/detail/new-employee.pug')
    context = {
            'org_id': org,
            'dept_id': dept,
            'department': Department.objects.get(org__slug=org, slug=dept)
        }
    return HttpResponse(template.render(context, request))

