from django.shortcuts import render
from itertools import permutations
from sch.models import Employee, Shift, Slot, Schedule, ShiftPreference, ShiftSortPreference 


def empl_shift_swaps (request, empid):
    
    empl = Employee.objects.get (slug=empid)

    sft_combos = list(permutations(list(empl.shifts_available.all().values_list('name', flat=True)),2))

    context = dict(employee=empl, combos=sft_combos, shifts=empl.shifts_available.all())

    return render(request, 'forms/shift-swaps.pug', context)
