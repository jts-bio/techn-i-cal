from django.shortcuts import render, HttpResponse, HttpResponseRedirect, redirect, render
from django.db.models import Count
from django.urls import reverse_lazy
from django.views.generic.detail import DetailView
from django.views.generic.list import ListView
from django.views.generic.edit import UpdateView, DeleteView, FormView
from django.forms import formset_factory
from django.contrib import messages


import itertools

from .models import *

from .forms import *

from .actions import PayPeriodActions, ScheduleBot, WorkdayActions, WeekActions, EmployeeBot

from .tables import *

from django.db.models import Q, F, Sum, Subquery, OuterRef, Count

from django_tables2 import RequestConfig

import datetime as dt


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

class DOCUMENTATION:
    def weekly (request):
        return render(request, 'sch/doc/week_functions.html')

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
    
    def periodFillTemplatesLanding (request,year,period):
        return render(request, 'sch/pay-period/fill_templates_landing.html', {'year':year, 'period':period})
    
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

            if week not in [0,1,52,53]:
                context['nextWeek'] = week + 1
                context['prevWeek'] = week - 1
                context['nextYear'] = year
                context['prevYear'] = year
            if week in [52,53]:
                context['nextWeek'] = 1
                context['prevWeek'] = 52
                context['nextYear'] = year + 1
                context['prevYear'] = year
            if week == 0:
                context['nextWeek'] = 2
                context['prevWeek'] = 52
                context['nextYear'] = year
                context['prevYear'] = year - 1
            if week == 1:
                context['nextWeek'] = 2
                context['prevWeek'] = 52
                context['nextYear'] = year
                context['prevYear'] = year - 1

            dates = Workday.objects.filter(date__year=year,iweek=week).values('date')
            context['hrsTable']   = [(
                empl, #0
                Slot.objects.empls_weekly_hours(year, week, empl), #1
                PtoRequest.objects.filter(workday__in=dates,employee=empl).count() #2
                ) for empl in Employee.objects.all()]
            
            weekprefScore = []
            
            for day in context['workdays']:
                                    day.table = self.render_day_table(day)
                                    pto = PtoRequest.objects.filter(workday=day.date,status__in=['A','P'])
                                    day.PTO = "-- ".join(pto.values_list('employee__name', flat=True))
                                    print("PTO:", day.PTO)
                                    day.nPTO = pto.count()
                                    prefScore = ScheduleBot.WdOverallShiftPrefScore(workday=day)
                                    day.prefScore = prefScore
                                    weekprefScore.append(prefScore)
                                    
            if len(weekprefScore) != 0:
                weekprefScore = sum(weekprefScore) / len(weekprefScore)
                context['weekprefScore'] = int(weekprefScore)
            else:
                context['weekprefScore'] = 0 
            
            total_unfilled = 0
            for day in self.object_list:
                total_unfilled += day.n_unfilled
            context['total_unfilled'] = total_unfilled
            context['pay_period']   = context['workdays'].first().iperiod
            context['pto_requests'] = PtoRequest.objects.filter( workday__week=week, status__in=['A','P'])
            context['dateFrom']     = context['workdays'].first().slug
            context['dateTo']       = context['workdays'].last().nextWD().slug
            
            
            ufs = self.get_unfavorables()
            # group ufs, currently {empl:count,empl:count..} as {count:[empl,empl...]} :
            context['unfavorables'] = {}
            for empl in ufs:
                if ufs[empl] in context['unfavorables']:
                    context['unfavorables'][ufs[empl]].append(empl)
                else:
                    context['unfavorables'][ufs[empl]] = [empl]
            # and sort it by decreasing count:
            context['unfavorables'] = {i:sorted(context['unfavorables'][i]) for i in sorted(context['unfavorables'], reverse=True)}
            

            return context

        def get_queryset(self):
            return Workday.objects.filter(date__year=self.kwargs['year'], iweek=self.kwargs['week']).order_by('date')

        def get_day_table(self, workday):
            shifts              = Shift.objects.on_weekday(weekday=workday.iweekday).order_by('cls')
            slots               = Slot.objects.filter(workday=workday)
            sftAnnot            = shifts.annotate(employee=Subquery(slots.filter(shift=OuterRef('pk')).values('employee__name')))
            # annotate if employee slot is turnaround
            sftAnnot            = sftAnnot.annotate(
                                    is_turnaround=Subquery(
                                        slots.filter(shift=OuterRef('pk'), 
                                        employee__name=OuterRef('employee')).values('is_turnaround')))
            sftAnnot            = sftAnnot.order_by('start','name','employee')
            return ShiftsWorkdaySmallTable(sftAnnot, order_by=("cls"))

        def render_day_table(self, workday):
            return self.get_day_table(workday).as_html(self.request)

        def get_hours_queryset (self, year, week):
            return Employee.objects.all().annotate(
                hours=Subquery(Slot.objects.filter(workday__date__year=year,workday__iweek=week, employee=F('pk')).aggregate(hours=Sum('hours')))
            )

        def get_unfavorables (self):
            nfs = tally(list(Slot.objects.filter(shift__start__hour__gte=10,workday__in=self.object_list).values_list('employee__name',flat=True)))
            return nfs

    class GET: 
        def empl_lowestHours (year,week):
            wds = Workday.objects.filter(date__year=year,iweek=week)
            emps = Employee.objects.all().exclude(fte=0)
            fteDict = {}
            ftes = emps.values('name','fte_14_day')
            for fte in ftes:
                fteDict.update({fte['name']:fte['fte_14_day']})
            workedHrs = {}
            for emp in emps:
                v = emp.weekly_hours(year,week)
                workedHrs.update({ emp.name :v })
            percWorked = {}
            for emp in ftes:
                if workedHrs[emp] != None:
                    percWorked.update({emp:workedHrs[emp]/fteDict[emp]})
            return percWorked
        
        def solvableUnfilledWeekSlots (self,year,iweek):
            wds = Workday.objects.filter(date__year=year,iweek=iweek)
            unsolved = [ wd.emptySlots for wd in wds ]
            for wd in unsolved:
                pass    # wd = [SlotMgr<S,S,S...> SlotMgr<S,S,S...>]
            
            return HttpResponse(slots,emps)
        
        def allEmplsWeeklyPercent (year,week):
            wds = Workday.objects.filter(date__year=year,iweek=week)
            emps = Employee.objects.all().exclude(fte=0)
            
            

    def weeklyHoursView (request):
        """View for a djangotables2 to show weeks in columns and employees in rows, with the employee weekly hours."""
        all_weeks = WeekActions.getAllWeekNumbers()
        table = EmployeeWeeklyHoursTable(Employee.objects.all())
        RequestConfig(request, paginate=True).configure(table) 
        context = {'table': table,
                    'weeks': all_weeks,}
        return render(request, 'sch/week/weekly-hours.html', context)
        
    def weekHoursTable (request,year,week):
        wds= Workday.objects.filter(date__year=year,iweek=week)
        empls = Employee.objects.all()
        for empl in empls:
            empl.week = [wds.filter(iweekday=i, slot__employee=empl).order_by('iweekday').values_list('slot__shift__name',flat=True) for i in range(7)]
        return render (request,'sch/week/week-hours-table.html', context={'empls': empls,'wds': wds, 'seven': range(7)})
             
    def weekFillTemplates(request,year, week):
        days = Workday.objects.filter(date__year=year, iweek=week)
        for day in days:
            WorkdayActions.fillDailySST(day)
        return HttpResponseRedirect(f'/sch/week/{year}/{week}/')

    def all_weeks_view(request):
        weeks = Workday.objects.filter(date__gte=dt.date.today()).values('date__year','iweek').distinct()
        for week in weeks:
            sums = []
            for day in Workday.objects.filter(date__year=week['date__year'],iweek=week['iweek']):
                sums += [day.percFilled]
            week['perc_filled'] = sum(sums)
        # weeks => List[int]
        weekTable = WeekListTable(weeks)
        slotCounts = []
        for week in weeks: 
            slotCounts.append(Slot.objects.filter(workday__date__year=week['date__year'],workday__iweek=week['iweek']).count())
        context = {
            'weeks' : list(zip(weeks,slotCounts)),
            'weekTable': weekTable,
        }
        
        return render(request, 'sch/week/all_weeks.html', context)
    
    def solve_week_slots (request, year, week):
        fx = True 
        n = 0
        while fx == True and n < 200 :
            fx = ScheduleBot.performSolvingFunctionOnce(year,week)
            n += 1
        return HttpResponseRedirect(f'/sch/week/{year}/{week}/')
    
    def make_preference_swaps (request, year, week):
        for empl in Employee.objects.all():
            print(empl.info_printWeek(year,week))
        workdays = Workday.objects.filter(date__year=year, iweek=week)
        for workday in workdays:
            i = 3
            while i > 0:
                bestswap = ScheduleBot.best_swap(workday)
                if bestswap != None:
                    ScheduleBot.perform_swap(*bestswap)
                    messages.success(request,f"[{bestswap[0].shift}] {bestswap[0].employee} swapped with [{bestswap[1].shift}] {bestswap[1].employee}")
                else:
                    i -= 1
        for empl in Employee.objects.all():
            print(empl.info_printWeek(year,week))
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
    
    def clearWeekSlots_LowPrefScoresOnly (request, year, week):
        # only switches slots that don't have the preferred employee
        WeekActions.delSlotsLowPrefScores(year,week)
        return HttpResponseRedirect(f'/sch/week/{year}/{week}/')
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
            context                  = super().get_context_data(**kwargs)
            context ['shift']        = self.object # type: ignore

            sstsA = [(day, ShiftTemplate.objects.filter(shift=self.object, ppd_id=day)) for day in range(7)] 
            context ['sstsA'] = sstsA
            sstsB = [(day, ShiftTemplate.objects.filter(shift=self.object, ppd_id=day)) for day in range(7,14)] 
            context ['sstsB'] = sstsB
            context ['ssts'] = sstsA + sstsB
            ssts  = {day: ShiftTemplate.objects.filter(shift=self.object, ppd_id=day) for day in range(14)}
            
            context ['prefs'] = ShiftPreference.objects.filter(shift=self.object).order_by('score') 
            context ['count'] = Employee.objects.filter(shifts_trained=self.object).count()
            return context

        def get_object(self):
            return Shift.objects.get(name=self.kwargs['name'])
        
    def shiftComingUpView (request, shift):
        context = {}
        shift   = Shift.objects.get(name=shift)
        context ['shift'] = shift 
        days    = Workday.objects.filter(date__gte=dt.date.today(),date__lt=dt.date.today()+dt.timedelta(days=28))
        context ['days'] = days.annotate(employee=Subquery(Slot.objects.filter(shift=shift,workday=OuterRef('pk')).values('employee__name')))
        
        return render(request,'sch/shift/upcoming.html',context=context)
        

    class ShiftListView (ListView):
        model           = Shift
        template_name   = 'sch/shift/shift_list.html'

        def get_context_data(self, **kwargs):
            context               = super().get_context_data(**kwargs)
            context['shifts']     = Shift.objects.all()
            shiftTable            = ShiftListTable(Shift.objects.all().order_by('start'))
            context['shiftTable'] = shiftTable

            return context

    class ShiftCreateView (FormView):
        template_name   = 'sch/shift/shift_form.html'
        form_class      = ShiftForm
        fields          = ['name', 'start', 'duration','occur_days', 'is_iv']
        success_url     = '/sch/shifts/all/'

        def form_valid(self, form):
            form.save() # type: ignore
            return super().form_valid(form)
        
    class ShiftUpdateView (UpdateView):
        model           = Shift
        template_name   = 'sch/shift/shift_form_edit.html'
        fields          = ['name','start','duration','occur_days','is_iv','cls']
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
    
    def shiftTalliesView (request, name):
        shift = Shift.objects.get(name=name)
        
        employees = Employee.objects.annotate(tally=Count('slot',filter=Q(slot__shift__name=shift)))
        context = {}
        context['shift'] = shift
        context['employees'] = employees 
        context['total'] = Slot.objects.filter(shift=shift).count()
        
        return render(request, 'sch/shift/tallies.html', context)
        
    def trainedShiftView(request, name):
        context = {}
        shift = Shift.objects.get(name=name)
        shiftClass = shift.cls
        context['shift'] = shift
        TrainedEmployeeShiftFormSet = formset_factory(TrainedEmployeeShiftForm, extra=0)
        
        if request.method == 'POST':
            formset = TrainedEmployeeShiftFormSet(request.POST)
            if formset.is_valid():
                for form in formset:
                    employee = form.cleaned_data.get('employee')
                    if form['is_trained'].value() == 'True':
                        if shift not in employee.shifts_trained:
                            employee.shifts_trained.add(shift)
                    if form['is_trained'].value() == 'False':
                        if shift in employee.shifts_trained:
                            employee.shifts_trained.remove(shift)
                            employee.save()
                    if form['is_available'].value() == 'True':
                        if shift not in employee.shifts_available:
                            employee.shifts_available.add(shift) 
                            employee.save()
                    if form['is_available'].value() == 'False':
                        if shift in employee.shifts_available:
                            employee.shifts_available.remove(shift)
                            employee.save()
                return HttpResponseRedirect(f'/sch/shift/{name}/')
            if formset.is_valid() == False:
                print(formset.errors)
        initData = [
            {
                'is_trained' : em.shifts_trained.filter(name=name).exists(),
                'is_available' : em.shifts_available.filter(name=name).exists(),
                'employee' : em,
                'shift' : shift,
            } for em in Employee.objects.filter(cls=shiftClass).order_by('name')
        ]
        formset = TrainedEmployeeShiftFormSet(initial=initData)
        context['formset'] = formset
        return render(request, 'sch/shift/trained_available_emps.html', context)
                        
class EMPLOYEE:
    
    
    class EmployeeListView (ListView):
        model           = Employee
        template_name   = 'sch/employee/employee_list.html'

        def get_context_data(self, **kwargs):
            context                  = super().get_context_data(**kwargs)
            context['employees']     = Employee.objects.all()
            context['employeeTable'] = EmployeeTable(Employee.objects.all().order_by('name'))
            context['allActive']     = "bg-yellow-700"
            return context
        
    class EmployeeListViewCpht (ListView):
        model           = Employee
        template_name   = 'sch/employee/employee_list.html'
        
        def get_context_data(self,**kwargs):
            context = super().get_context_data(**kwargs)
            context['employees']     = Employee.objects.filter(cls='CPhT')
            context['employeeTable'] = EmployeeTable(Employee.objects.filter(cls='CPhT').order_by('name'))
            context['cphtActive']    = "bg-yellow-700"
            return context
        
    class EmployeeListViewRph (ListView):
        model           = Employee
        template_name   = 'sch/employee/employee_list.html'
        
        def get_context_data(self,**kwargs):
            context = super().get_context_data(**kwargs)
            context['employees']     = Employee.objects.filter(cls='RPh')
            context['employeeTable'] = EmployeeTable(Employee.objects.filter(cls='RPh').order_by('name'))
            context['rphActive']     = "bg-yellow-700"
            return context
    

    ### CREATE
    class EmployeeCreateView (FormView):
        template_name   = 'sch/employee/employee_form.html'
        form_class      = EmployeeForm
        fields          = ['name', 'fte_14_day', 'shifts_trained', 'shifts_available', 'streak_pref', 'employee_class']
        success_url     = '/sch/employees/all/'

        def form_valid(self, form):
            form.save() # type: ignore
            return super().form_valid(form)

    ### DETAIL
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
            context['SSTGrid']      = [(day, 
                                        ShiftTemplate.objects.filter(employee=self.object, ppd_id=day), 
                                        TemplatedDayOff.objects.filter(employee=self.object, sd_id=day)) for day in range(42)] # type: ignore    
            context['ptoTable']     = PtoListTable(PtoRequest.objects.filter(employee=self.object)) 
            context['ptoReqsExist'] = PtoRequest.objects.filter(employee=self.object).exists()
            context['multiplesOf7m1'] = [i*7-1 for i in range(6) ]
            initial = {
                'employee': self.object,
                'date_from': dt.date.today() - dt.timedelta(days=int(dt.date.today().strftime("%w"))),
                'date_to': dt.date.today() - dt.timedelta(days=int(dt.date.today().strftime("%w"))) + dt.timedelta(days=42)
            }
            context['ScheduleForm'] = EmployeeScheduleForm(initial=initial)
            context['unfavorables'] = EmployeeBot.get_emplUpcomingUnfavorables(self.object.name)

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

    ### UPDATE
    class EmployeeUpdateView (UpdateView):
        model           = Employee
        template_name   = 'sch/employee/employee_form_edit.html'
        form_class      = EmployeeEditForm
        success_url     = '/sch/employees/all/'

        def get_object(self):
            return Employee.objects.get(name=self.kwargs['name'])

    ### SCH-FORM
    class EmployeeScheduleFormView (FormView):
        template_name   = 'sch/employee/schedule_form.html'
        form_class      = EmployeeScheduleForm
        fields          = ['employee', 'date_from', 'date_to']
        success_url     = '/sch/employees/all/'

        def form_valid(self, form):
            date_from = form.cleaned_data['date_from']
            date_to = form.cleaned_data['date_to']
            employee = form.cleaned_data['employee']
            return HttpResponseRedirect(f'{date_from.slug}/{date_to.slug}/')

        def get_context_data(self, **kwargs):
            context = super().get_context_data(**kwargs)
            employee = Employee.objects.get(name=self.kwargs['name'])
            date_from = Workday.objects.filter(iweekday=0, date__lt=dt.date.today()).latest('date')
            date_to   = Workday.objects.get(date=date_from.date + dt.timedelta(days=28))
            context['form'] = EmployeeScheduleForm(initial={'employee': employee, 'date_from': date_from, 'date_to': date_to})
            context['employee'] = employee
            return context

    ### SCHEDULE
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
    
    ### SHIFT-PREF-FORM
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
       
    ### TPL-DAY-OFF-BREAKDOWN 
    def tdoBreakdownView (request):
        context = {}
        context['days'] = tally(list(TemplatedDayOff.objects.all().values_list('ppd_id',flat=True)))
        return HttpResponse(context)
        
    ### SFT-SLOT-TMPL
    class EmployeeSstsView (FormView):
        """Display the 2 week template for a single employee,
        and allow new/del SSTs"""

        template_name = 'sch/employee/employee_ssts_form.html'
        form_class    = SstEmployeeForm
        success_url   = '/sch/employees/all/'
        
        def get_context_data(self, **kwargs):
            context = super().get_context_data(**kwargs)

            context['template_slots']     = ShiftTemplate.objects.filter(employee__name=self.kwargs['name'])
            context['templated_days_off'] = TemplatedDayOff.objects.filter(employee__name=self.kwargs['name'])
            formset = formset_factory(SstEmployeeForm, extra=0)
            
            initial = [{'sd_id': i,'employee':employee} for i in range(42)]
            
            formset    = formset (initial=initial)
            employee   = Employee.objects.get(name=self.kwargs['name'])
            context['employee'] = employee
            context['formset']  = formset
            return context
        
        def form_valid(self, form):
            form.save()
            return super().form_valid(form)
        
    def employeeSstsView (request, name):
        
        employee= Employee.objects.get(name=name)
        
        if request.method == 'POST':
                formset = formset_factory(SstEmployeeForm, extra=0)
                formset = formset(request.POST)
                
                if formset.is_valid():
                    for form in formset:
                        shift = form.cleaned_data['shift']
                        ppdid = form.cleaned_data['ppd_id']
                        employee = form.cleaned_data['employee']
                        if shift == None:
                            if ShiftTemplate.objects.filter(ppd_id=ppdid, employee=employee).exists():
                                sst = ShiftTemplate.objects.get(ppd_id=ppdid, employee=employee)
                                sst.delete()
                        if shift != None:
                            if ShiftTemplate.objects.filter(ppd_id=ppdid,employee=employee).exists():
                                pass
                            else:
                                sft = ShiftTemplate.objects.create(ppd_id=ppdid,employee=employee, shift=shift)
                                sft.save()
                            
                return HttpResponseRedirect(reverse_lazy('employee-detail', kwargs={'name': name}))
                
        context = {}
        context['employee'] = employee
        context['template_slots'] = ShiftTemplate.objects.filter(employee=employee)
        
        formset = formset_factory(SstEmployeeForm, extra=0)
        sts = [ShiftTemplate.objects.filter(employee=employee, ppd_id=i).exists() for i in range(42)]
        sts2 = []
        i = 0
        for s in sts:
            if s == True:
                sts2.append(ShiftTemplate.objects.get(ppd_id=i, employee=employee).shift)
                i += 1
            else:
                sts2.append(None)
                i += 1
        
        initial = [{'ppd_id': i,'employee':employee, 'shift': sts2[i]} for i in range(42)]
        
        formset    = formset (initial=initial)
        context['formset']  = formset
        return render(request, 'sch/employee/employee_ssts_form.html', context)
        
    def employeeTemplatedDaysOffView(request, name ):
        
            template_name = 'sch/employee/template_days_off.html'
            form_class = EmployeeTemplatedDaysOffForm
            success_url = '/sch/employees/all/'
            
            employee = Employee.objects.get(name=name)
            
            if request.method == "POST":
                formset = formset_factory(EmployeeTemplatedDaysOffForm,extra=0)
                formset = formset (request.POST)
                print('POST ')
                if formset.is_valid():
                    print('VALID')
                    for form in formset:
                        if form.cleaned_data.get('is_templated_off') == False:
                            print("hello!")
                            if TemplatedDayOff.objects.filter(employee=employee, sd_id=form.cleaned_data.get('sd_id')).exists():
                                tdo = TemplatedDayOff.objects.get(employee=employee, sd_id=form.cleaned_data.get('sd_id'))
                                tdo.delete()
                            else:
                                pass
                        elif form.cleaned_data.get('is_templated_off') == True:
                            if TemplatedDayOff.objects.filter(employee=employee, sd_id=form.cleaned_data.get('sd_id')).exists():
                                pass
                            else:
                                templated_day_off = TemplatedDayOff.objects.create(employee=employee, sd_id=form.cleaned_data.get('sd_id'))
                                templated_day_off.save()
                else:
                    print('NOT VALID')
                    print(formset.errors)
                        
                    return HttpResponseRedirect(reverse_lazy('employee-detail', kwargs={'name': name}))

            context = {}
            
            context['templated_days_off'] = TemplatedDayOff.objects.filter(employee__name=employee)
            context['employee'] = employee
            
            formset = formset_factory(EmployeeTemplatedDaysOffForm, extra=0)
            
            
            initial = [{'sd_id': i, 'employee': employee, 'is_templated_off': TemplatedDayOff.objects.filter(employee=employee,sd_id=i).exists()} for i in range(42)]
            
            formset = formset(initial=initial)
            context['formset'] = formset
            
            return render(request, template_name, context)       
    
    def employeeMatchCoworkerTdosView (request, name):
        form = EmployeeMatchCoworkerTdosForm()
        context = {}
        context['form']          = form
        employee        = Employee.objects.get(name=name)
        context['employee']      = employee
        template_name = 'sch/employee/match_tdos.html'
        if request.method == 'POST':
            form = EmployeeMatchCoworkerTdosForm(request.POST)
            if form.is_valid():
                employee = form.cleaned_data['employee']
                coworker = form.cleaned_data['coworker']
                oldtdos = TemplatedDayOff.objects.filter(employee=employee)
                for tdo in oldtdos:
                    tdo.delete()
                tdos = list(TemplatedDayOff.objects.filter(employee=coworker).values_list('sd_id',flat=True))
                for tdo in tdos:
                    t = TemplatedDayOff.objects.create(employee=employee,sd_id=tdo)
                    t.save()
            else :
                print(form.errors)
            return HttpResponseRedirect('/sch/employee/{}'.format(name))
        
        context['form'].initial = {'employee':employee}
        return render (request, template_name, context)
           
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
        
        return render(request, 'sch/employee/coworker.html', {'coworkers':other_employees, 'employee':employee})

    ### SHIFT TALLY
    class EmployeeShiftTallyView (DetailView):
        model = Employee
        template_name = 'sch/employee/shift_tally.html'

        def get_context_data(self, **kwargs):
            context = super().get_context_data(**kwargs)
            context['employee'] = self.object
            # annotate Shifts with the count of slots the employee has worked with that shift
            context['shifts'] = Shift.objects.annotate(slot_count=Count('slot__employee', filter=Q(slot__employee=context['employee'])))
            
            sd = ShiftPreference.objects.filter(employee=context['employee'], score=-2).values_list('shift', flat=True)
            d = ShiftPreference.objects.filter(employee=context['employee'], score=-1).values_list('shift', flat=True)
            n = ShiftPreference.objects.filter(employee=context['employee'], score=0).values_list('shift', flat=True)
            l = ShiftPreference.objects.filter(employee=context['employee'], score=1).values_list('shift', flat=True)
            sl = ShiftPreference.objects.filter(employee=context['employee'], score=2).values_list('shift', flat=True)
            context['stronglyDislike'] = Shift.objects.filter(id__in=sd).values('name')
            context['stronglyDislikeCount'] = Slot.objects.filter(employee=context['employee'], shift__name__in=context['stronglyDislike']).count()
            context['dislike'] = Shift.objects.filter(id__in=d).values('name')
            context['dislikeCount'] = Slot.objects.filter(employee=context['employee'], shift__name__in=context['dislike']).count()
            context['neutral'] = Shift.objects.filter(id__in=n).values('name')
            context['neutralCount'] = Slot.objects.filter(employee=context['employee'], shift__name__in=context['neutral']).count()
            context['like'] = Shift.objects.filter(id__in=l).values('name')
            context['likeCount'] = Slot.objects.filter(employee=context['employee'], shift__name__in=context['like']).count()
            context['stronglyLike'] = Shift.objects.filter(id__in=sl).values('name')
            context['stronglyLikeCount'] = Slot.objects.filter(employee=context['employee'], shift__name__in=context['stronglyLike']).count()
            
            return context
            
        def get_object(self):
            return Employee.objects.get(name=self.kwargs['name'])
    
    def coWorkerSelectView (request, name):
        context = {}
        context['employee'] = Employee.objects.get(name=name)
        context ['employees'] = Employee.objects.all().order_by('cls')

        return render(request,'sch/employee/coworker-select.html',context)
        
     
    ### COWORKER
    def coWorkerView (request, nameA, nameB):
        emp1 = Employee.objects.get(name=nameA)
        emp2 = Employee.objects.get(name=nameB)
        
        emp1slots = Slot.objects.filter(employee=emp1).values('workday')
        emp1days  = Workday.objects.filter(pk__in=emp1slots)
        emp2days  = Slot.objects.filter(employee=emp2).values('workday')
        
        days = emp1days.filter(pk__in=emp2days).annotate(
            sft1=Subquery(Slot.objects.filter(employee=emp1,workday=OuterRef('pk')).values('shift__name'))).annotate(
                sft2=Subquery(Slot.objects.filter(employee=emp2,workday=OuterRef('pk')).values('shift__name')))
            
        return render(request, 'sch/employee/coworker.html', {'days':days,'emp1':emp1,'emp2':emp2})

class SLOT:
    class GET :
        def empl__weekbestFill (workday,shift):
            yr = workday.date.year 
            iweek = workday.iweek 
            employees = Employee.objects.can_fill_shift_on_day(shift,workday)
            data = {
                empl : empl.weekly_hours_perc (yr,iweek)
                for empl in employees 
                    }
            # return empl with the lowest week-percentage
            return min(data, key=data.get) if data else None
            

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
            wd               = Workday.objects.get(slug=self.kwargs['date'])
            context['date']  = wd
            week             = wd.iweek 
            year             = wd.date.year
            period           = wd.iperiod
            context['shift'] = Shift.objects.get(name=self.kwargs['shift'])
            context['slots'] = Slot.objects.filter(workday__slug=self.kwargs['date'])
            empls            = Employee.objects.can_fill_shift_on_day(
                                    shift=context['shift'], workday=context['date'], method="available") #.order_by(F('weeklyPercent').desc(nulls_last=True))
                                    
            for empl in empls:
                empl.weeklyHours = empl.weekly_hours(year,week)
                empl.weeklyPercent = empl.weekly_hours_perc(year,week)
                empl.periodHours = empl.period_hours(year,period)
                
            context['posEmpls'] = empls
            context['bestFill'] = SLOT.GET.empl__weekbestFill (wd,context['shift'])     
            
            return context
            
            
            
            return context

        def get_initial(self):
            return {
                'workday': self.kwargs['date'], 
                'shift':   self.kwargs['shift']
                }

        def get_success_url(self):
            return reverse_lazy('workday', kwargs={'slug': self.kwargs['date']})

    class SlotCreateView_OtOveride (FormView):
        
        template_name   = 'sch/slot/slot_form.html'
        form_class      = SlotForm
        
        def get_context_data(self, **kwargs):
            context = super().get_context_data(**kwargs)
            context['date']  = self.kwargs['date']
            context['shift'] = self.kwargs['shift']
            context['slots'] = Slot.objects.filter(workday__slug=self.kwargs['date'])
            return context
            

        def form_valid(self, form):
            form.save()
            return super().form_valid(form)

        def get_initial(self):
            return {
                'workday': self.kwargs['date'], 
                'shift':   self.kwargs['shift'],
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

    class SlotDeleteView (DeleteView)               : 
        model                                       = Slot
        template_name                               = 'sch/slot/slot_confirm_delete.html'

        def get_object(self)                        : 
            return Slot.objects.get(workday__slug   = self.kwargs['date'], shift__name=self.kwargs['shift'])

        def get_context_data(self, **kwargs):
            context                                 = super().get_context_data(**kwargs)
            context['workday']                      = self.object.workday
            context ['shift']                       = self.object.shift
            context ['employee']                    = self.object.employee
            return context
        
        def get_success_url(self)                   : 
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
    context['dayrange']      = range(42)
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
                    sd_id  = form.cleaned_data['sd_id']
                    employee = form.cleaned_data['employee']
                    if ShiftTemplate.objects.filter(employee=employee, sd_id=sd_id).exists():
                        sst = ShiftTemplate.objects.get(employee=employee, sd_id=sd_id)
                        sst.shift = shift
                        sst.save()
                    else:
                        sst = ShiftTemplate.objects.create(sd_id=sd_id,shift=shift, employee=employee)
                        sst.save()
                # Delete SSTs on empty forms (if they changed)
                else:
                    sd_id  = form.cleaned_data['sd_id']
                    if ShiftTemplate.objects.filter(employee=employee, sd_id=sd_id).exists():
                        sst = ShiftTemplate.objects.get(employee=employee, sd_id=sd_id)
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
            context ['employee'] = self.object.employee
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
        {'ppd_id': i, 
         'shift' : shift } 
        
                            for i in on_days
        ]

    formset = TmpSlotFormSet(initial=initData)

    context.update({
        'shift': Shift.objects.get(name=shift),
        'employees': Employee.objects.trained_for(shift), # type: ignore
        'formset': formset
        })
    
    return render(request, 'sch/shift/shift_sst_form.html', context)
    
class SCHEDULE:
    
    class FX:
        
        def getSlots (year,sch):
            wds = Workday.objects.filter(date__year=year, ischedule=sch)
            for wd in wds:
                wd.slots = wd.emptySlots 
    
    def scheduleView (request, year, sch):
        context = {}
        employees = Employee.objects.all().order_by('name')
        for empl in employees:
            schedule = Workday.objects.filter(date__year=year,ischedule=sch).annotate(
                emplShift=Subquery(Slot.objects.filter(employee=empl.pk, workday=OuterRef('pk')).values('shift__name')[:1])).annotate(
                    ptoReq=Subquery(PtoRequest.objects.filter(employee=empl.pk, workday=OuterRef('date')).values('employee__name')[:1])).annotate(
                    streakPref=Subquery(Employee.objects.filter(pk=empl.pk).values('streak_pref')[:1])).annotate(
                    streak=Subquery(Slot.objects.filter(employee=empl.pk, workday=OuterRef('pk')).values('streak')[:1])).values_list('iweekday','emplShift','streak','ptoReq','streakPref')
            
            empl.schedule = schedule
            
        context['employees'] = employees
        context['days'] = Workday.objects.filter(date__year=year,ischedule=sch)
        context['weekendlist'] = [0,6]
        context['unfavorables'] = ScheduleBot.get_unfavorables(year,sch)
        context['year'] = year
        context['sch'] = sch
        
        context['conflicted'] = SCHEDULE.tdosConflictedSlots(year,sch)
        te = 0
        tot = 0
        for wd in Workday.objects.filter(date__year=year,ischedule=sch):
            te += wd.emptySlots.count()
            tot += wd.filledSlots.count() + wd.emptySlots.count()
        context['percComplete'] = f'{int(100-round(te / tot, 2) * 100)}%'
        context['nEmpty'] = te
        context['tot'] = tot
        return render(request, 'sch/schedule/grid.html', context)
    
    def scheduleDelSlots (request, year, sch):
        slots = Slot.objects.filter(workday__date__year=year,workday__ischedule=sch)
        for slot in slots:
            slot.delete()
        context = {}
        employees = Employee.objects.all().order_by('name')
        for empl in employees:
            schedule = Workday.objects.filter(date__year=year,ischedule=sch).annotate(
                emplShift=Subquery(Slot.objects.filter(employee=empl.pk, workday=OuterRef('pk')).values('shift__name')[:1])).annotate(
                    ptoReq=Subquery(PtoRequest.objects.filter(employee=empl.pk, workday=OuterRef('date')).values('employee__name')[:1])).annotate(
                    streakPref=Subquery(Employee.objects.filter(pk=empl.pk).values('streak_pref')[:1])).annotate(
                    streak=Subquery(Slot.objects.filter(employee=empl.pk, workday=OuterRef('pk')).values('streak')[:1])).values_list('iweekday','emplShift','streak','ptoReq','streakPref')
            
            empl.schedule = schedule
            
        context['employees'] = employees
        context['days'] = Workday.objects.filter(date__year=year,ischedule=sch)
        context['weekendlist'] = [0,6]
        te = 0
        for wd in Workday.objects.filter(date__year=year,ischedule=sch):
            te += wd.emptySlots.count()
        context['totalEmpty'] = te
        return render(request,'sch/schedule/grid.html',context )
    
    def solveScheduleSlots (request,year,sch):
        ScheduleBot.solveSchedule(year,sch)
        for slot in SCHEDULE.tdosConflictedSlots(year,sch):
            slot.delete()
        for slot in Slot.objects.filter(workday__date__year=year,workday__ischedule=sch):
            slot.save()
        return HttpResponseRedirect(f'/sch/schedule/{year}/{sch}/')
    
    def solvePart2 (request,year,sch):
        emptySlots = []
        for day in Workday.objects.filter(date__year=year, ischedule=sch):
            for sft in day.emptySlots:
                emptySlots.append((day,sft))
        for slot in emptySlots:
            ScheduleBot.performSolvingFunctionOnce(slot)

    def tdosConflictedSlots (year, sch):
        tdos = TemplatedDayOff.objects.all().annotate(overlapped=Subquery(
            Slot.objects.filter(
                workday__date__year=year,
                workday__ischedule=sch,
                workday__sd_id=OuterRef('sd_id'),
                employee=OuterRef('employee')).values('pk')
        ))
        dic = {empl:[] for empl in Employee.objects.all()}
        tdos_notblank = []
        for tdo in tdos:
            if tdo.overlapped != None:
                s = Slot.objects.get(pk=tdo.overlapped)
                tdos_notblank.append(s)
        return tdos_notblank
    

class HTMX:
    def alertView (request, title, msg):
        return render(request, 'sch/doc/alert.html', context={'title': title, 'msg': msg})
    
    def spinner (request):
        return render(request, 'sch/test/spinner.html')
        
class TEST:
    
    def spinner (request):
        return render(request, 'sch/test/spinner.html')
    
    def possibleInterWeekSlotSwaps (request, workday, shift):
        context = {}
        slot = Slot.objects.get(workday__slug=workday,shift__name=shift)
        context['shift'] = slot.shift
        context['employee'] = slot.employee
        context['workday'] = slot.workday
        context['slot'] = slot
        
        allinWeek       = Slot.objects.filter(workday__date__year=slot.workday.date.year,workday__iweek=slot.workday.iweek)
        daysWorked      = allinWeek.filter(employee=slot.employee).values('workday')
        dropDaysWork    = allinWeek.exclude(workday__in=daysWorked)
        dropUntrained   = dropDaysWork.filter(shift__in=slot.employee.shifts_trained.all())
        empAslots       = allinWeek.filter(employee=slot.employee).values('workday')
        dropOnDaysWorked = dropUntrained.exclude(workday__in=empAslots)
        #conflicting are Slots that create turnaround interference with the potential trade
        allconflicting  = Slot.objects.none()
        for s in Slot.objects.filter(pk__in=empAslots):
            allconflicting = allconflicting & Slot.objects.incompatible_slots(workday=s.workday,shift=s.shift)
        dropConflicting = dropOnDaysWorked.exclude(pk__in=allconflicting)
        possible        = dropConflicting

        pos = []
        
        for possibleSlot in possible:
            # check to make sure employeeB is trained for the shift they would be swapping into
            if possibleSlot.employee.shifts_trained.contains(slot.shift):
                # dont include in possiblities if employeeB would be traded into a turnaround
                if Slot.objects.incompatible_slots(workday=slot.workday,shift=slot.shift).filter(employee=possibleSlot.employee).exists():
                    pass
                else:
                    pos.append(possibleSlot)
                    
        possibilities = []    
        for p in pos:
            if not ShiftTemplate.objects.filter(shift=p.shift,ppd_id=p.workday.ppd_id).exists():
                possibilities.append(p)
        
        
        context['possible'] = possibilities
        
        context['incompatible'] = Slot.objects.incompatible_slots(shift=slot.shift,workday=slot.workday)
        return render(request,'sch/test/is.html',context)
    
    def makeSwap (request,slotA,slotB):
        slot_a = Slot.objects.get(slug=slotA)
        slot_b = Slot.objects.get(slug=slotB)
        slotAEmpl = slot_a.employee
        slotAWD = slot_a.workday
        slotAShift = slot_a.shift
        slotBEmpl = slot_b.employee
        slotBWD = slot_b.workday
        slotBShift = slot_b.shift
        
        slot_a.delete()
        slot_b.delete()
        newA = Slot.objects.create(workday=slotAWD,shift=slotAShift,employee=slotBEmpl)
        newA.save()
        newB = Slot.objects.create(workday=slotBWD,shift=slotBShift,employee=slotAEmpl)
        newB.save()
        
        message = f"""
        [{newA.workday.weekday} {newA.shift}]-{newA.employee.name.capitalize()} 
        swapped with
        [{newB.workday.weekday} {newB.shift}]-{newB.employee.name.capitalize()}"""
        
        messages.success(request,message,"toast")
        
        return HttpResponseRedirect(f'/sch/week/{slotAWD.date.year}/{slotAWD.iweek}/')
    
    def allOkIntraWeekSwaps (request , workday, shift):
        """ALL OK INTRA-WEEK SWAPS
        ============================
        -> list [Slot]
        Get All the Slots that could be traded with this input slot with respect to training,
        and would NOT create any inappropraite turnarounds.
        """
        slot = Slot.objects.get(workday__slug=workday,shift__name=shift)
        empA = slot.employee    #type: Employee 
        shiftA = slot.shift     #type: Shift
        
        # potential slots employee A can swap into within this week
        potential = Slot.objects.filter(
            workday__iweek=slot.workday.iweek,
            workday__date__year=slot.workday.date.year,
            shift__in=empA.shifts_trained.all())
        
        # build list of employeeA currentSlots
        empA_weekslots = Slot.objects.filter(employee=empA, workday__iweek=slot.workday.iweek).exclude(workday=slot.workday)
        weekbeforeSat = (slot.workday.iweek_of).prevWD()
        weekafterSun = Slot.objects.filter(workday__date=weekbeforeSat.date+dt.timedelta(days=7),employee=empA)
        weekbeforeSat = Slot.objects.filter(workday=weekbeforeSat,employee=empA)
        empA_allslots = empA_weekslots & weekbeforeSat & weekafterSun
        
        # use the incompatible_slots method of employeeA's slots to exculde slots to not consider
        for s in empA_allslots:
            potential = potential.exclude(Slot.objects.incompatible_slots(s.workday,s.shift))
        context = {
            'slot':slot,
            'empA':empA,
            'shiftA':shiftA,
            'empA_allSlots':empA_allslots,
            'potential':potential,
        }
        return render(request, 'sch/test/test.html', context=context)