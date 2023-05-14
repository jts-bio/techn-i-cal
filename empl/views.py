from django.shortcuts import render, redirect
from itertools import permutations
from sch.models import Employee, Shift, Slot, Schedule, ShiftPreference, ShiftSortPreference 


def empl_list (request):
    employees = Employee.objects.all()
    context = {
        'employees': employees
    }
    return render(request, 'list/employee-list.pug', context)



def empl_new (request):
    from sch.forms import EmployeeForm
    if request.method == 'POST':
        form = EmployeeForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('empl:list')
        else:
            print(form.errors)
    else:
        form = EmployeeForm()
    return render(request, 'forms/new-employee.pug', {'form': form})

def empl_shift_swaps (request, empl):
    
    empl = Employee.objects.get(slug=empl)
    sft_combos = list(permutations(list(empl.shifts_available.all().values_list('name', flat=True)),2))

    context = dict(
        employee=empl,
        combos=sft_combos,
        shifts=empl.shifts_available.all()
    )
    return render(request, 'forms/shift-swaps.pug', context)


def empl_profile_img_browser(request, empid):
    from sch.data import Images
    from django.contrib import messages

    if request.method == "POST":

        employee = Employee.objects.get(slug=empid)
        employee.image_url = request.POST.get('img_input')
        employee.save()

        messages.success(request, f'Profile image for {employee} successfully updated.')
        return redirect('empl:list')

    context = {
            "images":   Images.PROFILE_OPTIONS,
            "employee": Employee.objects.get(slug=empid)
        }
    return render(request, 'forms/img-chooser.pug', context)
