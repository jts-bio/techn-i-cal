from xml.sax.handler import DTDHandler
from django.shortcuts import render, HttpResponse, HttpResponseRedirect, redirect, render
from django.db.models import query, IntegerField, Count
from django.urls import reverse_lazy
from django.views.generic.detail import DetailView
from django.views.generic.list import ListView
from django.views.generic.edit import CreateView, UpdateView, DeleteView, FormView
from django.forms import formset_factory

from .models import (
    PtoRequest, Shift, Employee, ShiftPreference, Workday, Slot, 
    PtoRequest, ShiftManager, ShiftTemplate, 
    WorkdayManager
)

from .forms import (
    SlotForm, SlotPriorityForm, SstForm, 
    ShiftForm, EmployeeForm, EmployeeEditForm, 
    BulkWorkdayForm, SSTForm, SstEmployeeForm, 
    PTOForm, PTORangeForm, EmployeeScheduleForm,
    PtoResolveForm, PTODayForm, ClearWeekSlotsForm,
    EmployeeShiftPreferencesForm, EmployeeShiftPreferencesFormset
)

from .actions import PayPeriodActions, ScheduleBot, WorkdayActions

from .tables import (
    EmployeeTable, PtoRequestTable, ShiftListTable, ShiftsWorkdayTable, 
    ShiftsWorkdaySmallTable, WeeklyHoursTable, WorkdayListTable, 
    PtoRequestTable, PtoListTable
)

from django.db.models import Q, F, Sum, Subquery, OuterRef, DurationField, ExpressionWrapper, Count

from django_tables2 import tables

import datetime as dt
import random


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
            context['n_turnarounds'] = Slot.objects.turnarounds().count()
            for obj in context['workdays']:
                if obj.percFilled != 1:
                    context['firstUnfilledShift'] = obj
                    context['firstUnfillednDays'] = (obj.date - dt.date.today()).days
                    break
            return context

        def get_queryset(self):
            return Workday.objects.filter(date__gte=dt.date.today()).order_by('date')

    class WorkDayDetailView (DetailView):

        model           = Workday
        template_name   = 'sch/workday/workday_detail.html'

        def get_context_data(self, **kwargs):
            context             = super().get_context_data(**kwargs)
            context['wd']       = self.object  
            context['slug']     = self.object.slug
            context['today']    = dt.date.today()
            shifts              = Shift.objects.on_weekday(weekday=self.object.iweekday)   # type: ignore
            slots               = Slot.objects.filter(workday=self.object)
            for slot in slots:
                slot.save()
            shifts              = shifts.annotate(assign=Subquery(slots.filter(shift=OuterRef('pk')).values('employee')))
            shifts              = shifts.annotate(assignment=Subquery(slots.filter(shift=OuterRef('pk')).values('employee__name')))
            # annotate shifts with whether that slot is a turnaround
            shifts              = shifts.annotate(
                is_turnaround=Subquery(slots.filter(shift=OuterRef('pk')).values('is_turnaround'))).annotate(
                    prefScore=Subquery(ShiftPreference.objects.filter(shift=OuterRef('pk'), employee=OuterRef('assign')).values('score'))
                )
            context['shifts']   = shifts
            try: 
                context['overallSftPref'] = int(shifts.aggregate(Sum(F('prefScore')))['prefScore__sum'] /(2 * len(slots)) *100)
            except:
                context['overallSftPref'] = 0
            
            context['sameWeek'] = Workday.objects.same_week(self.object)  # type: ignore
            #weeklyHours        = [(empl, Slot.objects.empls_weekly_hours(year, week, empl)) for empl in Employee.objects.all()]
            unfilled            = Shift.objects.filter(occur_days__contains=self.object.iweekday).exclude(pk__in=slots.values('shift'))
            # ANNOTATION FOR # OF TECHS WHO COULD FILL SHIFTS SLOT 
            for sft in unfilled:
                sft.n_can_fill  = Employee.objects.can_fill_shift_on_day(shift=sft, workday=self.object).values('pk').count()
            context['unfilled'] = unfilled

            context['ptoReqs']  = PtoRequest.objects.filter(workday=self.object.date, status__in=['P','A']).values('employee__name')
            ptoReqs             = Employee.objects.filter(name__in=context['ptoReqs'])
            slottedEmployees    = Employee.objects.filter(pk__in=slots.values('employee'))
            badPtoReqs          = slottedEmployees & ptoReqs
            context['badPtoReqs'] = badPtoReqs
            context['ptoForm']  = PTODayForm()
            
            # Context = wd, shifts, sameWeek, slots, slotdeet
            return context
        
        def get_object(self):
            return Workday.objects.get(slug=self.kwargs['slug'])

    class WorkdayPtoRequest (FormView):
        form_class = PTODayForm
        template_name = 'sch/workday/ptoRequest.html'
        
        def get_success_url (self):
            return reverse_lazy('workday', kwargs={'slug': self.kwargs['date']})
        
        def get_context_data(self, **kwargs):
            context = super().get_context_data(**kwargs)
            context['date'] = Workday.objects.get(slug=self.kwargs['date']).date
            context['form'] = PTODayForm(initial={'workday': context['date']})
            return context

        def form_valid(self, form):
            workday = form.cleaned_data['workday']
            employee = form.cleaned_data['employee']
            req = PtoRequest.objects.create( workday=workday,employee=employee,status='P')
            req.save()
            return super().form_valid(form)

    class WorkdayBulkCreateView (FormView):
        template_name = 'sch/workday/bulk_create.html'
        form_class = BulkWorkdayForm
        success_url = reverse_lazy('workday-list')

        def form_valid(self, form):
            date_from = form.cleaned_data['date_from']
            date_to = form.cleaned_data['date_to']
            WorkdayActions.bulk_create(date_from, date_to) # type: ignore
            return super().form_valid(form)

    class ResolvePtoRequestFormView (FormView):
        model = Slot
        template_name = 'sch/workday/resolve_pto_request.html'
        form_class = PtoResolveForm


        def get_context_data(self, **kwargs) :
            context = super().get_context_data(**kwargs)
            context['slot'] = Slot.objects.get(workday__slug=self.kwargs['date'], employee__name=self.kwargs['employee'])
            context['ptoreq'] = PtoRequest.objects.get(workday=self.kwargs['date'], employee__name=self.kwargs['employee'])
            initial = {
                'slot': context['slot'],
                'ptoreq': context['ptoreq'],
            }
            context['form'] = PtoResolveForm(initial=initial)
            print(context['slot'], context['ptoreq'])
            return context

        def form_valid(self, form):
            slot = form.cleaned_data['slot']
            ptoreq = form.cleaned_data['ptoreq']
            action = form.cleaned_data['action']
            if action == 'es':
                slot.delete()
            elif action == 'rp':
                ptoreq.status = 'D'
                ptoreq.save()
            return super().form_valid(form)


        def get_success_url(self):
            return reverse_lazy('workday', kwargs={'slug': self.kwargs['date']})

    def runSwaps (request, date):
        workday = Workday.objects.get(slug=date)
        bestswap = ScheduleBot.best_swap(workday)
        if bestswap != None:
            ScheduleBot.perform_swap(*bestswap)
        return HttpResponseRedirect(reverse_lazy('workday', kwargs={'slug': date}))
    
def workdayFillTemplate(request, date):
    # URL : /sch2/day/<date>/fill/
    workday = Workday.objects.get(date=date)
    WorkdayActions.fillDailySST(workday)
    return HttpResponseRedirect(f'/sch/day/{date}/')



class PERIOD :
    def period_view (request, year, period):
        # URL : /sch2/period/<year>/<week>/
        workdays  = Workday.objects.filter(date__year=year, iperiod=period)
        slots     = Slot.objects.filter(workday__in=workdays)
        employees = PayPeriodActions.getPeriodFtePercents(year, period)
        
        weekA     = workdays.filter(ppd_id__lte=6)
        for day in weekA:
            day.percent_coverage = PayPeriodActions.getWorkdayPercentCoverage(day)
        weekB     = workdays.filter(ppd_id__gt=6)
        for day in weekB:
            day.percent_coverage = PayPeriodActions.getWorkdayPercentCoverage(day)
            
        context  = {
            'year'      : year,
            'period'    : period,
            'workdays'  : workdays,
            'slots'     : slots,
            'employees' : employees,
            'weekA'     : weekA,
            'weekB'     : weekB,
            'weekA_url' : f'/sch/week/{year}/{period*2}',
            'weekB_url' : f'/sch/week/{year}/{period*2+1}',
            'firstDay'  : workdays.first().slug,
            'lastDayPlusOne': workdays.last().nextWD().slug,
            }
        
        return render(request,'sch/pay-period/period.html', context)
    
    def periodPrefBreakdown (request, year, period):
        # URL : /sch2/period/<year>/<week>/prefs/
        workdays  = Workday.objects.filter(date__year=year, iperiod=period)
        slots     = Slot.objects.filter(workday__in=workdays)
        employees = Employee.objects.all()
        for employee in employees:
            scores = []
            emp_slots = slots.filter(employee=employee)
            for s in emp_slots:
                scores.append(s.prefScore)
            if len(scores) == 0:
                employee.score = "No Shifts..."
            else:
                employee.score = sum(scores) / len(scores)
        context  = {
            'year'      : year,
            'period'    : period,
            'workdays'  : workdays,
            'slots'     : slots,
            'employees' : employees,
            }
        return render(request,'sch/pay-period/prefs.html', context)
    
    def periodFillTemplates (request, year, period):
        # URL : /sch2/period/<year>/<week>/fill/
        workdays = Workday.objects.filter(date__year=year, iperiod=period)
        for workday in workdays:
            WorkdayActions.fillDailySST(workday)
        return HttpResponseRedirect(f'/sch/pay-period/{year}/{period}/')

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

            if week != 0: 
                context['nextWeek'] = week + 1
                context['prevWeek'] = week - 1

            context['hrsTable']   = [(empl, Slot.objects.empls_weekly_hours(year, week, empl)) for empl in Employee.objects.all()]
            
            for day in context['workdays']:
                                    day.table = self.render_day_table(day)
            total_unfilled = 0
            for day in self.object_list:
                total_unfilled += day.n_unfilled
            context['total_unfilled'] = total_unfilled
            
            context['pay_period'] = context['workdays'].first().iperiod
            
            context['pto_requests'] = PtoRequest.objects.filter( workday__week=week, status__in=['A','P'])
            
            context['dateFrom'] = context['workdays'].first().slug
            context['dateTo'] = context['workdays'].last().nextWD().slug

            return context

        def get_queryset(self):
            return Workday.objects.filter(date__year=self.kwargs['year'], iweek=self.kwargs['week']).order_by('date')

        def get_day_table(self, workday):
            shifts              = Shift.objects.on_weekday(weekday=workday.iweekday)   # type: ignore
            slots               = Slot.objects.filter(workday=workday)
            sftAnnot            = shifts.annotate(employee=Subquery(slots.filter(shift=OuterRef('pk')).values('employee__name')))
            # annotate if employee slot is turnaround
            sftAnnot            = sftAnnot.annotate(
                                    is_turnaround=Subquery(
                                        slots.filter(shift=OuterRef('pk'), 
                                        employee__name=OuterRef('employee')).values('is_turnaround')))
            sftAnnot            = sftAnnot.order_by('start','name','employee')
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

    def all_weeks_view(request):
        weeks = Workday.objects.filter(date__gte=dt.date.today()).values('date__year','iweek').distinct()
        context = {
            'weeks': weeks,
        }
        return render(request, 'sch/week/all_weeks.html', context)
    
    def solve_week_slots (request, year, week):
        fx = True
        while fx == True:
            fx = ScheduleBot.performSolvingFunctionOnce(year,week)
        
        # wds = Workday.objects.filter(date__year=year, iweek=week).order_by('date')
        # if len(wds) == 0:
        #     return HttpResponseRedirect(f'/sch/week/{year}/{week}/')
        # for day in wds:
        #     day.getshifts = Shift.objects.on_weekday(day.iweekday).exclude(slot__workday=day)
        #     day.slots     = Slot.objects.filter(workday=day)
        # # put the list into a list of occurences in the form (workday, shift, number of employees who could fill this slot)
        # unfilledSlots = [(day, shift, Employee.objects.can_fill_shift_on_day(shift=shift, workday=day).values('pk').count()) for day in wds for shift in day.getshifts]
        # # sort this list by the number of employees who could fill the slot
        # unfilledSlots.sort(key=lambda x: x[2])
        # if len(unfilledSlots) == 0:
        #     return HttpResponseRedirect(f'/sch/week/{year}/{week}/')
        
        # slot = unfilledSlots[0]
        # # for each slot, assign the employee who has the least number of other slots they could fill
        # day = slot[0]
        # shift = slot[1]
        # # pull out employees with no guaranteed hours
        # prn_empls = Employee.objects.filter(fte=0)
        # empl = Employee.objects.can_fill_shift_on_day(shift=shift, workday=day).annotate(n_slots=Count('slot')).order_by('n_slots')
        # incompat_empl = Slot.objects.incompatible_slots(workday=day,shift=shift).values('employee')
        # empl = empl.exclude(pk__in=incompat_empl)
        # empl = empl.exclude(pk__in=prn_empls)
        # if empl.count() == 0:
        #     return HttpResponseRedirect(f'/sch/week/{year}/{week}/')
        # rand = random.randint(0,int(empl.count()/2))
        # empl = empl[rand]
        # Slot.objects.create(workday=day, shift=shift, employee=empl)
        return HttpResponseRedirect(f'/sch/week/{year}/{week}/')

    class ClearWeekSlotsView (FormView):
        template_name = 'sch/week/clear_slots_form.html'
        form_class    = ClearWeekSlotsForm
        
        def get_context_data (self, **kwargs):
            context = super().get_context_data(**kwargs)
            context['title'] = 'Clear Slots'
            context['year']  = self.kwargs['year']
            context['week']  = self.kwargs['week']
            return context
    
        def form_valid(self, form):
            if form.cleaned_data['confirm']:
                Slot.objects.filter(workday__date__year=self.kwargs['year'], workday__iweek=self.kwargs['week']).delete()
            return super().form_valid(form)
        
        def get_success_url (self):
            # return to the WeekView
            return reverse_lazy('week', kwargs={'year': self.kwargs['year'], 'week': self.kwargs['week']})
        

    class WeeklyUnfilledSlotsView (ListView):
        model = Workday
        template_name = 'sch/week/unfilled_slots.html'
        context_object_name = 'workdays'

        def get_context_data(self, **kwargs):
            context = super().get_context_data(**kwargs)
            context['title']      = 'Week'
            context['year_num']   = self.kwargs['year']
            year                  = self.kwargs['year']
            context['week_num']   = self.kwargs['week']
            week                  = self.kwargs['week']

            # for each day in the week, get the list of shifts that occur on that day, and no slot exists for that shift and day.
            for day in context['workdays']:
                day.getshifts = Shift.objects.on_weekday(day.iweekday).exclude(slot__workday=day)
                day.slots     = Slot.objects.filter(workday=day)
            # put the list into a list of occurences in the form (workday, shift, number of employees who could fill this slot)
            context['unfilled_slots'] = [(day, shift, Employee.objects.can_fill_shift_on_day(shift=shift, workday=day).values('pk').count()) for day in context['workdays'] for shift in day.getshifts]
            # sort this list by the number of employees who could fill the slot
            context['unfilled_slots'].sort(key=lambda x: x[2])
            if week != 0: 
                context['nextWeek'] = week + 1
                context['prevWeek'] = week - 1
            context['hrsTable']   = [(empl, Slot.objects.empls_weekly_hours(year, week, empl)) for empl in Employee.objects.all()]
            total_unfilled = 0
            for day in self.object_list:
                total_unfilled += day.n_unfilled
            context['total_unfilled'] = total_unfilled
            return context

        def get_queryset(self):
            return Workday.objects.filter(date__year=self.kwargs['year'], iweek=self.kwargs['week']).order_by('date')

        def get_day_table(self, workday):
            shifts              = Shift.objects.on_weekday(weekday=workday.iweekday)

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
            context ['ssts'] = sstsA + sstsB
            ssts = {day: ShiftTemplate.objects.filter(shift=self.object, ppd_id=day) for day in range(14)} # type: ignore
            
            context['prefs'] = ShiftPreference.objects.filter(shift=self.object).order_by('score') # type: ignore
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
        fields          = ['start','duration','occur_days','is_iv']
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
            context['ptoReqsExist'] = PtoRequest.objects.filter(employee=self.object).exists()
            initial = {
                'employee': self.object,
                'date_from': dt.date.today() - dt.timedelta(days=int(dt.date.today().strftime("%w"))),
                'date_to': dt.date.today() - dt.timedelta(days=int(dt.date.today().strftime("%w"))) + dt.timedelta(days=42)
            }
            context['ScheduleForm'] = EmployeeScheduleForm(initial=initial)

            return context

        def get_object(self):
            return Employee.objects.get(name=self.kwargs['name'])

        def employeeSstGrid (employee):
            ssts = ShiftTemplate.objects.filter(employee=employee)
            sstsA = [(day, ssts.filter(ppd_id=day)) for day in range(7)]
            sstsB = [(day, ssts.filter(ppd_id=day)) for day in range(7,14)]
            return (sstsA, sstsB)

        def form_valid(self, form):
            date_from = form.cleaned_data['date_from']
            date_to = form.cleaned_data['date_to']
            employee = form.cleaned_data['employee']
            return HttpResponseRedirect(reverse_lazy('employee-schedule', kwargs={'name': employee.name, 'date_from': date_from, 'date_to': date_to}))

    class EmployeeUpdateView (UpdateView):
        model           = Employee
        template_name   = 'sch/employee/employee_form_edit.html'
        form_class      = EmployeeEditForm
        success_url     = '/sch/employees/all/'

        def get_object(self):
            return Employee.objects.get(name=self.kwargs['name'])

    class EmployeeScheduleFormView (FormView):
        template_name   = 'sch/employee/schedule_form.html'
        form_class      = EmployeeScheduleForm
        fields          = ['employee', 'date_from', 'date_to']
        success_url     = '/sch/employees/all/'

        def form_valid(self, form):
            date_from = form.cleaned_data['date_from']
            date_to = form.cleaned_data['date_to']
            employee = form.cleaned_data['employee']
            return HttpResponseRedirect(reverse_lazy('employee-schedule', kwargs={'name': employee.name, 'date_from': date_from, 'date_to': date_to}))

        def get_context_data(self, **kwargs):
            context = super().get_context_data(**kwargs)
            employee = Employee.objects.get(name=self.kwargs['name'])
            date_from = dt.date.today() - dt.timedelta(days=int(dt.date.today().strftime("%w")))
            date_to   = date_from + dt.timedelta(days=42)
            context['form'] = EmployeeScheduleForm(initial={'employee': employee, 'date_from': date_from, 'date_to': date_to})
            context['employee'] = employee
            return context

    class EmployeeScheduleView (ListView):
        model           = Slot 
        template_name   = 'sch/employee/schedule.html'

        def get_context_data(self, **kwargs):
            context = super().get_context_data(**kwargs)
            employee = Employee.objects.get(name=self.kwargs['name'])
            date_from = dt.datetime.strptime(self.kwargs['date_from'], '%Y-%m-%d').date()
            date_to   = dt.datetime.strptime(self.kwargs['date_to'], '%Y-%m-%d').date()
            context['employee'] = employee
            context['date_from'] = date_from
            context['date_to'] = date_to
            slots = Slot.objects.filter(employee=employee, workday__date__gte=date_from, workday__date__lte=date_to)
            ptoReqs = PtoRequest.objects.filter(employee=employee)
            
            days = [{
                'date':i.strftime("%Y-%m-%d"),
                'slot':slots.filter(workday__date=i).first(),
                'ptoReq':ptoReqs.filter(workday=i).first()
                } for i in (date_from + dt.timedelta(n) for n in range((date_to-date_from).days))]
            context['days'] = days
            return context
        
    class EmployeeShiftPreferencesFormView (FormView):
        
        form_class = EmployeeShiftPreferencesForm
        template_name = 'sch/employee/shift_preferences_form.html'
        
        def get_context_data(self, **kwargs):
            context = super().get_context_data(**kwargs)
            employee = Employee.objects.get(name=self.kwargs['name'])
            shifts = employee.shifts_trained
            shifts = Shift.objects.filter(pk__in=shifts.all().values_list('id'))
            formset = formset_factory(EmployeeShiftPreferencesForm, extra=0)
            formset = formset(initial=[{'shift':shift,'employee':employee} for shift in shifts]) # type: ignore
            context['formset'] = formset
            context['employee'] = employee
            return context
        
        def form_valid(self, form):
            employee = form.cleaned_data['employee']
            shift = form.cleaned_data['shift']
            priority = form.cleaned_data['priority']
            if ShiftPreference.objects.filter(employee=employee, shift=shift).exists():
                shiftPreference = ShiftPreference.objects.get(employee=employee, shift=shift)
                shiftPreference.priority = priority
                shiftPreference.save()
            else:
                shiftPreference = ShiftPreference.objects.create(employee=employee, shift=shift, priority=priority)
                shiftPreference.save()
            form.save()
            return super().form_valid(form)
        
        def post (self, request, *args, **kwargs):
            form = self.get_form()
            if form.is_valid():
                return self.form_valid(form)
            print(request.POST)
            return HttpResponseRedirect(reverse_lazy('employee-detail', kwargs={'name': self.kwargs['name']}))
    
    def shift_preference_form_view (request, name):
        context = {}
        employee = Employee.objects.get(name=name)
        context['employee'] = employee
        prefFormset = formset_factory(EmployeeShiftPreferencesForm, extra=0)
        trainedFor = employee.shifts_trained.all()
        
        if request.method == "POST":
            print(request.POST)
            formset = prefFormset(request.POST)
            for form in formset:
                print(form)
                shift = form.cleaned_data['shift']
                priority = form.cleaned_data['priority']
                if ShiftPreference.objects.filter(employee=employee, shift=shift).exists():
                    shiftPreference = ShiftPreference.objects.get(employee=employee, shift=shift)
                    print(shiftPreference,"test")
                    shiftPreference.delete()
                    shiftPreference = ShiftPreference.objects.create(employee=employee, shift=shift, priority=priority)
                    shiftPreference.save()
                else:
                    shiftPreference = ShiftPreference.objects.create(employee=employee, shift=shift, priority=priority)
                    shiftPreference.save()
                    print(shiftPreference,'didntexist')
            return HttpResponseRedirect(reverse_lazy('employee-detail', kwargs={'name': name}))
        
        initData = [
            {'employee':employee, 'shift': s} for s in trainedFor
        ]
        for i in initData:
            if ShiftPreference.objects.filter(employee=employee, shift=i['shift']).exists():
                i['priority'] = ShiftPreference.objects.get(employee=employee, shift=i['shift']).priority
        
        formset = prefFormset(initial=initData) # type: ignore
        
        context['formset'] = formset
        context['emplPrefs'] = ShiftPreference.objects.filter(employee=employee)
        
        return render(request, 'sch/employee/shift_preferences_form.html', context)
        
    class EmployeeSstsView (FormView):
        """Display the 2 week template for a single employee,
        and allow new/del SSTs"""

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
            
    def employeeCoworkerView (request, name):
        employee    = Employee.objects.get(name=name)
        workdays    = Slot.objects.filter(employee=employee).values('workday')
        
        other_employees = Employee.objects.all().exclude(
            name=employee).annotate(
                count=Count('slot__workday', filter=Q(slot__workday__in=workdays))).order_by('-count')
        
        return render(request, 'sch/employee/coworkers.html', {'coworkers':other_employees, 'employee':employee})

    class EmployeeShiftTallyView (DetailView):
        model = Employee
        template_name = 'sch/employee/shift_tally.html'

        def get_context_data(self, **kwargs):
            context = super().get_context_data(**kwargs)
            context['employee'] = self.object
            # annotate Shifts with the count of slots the employee has worked with that shift
            context['shifts'] = Shift.objects.annotate(slot_count=Count('slot__employee', filter=Q(slot__employee=context['employee'])))
            return context
        
        def get_object(self):
            return Employee.objects.get(name=self.kwargs['name'])

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
            context['slots'] = Slot.objects.filter(workday__slug=self.kwargs['date'])
            return context

        def get_initial(self):
            return {
                'workday': self.kwargs['date'], 
                'shift':   self.kwargs['shift']
                }

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

    class SlotDeleteView (DeleteView):
        model         = Slot
        template_name = 'sch/slot/slot_confirm_delete.html'

        def get_object(self):
            return Slot.objects.get(workday__slug=self.kwargs['date'], shift__name=self.kwargs['shift'])

        def get_context_data(self, **kwargs):
            context = super().get_context_data(**kwargs)
            context['workday'] = self.object.workday
            context ['shift']  = self.object.shift
            context ['employee'] = self.object.employee
            return context
        
        def get_success_url(self):
            return reverse_lazy('workday', kwargs={'slug': self.object.workday.slug})

    class SlotTurnaroundsListView (ListView):
        template_name = 'sch/slot/turnarounds.html'
        context_object_name = 'slots'

        def get_queryset(self):
            for slot in Slot.objects.turnarounds():
                slot.save()
            return Slot.objects.turnarounds()


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
            context['employee'] = self.object.employee
            return context

        def get_queryset(self):
            return ShiftTemplate.objects.filter(shift__name=self.kwargs['shift'])

class PTO:

    def resolve_pto_request (request, date, employee):
        slot = Slot.objects.get(employee__name=employee, workday__slug=date)
        shift = slot.shift
        if request.method == 'POST':
            form = PtoResolveForm(request.POST)
            if form.is_valid():
                form.save()
                return reverse_lazy('workday', kwargs={'slug': date})
        else:
            initial = {'workday': date, 'shift': shift, 'employee': employee}
            form    = PtoResolveForm(initial=initial)

        return render(
            request, 'sch/workday/resolve_pto_request.html', {
                'form': form, 
                'date': date, 
                'shift': shift,
                'employee': employee
                })
    
    def CreatePtoRequestOnDayView (FormView):
        form_class = PTODayForm
        template_name = 'sch/pto/pto_day_form.html'
        
    class PtoManagerView (ListView):
        
        model               = PtoRequest
        template_name       = 'sch/pto/list.html'
        context_object_name = 'ptos'
        queryset            = PtoRequest.objects.all()
        
        def get_context_data(self, **kwargs):
            context = super().get_context_data(**kwargs) 
            context['table'] = PtoRequestTable(self.object_list)
            return context
        

        



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

    context.update({
        'shift': Shift.objects.get(name=shift),
        'employees': Employee.objects.trained_for(shift), # type: ignore
        'formset': formset})
    
    
    return render(request, 'sch/shift/shift_sst_form.html', context)
    
