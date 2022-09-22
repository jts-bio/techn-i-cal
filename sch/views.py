from django.shortcuts import render, HttpResponse, HttpResponseRedirect, redirect
from django.db.models import query
from django.urls import reverse_lazy
from django.views.generic.detail import DetailView
from django.views.generic.list import ListView
from django.views.generic.edit import CreateView, UpdateView, DeleteView, FormView
from django.forms import formset_factory

from .models import PtoRequest, Shift, Employee, Workday, Slot, PtoRequest, ShiftManager, ShiftTemplate, WorkdayManager

from .forms import SlotForm, SstForm, ShiftForm, EmployeeForm, EmployeeEditForm, BulkWorkdayForm, SSTForm, SstEmployeeForm, PTOForm, PTORangeForm

from .actions import WorkdayActions

from .tables import EmployeeTable, ShiftListTable, ShiftsWorkdayTable, ShiftsWorkdaySmallTable, WeeklyHoursTable, WorkdayListTable, PtoListTable

from django.db.models import Q, F, Sum, Subquery, OuterRef, DurationField, ExpressionWrapper, Count

from django_tables2 import tables

import datetime as dt


# Create your views here.

def index(request) -> HttpResponse:
    today = dt.date.today()
    wd = Workday.objects.get(date=today)
    shifts = wd.shifts()
    context = {
        'wd': wd, 
        'shifts': shifts,
    }
    return render(request, 'static/index.html', context)


def day_changer (request, date) -> HttpResponse:
    workday = Workday.objects.get(slug=date)
    template_html = 'sch/workday/dayChanger.html'
    return render(request, template_html, {'workday': workday})

class WORKDAY :
    class WorkdayListView (ListView):

        model = Workday
        template_name = 'sch/workday/list.html'
        context_object_name = 'workdays'
        
        def get_context_data(self, **kwargs):
            context = super().get_context_data(**kwargs)
            context['title'] = 'Workdays'
            context['table'] = WorkdayListTable(self.get_queryset())
            return context

        def get_queryset(self):
            return Workday.objects.filter(date__gte=dt.date.today()).order_by('date')

    class WorkDayDetailView (DetailView):

        model           = Workday
        template_name   = 'sch/workday/workday_detail.html'

        def get_context_data(self, **kwargs):
            context             = super().get_context_data(**kwargs)
            context['wd']       = self.object  # type: ignore
            context['today']    = dt.date.today()
            shifts              = Shift.objects.on_weekday(weekday=self.object.iweekday)   # type: ignore
            slots               = Slot.objects.filter(workday=self.object)
            sftAnnot            = shifts.annotate(employee=Subquery(slots.filter(shift=OuterRef('pk')).values('employee__name')))
            context['table']    = ShiftsWorkdayTable(sftAnnot, order_by="start")
            context['sameWeek'] = Workday.objects.same_week(self.object)  # type: ignore

            unfilled            = Shift.objects.filter(occur_days__contains=self.object.iweekday).exclude(pk__in=slots.values('shift')) # type: ignore
            context['unfilled'] = unfilled

            ptoReqs             = PtoRequest.objects.filter(workday=self.object.date).values('employee')
            context['ptoReqs']    = Employee.objects.filter(pk__in=ptoReqs)
            
            # Context = wd, shifts, sameWeek, slots, slotdeet
            return context
        
        def get_object(self):
            return Workday.objects.get(slug=self.kwargs['slug'])

    class WorkdayBulkCreateView (FormView):
        template_name = 'sch/workday/bulk_create.html'
        form_class = BulkWorkdayForm
        success_url = reverse_lazy('workday-list')

        def form_valid(self, form):
            date_from = form.cleaned_data['date_from']
            date_to = form.cleaned_data['date_to']
            WorkdayActions.bulk_create(date_from, date_to) # type: ignore
            return super().form_valid(form)

def workdayFillTemplate(request, date):
    # URL : /sch2/day/<date>/fill/
    workday = Workday.objects.get(date=date)
    WorkdayActions.fillDailySST(workday)
    return HttpResponseRedirect(f'/sch/day/{date}/')

class WEEK:
    class WeekView (ListView):

        model = Workday
        template_name = 'sch/week/week.html'
        context_object_name = 'workdays'

        def get_context_data(self, **kwargs):
            context = super().get_context_data(**kwargs)
            context['title']      = 'Week'
            context['year']       = self.kwargs['year']
            year                  = self.kwargs['year']
            context['week_num']   = self.kwargs['week']
            week                  = self.kwargs['week']

            context['hrsTable']   = [(empl, Slot.objects.empls_weekly_hours(year, week, empl)) for empl in Employee.objects.all()]
            
            for day in context['workdays']:
                                    day.table = self.render_day_table(day)
            total_unfilled = 0

            for day in self.object_list:
                total_unfilled += day.n_unfilled
            context['total_unfilled'] = total_unfilled
            return context

        def get_queryset(self):
            return Workday.objects.filter(date__year=self.kwargs['year'], iweek=self.kwargs['week']).order_by('date')

        def get_day_table(self, workday):
            shifts              = Shift.objects.on_weekday(weekday=workday.iweekday)   # type: ignore
            slots               = Slot.objects.filter(workday=workday)
            sftAnnot            = shifts.annotate(employee=Subquery(slots.filter(shift=OuterRef('pk')).values('employee__name')))
            return ShiftsWorkdaySmallTable(sftAnnot, order_by="start")

        def render_day_table(self, workday):
            return self.get_day_table(workday).as_html(self.request)

        def get_hours_queryset (self, year, week):
            return Employee.objects.all().annotate(
                hours=Subquery(Slot.objects.filter(workday__date__year=year,workday__iweek=week, employee=F('pk')).aggregate(hours=Sum('hours')))
            )

    def weekView (request, year, week):
        week_num = week
        week_yr  = year
        week     = Workday.objects.in_week(year, week)  # type: ignore
        slots    = Slot.objects.filter(workday__in=week)
        shifts   = Shift.objects.all()
        # annotate each day in week, so that it has a list of shifts that occur on that workday, and the slot employee if one is assigned
        for day in week:
            day.getshifts = Shift.objects.on_weekday(day.iweekday)  # type: ignore
            day.slots     = slots.filter(workday=day)

        employees = Employee.objects.all()
        wk_hrs    = employees.annotate(
            weekly_hours=Sum(
                (ExpressionWrapper(F('slot__shift__duration'), output_field=DurationField())-dt.timedelta(minutes=30)),
                filter=Q(slot__workday__iweek=week_num, slot__workday__date__year=week_yr))).values('name','weekly_hours')
        
        table = WeeklyHoursTable(Employee.objects.all())
    # type: ignore
        print(wk_hrs)
        context = {
            'workdays'  : week,
            'slots'     : slots,
            'shifts'    : shifts,
            'week_num'  : week_num,
            'week_yr'   : week_yr,
            'employees' : employees,
            'wk_hrs'    : wk_hrs,
            'table'     : table,
        }
        return render(request, 'sch/week/week.html', context)

    def weekFillTemplates(request,year, week):
        days = Workday.objects.filter(date__year=year, iweek=week)
        for day in days:
            WorkdayActions.fillDailySST(day)
        return HttpResponseRedirect(f'/sch/week/{year}/{week}/')

class EmployeeDetailView (DetailView):

    model           = Employee
    template_name   = 'sch2/employee.html'    
    
    def get_object(self):
        return Employee.objects.get(name=self.kwargs['name'])

    def get_context_data(self, **kwargs):
        context             = super().get_context_data(**kwargs)
        context['employee'] = self.object  # type: ignore
        context['slots']    = Slot.objects.filter(employee=self.object)   # type: ignore
        context['shifts']   = self.object.shifts_trained.all()  # type: ignore
        context['next7']    = Workday.objects.filter(date__gte=dt.date.today())[:7]
        context['ptoTable'] = PtoListTable(PtoRequest.objects.filter(employee=self.object))
        # use templateTags to get the next 7 days : 
        #                     EMPL_GETSHIFT(wd,empl)
        return context



def slotAdd (request, date, shift):
    if request.method == 'POST':
        form = SlotForm(request.POST)
        if form.is_valid():
            employee = form.cleaned_data['employee']
            workday  = Workday.objects.get(slug=date)
            shift    = Shift.objects.get(name=shift)
            slot = Slot.objects.create(workday=workday, shift=shift,employee=employee)
            slot.save()
            return HttpResponseRedirect(f'/sch2/day/{workday.slug}/')
    workday = Workday.objects.get(date=date)
    shift   = Shift.objects.get(name=shift)

    employees_available = Employee.objects.filter(shifts_available=shift)

    othershifts = Shift.objects.exclude(name=shift)
    empls_on_day = Slot.objects.filter(workday=workday, shift__in=othershifts).values('employee')
    employees_on_day = Employee.objects.filter(pk__in=empls_on_day)

    employees = employees_available.exclude(pk__in=employees_on_day)

    if shift.start < dt.time(12,0):
        if Workday.objects.filter(date=workday.date - dt.timedelta(days=1)).exists():
            daybefore = Workday.objects.get(date=workday.date - dt.timedelta(days=1))
            empls_on_dayb = Slot.objects.filter(workday=daybefore, shift__start__gte=dt.time(12,0)).values('employee')
            employees = employees.exclude(pk__in=empls_on_dayb)
    
    if shift.start > dt.time(12,0):
        if Workday.objects.filter(date=workday.date + dt.timedelta(days=1)).exists():
            dayafter = Workday.objects.get(date=workday.date + dt.timedelta(days=1))
            empls_on_daya = Slot.objects.filter(workday=dayafter, shift__start__lte=dt.time(12,0)).values('employee')
            employees = employees.exclude(pk__in=empls_on_daya)

    week_num = workday.iweek
    week_yr  = workday.date.year
    employees_hrs_available = employees.annotate(weekly_hours=Sum(F('slot__shift__duration')-dt.timedelta(minutes=30), filter=Q(slot__workday__iweek=week_num, slot__workday__date__year=week_yr)))
    print(employees_hrs_available.values('name','weekly_hours'))
    employees_no_hrs_avaliable = employees_hrs_available.filter(weekly_hours__gt=(dt.timedelta(hours=40)-shift.duration + dt.timedelta(minutes=30))) 
    
    employees = employees.exclude(pk__in=employees_no_hrs_avaliable)

    context = {
        'workday':   workday,
        'shift':     shift,
        'employees': employees,
    }
    return render(request, 'sch2/slot/slotAdd.html', context)
  
def slotAdd_post (request, workday, shift):
    if request.method == 'POST':
        form = SlotForm(request.POST)
        if form.is_valid():
            employee = form.cleaned_data['employee']
            slot = Slot.objects.create(workday=WorkdayManager.slug, shift=shift,employee=employee)  # type: ignore
            slot.save()
            return HttpResponseRedirect(f'/sch2/day/{workday.slug}/')
    else:
        return HttpResponse('Error: Not a POST request')

def slot(request, date, shift):
    if Slot.objects.filter(workday__slug=date, shift__name=shift).exists():
        slot = Slot.objects.get(workday__slug=date, shift__name=shift)
        context = {
            'slot': slot,
        }
        return render(request, 'sch2/slot.html', context)
    else:
        wd = Workday.objects.get(slug=date)
        context = {
            'wd': wd,
            'shift': Shift.objects.get(name=shift),
            'wdURL': wd.get_absolute_url(),
            'fillURL': f'/sch2/day/{date}/{shift}/add/',
        }
        return render(request, 'sch2/slot/noSlot.html', context)

def slotDelete(request, date, shift):
    slot = Slot.objects.get(workday__slug=date, shift__name=shift)
    slot.delete()
    return HttpResponseRedirect(f'/sch2/day/{date}/')

class SHIFT :
    class ShiftDetailView (DetailView):
        model                = Shift
        template_name        = 'sch/shift/shift_detail.html'
        context_object_name  = 'shifts'

        def get_context_data(self, **kwargs):
            context                 = super().get_context_data(**kwargs)
            context['shift']        = self.object # type: ignore

            sstsA = [(day, ShiftTemplate.objects.filter(shift=self.object, ppd_id=day)) for day in range(7)] # type: ignore
            context['sstsA'] = sstsA
            sstsB = [(day, ShiftTemplate.objects.filter(shift=self.object, ppd_id=day)) for day in range(7,14)] # type: ignore
            context['sstsB'] = sstsB

            ssts = {day: ShiftTemplate.objects.filter(shift=self.object, ppd_id=day) for day in range(14)} # type: ignore
            return context

        def get_object(self):
            return Shift.objects.get(name=self.kwargs['name'])

    class ShiftListView (ListView):
        model           = Shift
        template_name   = 'sch/shift/shift_list.html'

        def get_context_data(self, **kwargs):
            context               = super().get_context_data(**kwargs)
            context['shifts']     = Shift.objects.all()
            shiftTable            = ShiftListTable(Shift.objects.all())
            context['shiftTable'] = shiftTable

            return context

    class ShiftCreateView (FormView):
        template_name   = 'sch/shift/shift_form.html'
        form_class      = ShiftForm
        fields          = ['name', 'start', 'duration','occur_days']
        success_url     = '/sch/shifts/all/'

        def form_valid(self, form):
            form.save() # type: ignore
            return super().form_valid(form)
        
    class ShiftUpdateView (UpdateView):
        model           = Shift
        template_name   = 'sch/shift/shift_form_edit.html'
        fields          = ['start','duration','occur_days']
        success_url     = '/sch/shifts/all/'

        def get_object(self):
            return Shift.objects.get(name=self.kwargs['name'])
    
    class ShiftDeleteView (DeleteView):
        model           = Shift
        success_url     = reverse_lazy('shift-list')
    
    class ShiftTemplateView (FormView):
        template_name = 'sch/shift/shift_sst_form.html'
        form_class = SSTForm
        fields = ['ppd_id', 'employee']
        success_url = '/sch/shifts/all/'
        
        def get_context_data(self, **kwargs):
            context = super().get_context_data(**kwargs)
            context['template_slots'] = ShiftTemplate.objects.filter(shift__name=self.kwargs['name'])
            context['shift'] = Shift.objects.get(name=self.kwargs['name'])
            return context

        def get_queryset (self):
            return ShiftTemplate.objects.filter(shift__name=self.kwargs['name'])

class EMPLOYEE:
    class EmployeeListView (ListView):
        model           = Employee
        template_name   = 'sch/employee/employee_list.html'

        def get_context_data(self, **kwargs):
            context                  = super().get_context_data(**kwargs)
            context['employees']     = Employee.objects.all()
            context['employeeTable'] = EmployeeTable(Employee.objects.all())
            return context

    class EmployeeCreateView (FormView):
        template_name   = 'sch/employee/employee_form.html'
        form_class      = EmployeeForm
        fields          = ['name', 'fte_14_day', 'shifts_trained', 'shifts_available', 'streak_pref']
        success_url     = '/sch/employees/all/'

        def form_valid(self, form):
            form.save() # type: ignore
            return super().form_valid(form)

    class EmployeeDetailView (DetailView):
        model               = Employee
        template_name       = 'sch/employee/employee_detail.html'
        context_object_name = 'employees'

        def get_context_data(self, **kwargs):
            context                 = super().get_context_data(**kwargs)
            context['employee']     = self.object # type: ignore
            context['sfts_trained'] = self.object.shifts_trained.all() # type: ignore
            context['sfts_avail']   = self.object.shifts_available.all() # type: ignore
            context['ppdays']       = range(14)
            context['ssts']         = ShiftTemplate.objects.filter(employee=self.object) 
            context['sstHours']     = context['ssts'].aggregate(Sum('shift__hours'))['shift__hours__sum']
            context['SSTGrid']      = [(day, ShiftTemplate.objects.filter(employee=self.object, ppd_id=day)) for day in range(14)] # type: ignore    
            context['ptoTable']     = PtoListTable(PtoRequest.objects.filter(employee=self.object)) 
            return context

        def get_object(self):
            return Employee.objects.get(name=self.kwargs['name'])

        def employeeSstGrid (employee):
            ssts = ShiftTemplate.objects.filter(employee=employee)
            sstsA = [(day, ssts.filter(ppd_id=day)) for day in range(7)]
            sstsB = [(day, ssts.filter(ppd_id=day)) for day in range(7,14)]
            return (sstsA, sstsB)

    class EmployeeUpdateView (UpdateView):
        model           = Employee
        template_name   = 'sch/employee/employee_form_edit.html'
        form_class      = EmployeeEditForm
        success_url     = '/sch/employees/all/'

        def get_object(self):
            return Employee.objects.get(name=self.kwargs['name'])

    class EmployeeSstsView (FormView):
        template_name = 'sch/employee/employee_ssts_form.html'
        form_class = SstEmployeeForm
        success_url = '/sch/employees/all/'
        
        def get_context_data(self, **kwargs):
            context = super().get_context_data(**kwargs)

            context['template_slots'] = ShiftTemplate.objects.filter(employee__name=self.kwargs['name'])
            formset = formset_factory(SstEmployeeForm, extra=0)
            formset = formset(initial=[{'ppd_id': i,'employee':employee} for i in range(14)])
            employee = Employee.objects.get(name=self.kwargs['name'])
            context['employee'] = employee
            empl_ssts = ShiftTemplate.objects.filter(employee=employee)
            context['formset'] = formset
            return context

    class EmployeeAddPtoView (FormView):

        template_name = 'sch/employee/employee_add_pto.html'
        form_class = PTOForm
        fields      = ['employee', 'workday','dateCreated', 'status']
        success_url = '/sch/employees/all/'
        
        def get_context_data(self, **kwargs):
            context = super().get_context_data(**kwargs)
            context['employee'] = Employee.objects.get(name=self.kwargs['name'])
            context['form'].fields['employee'].initial = Employee.objects.get(name=self.kwargs['name'])
            return context

        def form_valid(self, form):
            form.save()
            return super().form_valid(form)

    class EmployeeAddPtoRangeView (FormView):

        template_name = 'sch/employee/employee_add_pto.html'
        form_class    = PTORangeForm
        success_url   = '/sch/employees/all/'

        def get_context_data(self, **kwargs):
            context = super().get_context_data(**kwargs)
            context['employee'] = Employee.objects.get(name=self.kwargs['name'])
            context['form'].fields['employee'].initial = Employee.objects.get(name=self.kwargs['name'])
            return context

        def form_valid(self, form):
            # valid if date_from <= date_to
            if form.cleaned_data['date_from'] <= form.cleaned_data['date_to']:
                return super().form_valid(form)
            else:
                return self.form_invalid(form)
        
        def form_invalid(self, form):
            return super().form_invalid(form)

        def post (self, request, *args, **kwargs):
            form = self.get_form()
            if form.is_valid():
                date = form.cleaned_data['date_from']
                end = form.cleaned_data['date_to']
                employee = form.cleaned_data['employee']
                while date <= end:
                    obj = PtoRequest.objects.create(employee=employee, workday=date, dateCreated=date, status='P')
                    obj.save()
                    date += dt.timedelta(days=1)                
                return self.form_valid(form)
            else:
                return self.form_invalid(form)

class SLOT:

    def create_slot (request, date, shift):

        if request.method == 'POST':
            form = SlotForm(request.POST)
            if form.is_valid():
                form.save()
                return redirect('/sch/slots/all/')
        else:
            initial = {'workday': date, 'shift': shift}
            form    = SlotForm(initial=initial)

        return render(
            request, 'sch/slot/slot_form.html', {
                'form': form, 
                'date': date, 
                'shift': shift
                })  

    class SlotCreateView (FormView):

        template_name   = 'sch/slot/slot_form.html'
        form_class      = SlotForm

        def form_valid(self, form):
            form.save()
            return super().form_valid(form)

        def get_context_data(self, **kwargs):
            context          = super().get_context_data(**kwargs)
            context['date']  = self.kwargs['date']
            context['shift'] = self.kwargs['shift']
            return context

        def get_initial(self):
            return {'workday': self.kwargs['date'], 'shift': self.kwargs['shift']}

        def get_success_url(self):
            return reverse_lazy('workday', kwargs={'slug': self.kwargs['date']})

    class SlotDetailView (DetailView):
        model               = Slot
        template_name       = 'sch/slot/slot_detail.html'
        context_object_name = 'slots'

        def get_context_data(self, **kwargs):
            context                 = super().get_context_data(**kwargs)
            context['slot']         = self.object # type: ignore
            context['shifts']       = self.object.shifts.all() # type: ignore
            return context

        def get_object(self):
            return Slot.objects.get(name=self.kwargs['name'])


def EmpSSTView (request, name):
    context                  = {}
    employee                 = Employee.objects.get(name=name)
    context['employee']      = employee
    context['dayrange']      = range(14)
    context['wd']            = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat']
    on_days = range(14)
    TmpSlotFormSet = formset_factory(SstEmployeeForm, extra=0)

    
    if request.method == 'POST':
        TmpSlotFormSet = formset_factory(SstEmployeeForm)
        formset = TmpSlotFormSet(request.POST)
        for form in formset:
            if form.is_valid():
                # Only create new SSTs on non empty forms
                if form.cleaned_data['shift'] != None:
                    shift = form.cleaned_data['shift']
                    ppd_id  = form.cleaned_data['ppd_id']
                    employee = form.cleaned_data['employee']
                    if ShiftTemplate.objects.filter(employee=employee, ppd_id=ppd_id).exists():
                        sst = ShiftTemplate.objects.get(employee=employee, ppd_id=ppd_id)
                        sst.shift = shift
                        sst.save()
                    else:
                        sst = ShiftTemplate.objects.create(ppd_id=ppd_id,shift=shift, employee=employee)
                        sst.save()
                # Delete SSTs on empty forms (if they changed)
                else:
                    ppd_id  = form.cleaned_data['ppd_id']
                    if ShiftTemplate.objects.filter(employee=employee, ppd_id=ppd_id).exists():
                        sst = ShiftTemplate.objects.get(employee=employee, ppd_id=ppd_id)
                        sst.delete()
            else:
                print(form.errors)
                    
        return HttpResponseRedirect(f'/sch/employee/{employee.name}/')

    initData = [
        {'ppd_id': i, 'employee': employee } for i in on_days
        ]

    formset = TmpSlotFormSet(initial=initData)

    context = {
        'employee': Employee.objects.get(name=employee), # type: ignore
        'formset': formset,
        'idata': initData,

    }
    return render(request, 'sch/employee/employee_ssts_form.html', context)

class SST:
    class sstUpdateView (UpdateView):
        model           = ShiftTemplate
        template_name   = 'sch/sst/sst_form_edit.html'
        fields          = ['shift','ppd_id','employee']
        success_url     = '/sch/shifts/all/'

        def get_context_data(self, **kwargs):
            context = super().get_context_data(**kwargs) 

        def get_queryset(self):
            return ShiftTemplate.objects.filter(shift=self.kwargs['name'])



def shiftTemplate (request, shift):
    context               = {}
    shift                 = Shift.objects.get(name=shift)
    context['shift']      = shift
    context['dayrange']   = range(14)
    context['wd']         = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat']
    on_days = shift.ppd_ids 
    TmpSlotFormSet = formset_factory(SstForm, extra=0)

    
    if request.method == 'POST':
        TmpSlotFormSet = formset_factory(SstForm)
        formset = TmpSlotFormSet(request.POST)
        for form in formset:
            if form.is_valid():
                if form.cleaned_data['employee'] != None:
                    employee = form.cleaned_data['employee']
                    ppd_id  = form.cleaned_data['ppd_id']
                    if ShiftTemplate.objects.filter(shift=shift, ppd_id=ppd_id).exists():
                        sst = ShiftTemplate.objects.get(shift=shift, ppd_id=ppd_id)
                        sst.employee = employee
                        sst.save()
                    else:
                        sst = ShiftTemplate.objects.create(ppd_id=ppd_id,shift=shift, employee=employee)
                        sst.save()
            else:
                print(form.errors)
                    
        return HttpResponseRedirect(f'/sch/shift/{shift.name}/')

    initData = [
        {'ppd_id': i, 'shift': shift } for i in on_days
        ]

    formset = TmpSlotFormSet(initial=initData)

    context = {
        'shift': Shift.objects.get(name=shift),
        'employees': Employee.objects.trained_for(shift), # type: ignore
        'formset': formset,
        'idata': initData,

    }
    return render(request, 'sch/shift/shift_sst_form.html', context)