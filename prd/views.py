from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect

from sch.models import ( Period, Schedule, PtoRequest, 
                         Employee, Shift, Slot, Workday, 
                         ShiftPreference, ShiftSortPreference )

# Create your views here.

querySum = lambda query, val: sum(list(query.values_list(val, flat=True)))


def prd_detail (request, schId:str, n:int) -> 'HttpResponse':
    sch = Schedule.objects.get(slug=schId) #type: Schedule
    prd = sch.periods.all()[n]  # type: Period
    wk1, wk2 = prd.weeks.all()
    employees = { 
        empl : (
            querySum (wk1.slots.filter(employee=empl),"shift__hours"),
            querySum (wk2.slots.filter(employee=empl),"shift__hours")
        ) for empl in sch.employees.all() 
    } # type: dict
    return render(request, './prd/hours-matrix.html', {"employees":employees, "period":prd })

def preline_table (request) -> 'HttpResponse':
    return render (request, 'prd/preline-table.html')