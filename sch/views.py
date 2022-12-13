from django.shortcuts import render, HttpResponse, HttpResponseRedirect
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Count
from django.urls import reverse_lazy, reverse
from django.views.generic.detail import DetailView
from django.views.generic.list import ListView
from django.views.generic.edit import UpdateView, DeleteView, FormView
from django.views.generic import View
from django.forms import formset_factory
from django.contrib import messages, admin
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.http import JsonResponse
from django_require_login.decorators import public
from django.contrib.auth.models import User


from .models import *
from .xviews.week import *
from .forms import *
from .formsets import *
from .actions import *
from .tables import *
from django.db.models import Q, F, Sum, Subquery, OuterRef, Count
from django_tables2 import RequestConfig
import datetime as dt


def index(request):
    
    if request.user == None:
        return HttpResponseRedirect(reverse_lazy("login-view"))
    
    today   = dt.date.today()
    wd      = Workday.objects.get(date=today)
    shifts  = wd.shifts
    context = {
        'user'  : request.user,
        'wd'    : wd, 
        'shifts': shifts,
    }
    return render ( request, 'index.html', context )

def day_changer (request, date):
    workday         = Workday.objects.get(slug=date)
    template_html   = 'sch/workday/dayChanger.html'
    
    return render (request, template_html, {'workday': workday})

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
            context['shifts']   = shifts.order_by('start')
            try: 
                context['overallSftPref'] = int(shifts.aggregate(Sum(F('prefScore')))['prefScore__sum'] /(2 * len(slots)) *100)
            except:
                context['overallSftPref'] = 0
            
            context['sameWeek'] = Workday.objects.same_week(self.object)  # type: ignore
            #weeklyHours        = [(empl, Slot.objects.empls_weekly_hours(year, week, empl)) for empl in Employee.objects.all()]
            unfilled            = Shift.objects.filter(occur_days__contains=self.object.iweekday).exclude(pk__in=slots.values('shift'))
            # ANNOTATION FOR # OF TECHS WHO COULD FILL SHIFTS SLOT 
            for sft in unfilled:
                sft.n_can_fill  = Employee.objects.can_fill_shift_on_day(shift=sft, cls=sft.cls,workday=self.object).values('pk').count()
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
            slot   = form.cleaned_data['slot']
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
    
    def periodFillTemplatesLanding (request, year, period):
        return render(request, 'sch/pay-period/fill_templates_landing.html', {'year':year, 'period':period})
    
    def periodFillTemplates (request, year, period):
        # URL : /sch2/period/<year>/<week>/fill/
        workdays = Workday.objects.filter(date__year=year, iperiod=period)
        for workday in workdays:
            WorkdayActions.fillDailySST(workday)
        return HttpResponseRedirect(f'/sch/pay-period/{year}/{period}/')

class WEEK:
    class WeekView (ListView):

        model               =  Week
        template_name       = 'sch/week/week.html'
        context_object_name = 'workdays'

        def get_context_data  (self, **kwargs):
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
            
            weekprefScore  = sum(week.slots.exclude(employee=None).values_list('empl_sentiment',flat=True)) / len(week.slots.exclude(employee=None))
            
            for day in context['workdays']:
                day.table = self.render_day_table(day)
                prefScore = sum(day.slots.exclude(employee=None).values_list('empl_sentiment',flat=True)) / len(day.slots.exclude(employee=None))
                day.prefScore = prefScore
                
            
            context['ptos'] = PtoRequest.objects.filter(workday__in=dates)
                                    
            if len(weekprefScore) != 0:
                weekprefScore = sum(weekprefScore) / len(weekprefScore)
                context['weekprefScore'] = int(weekprefScore)
            else:
                context['weekprefScore'] = 0 
            
            total_unfilled = 0
            for day in self.object_list:
                total_unfilled += day.n_unfilled
            context['total_unfilled'] = total_unfilled
            context['pay_period']   = context['workdays'].first().period
            context['pto_requests'] = PtoRequest.objects.filter( workday__week=week, status__in=['A','P'])
            context['dateFrom']     = context['workdays'].first().slug
            context['dateTo']       = context['workdays'].last().nextWD().slug
            context['turnarounds']  = (Slot.objects.filter(workday__in=context['workdays'], is_turnaround=True) | Slot.objects.filter(workday__in=context['workdays'], is_preturnaround=True))
            
            
            ufs = self.get_unfavorables()
            # group ufs, currently {empl:count,empl:count..} as {count:[empl,empl...]} :
            context['unfavorables'] = {}
            for empl in ufs:
                if empl:
                    if ufs[empl] in context['unfavorables']:
                        context['unfavorables'][ufs[empl]].append(empl)
                    else:
                        context['unfavorables'][ufs[empl]] = [empl]
            # and sort it by decreasing count:
            context['unfavorables'] = {
                i : sorted(context['unfavorables'][i]) for i in sorted(
                    context['unfavorables'], reverse=True)}
            _week = WEEK.GET()
            context['weekly_percents'] = _week.getPercentsWorkedWeek(year,week)
            context['turnarounds']     = _week.getTurnarounds(year,week)
            
            context['week_pto_reqs'] = PtoRequest.objects.filter(workday__in=context['workdays'])
            weekObj = Week.objects.get(year=year,number=week)
            context['weekObj'] = weekObj
            

            return context

        def get_queryset  (self):
            return Workday.objects.filter(date__year=self.kwargs['year'], iweek=self.kwargs['week']).order_by('date')

        def get_day_table  (self, workday):
            shifts              = Shift.objects.on_weekday(weekday=workday.iweekday).order_by('cls')
            slots               = Slot.objects.filter(workday=workday)
            sftAnnot            = shifts.annotate(employee=Subquery(slots.filter(shift=OuterRef('pk')).values('employee__name')))
            sftAnnot            = sftAnnot.annotate(employeeSlug=Subquery(slots.filter(shift=OuterRef('pk')).values('employee__slug')))
            # annotate if employee slot is turnaround
            sftAnnot            = sftAnnot.annotate(
                                    is_turnaround=Subquery(
                                        slots.filter(shift=OuterRef('pk'), 
                                        employee__name=OuterRef('employee')).values('is_turnaround')))
            sftAnnot            = sftAnnot.order_by('start','name','employee','employeeSlug')
            return ShiftsWorkdaySmallTable(sftAnnot, order_by=("cls"))

        def render_day_table(self, workday):
            return self.get_day_table(workday).as_html(self.request)

        def get_hours_queryset (self, year, week):
            return Employee.objects.all().annotate(
                hours=Subquery(Slot.objects.filter(workday__date__year=year,workday__iweek=week, employee=F('pk')).aggregate(hours=Sum('hours')))
            )
        
        def get_unfavorables (self):
            unfs = {}
            for day in self.object_list:
                unfs.update(day.unfavorables)
            return unfs
        
        def get_unfavorables (self):
            nfs = tally(
                list(Slot.objects.filter(
                    shift__start__hour__gte=10,workday__in=self.object_list).values_list ('employee__name', flat=True)) )
            # sort nfs by value:
            nfs = {i : nfs[i] for i in sorted(nfs, key=nfs.get)}
            return nfs

    def dayTableFragment(request, workday):
        workday = Workday.objects.get(slug=workday)
        context = {'workday':workday}
        template = 'sch/week/day-table-frag.html'
        return render(request, template, context)
    
    def iweekView (request, year, week_n):
        week = Week.objects.get(year=year,number=week_n)
        week.empl_week_sentiment()

    class GET: 
        def getPercentsWorkedWeek (self,year,week):
            """
            Get a DICT of percentFTE filled in a given week
            Suggested to fill next slot with employee at lowest FTE %
            
            >>> [(0.75,Josh),(0.83,Molly)...]
            """
            wds = Workday.objects.filter(date__year=year,iweek=week)
            emps = Employee.objects.all().exclude(fte=0)
            ftes = emps.values_list('name','fte_14_day')
            
            ### ANNOTATION 1 : worked_hours
            workedHrs = Employee.objects.filter(fte__gt=0)
            for emp in workedHrs:
                v = emp.weekly_hours(year,week)
                emp.worked_hours = v
                
            ### ANNOTATION 2 : perc_worked
            
            for emp in workedHrs:
                if Slot.objects.filter(workday__date__year=year,workday__iweek=week,employee=emp).exists():
                    emp.perc_worked= emp.worked_hours/(emp.fte_14_day/2)
            
            s = []
            for d in workedHrs:
                try:
                    if d.perc_worked != None:
                        if d.perc_worked > 1:
                            css= "orange-glow"
                        if d.perc_worked <= 1:
                            css= "green-glow"
                        if d.perc_worked <= 0.83:
                            css= "red-glow"
                except:
                    d.perc_worked = 0
                    css = ""
                     
                s.append((int(d.perc_worked*100),d.worked_hours,d.name,css))
            s.sort()
            # turn into Dict of {name: {'worked':workedH, 'perc_fte_w':perc}}
            return [{'employeeSlug':e[2].replace(' ','-'),'employee':e[2], 'week_hours':e[1],'week_percent':e[0],'css':e[3]} for e in s]
        
        def solvableUnfilledWeekSlots (self,year,iweek):
            wds = Workday.objects.filter(date__year=year,iweek=iweek)
            unsolved = [ wd.emptySlots for wd in wds ]
            for wd in unsolved:
                pass    # wd = [SlotMgr<S,S,S...> SlotMgr<S,S,S...>]
            
            return HttpResponse(slots,emps)
        
        def allEmplsWeeklyPercent (year,week):
            wds = Workday.objects.filter(date__year=year,iweek=week)
            emps = Employee.objects.all().exclude(fte=0)
            
        def getTurnarounds (self,year,weekId):
            slots = Slot.objects.filter(workday__date__year=year,workday__iweek=weekId,is_turnaround=True) | Slot.objects.filter(workday__date__year=year,workday__iweek=weekId,is_preturnaround=True) 
            return slots

    def weeklyHoursView (request):
        """
        View for a djangotables2 to show weeks in columns 
        and employees in rows, with the employee 
        weekly hours."""
        
        all_weeks = WeekActions.getAllWeekNumbers()
        table = EmployeeWeeklyHoursTable(Employee.objects.all())
        RequestConfig(request, paginate=True).configure(table) 
        context = {'table': table,
                    'weeks': all_weeks,}
        return render(request, 'sch/week/weekly-hours.html', context)
        
    def weekHoursTable (request, year, week):
        """WEEK HOURS TABLE """
        wds   = Workday.objects.filter(date__year=year,iweek=week)
        empls = Employee.objects.all()
        for empl in empls:
            empl.week = [wds.filter(iweekday=i, slot__employee=empl).order_by('iweekday').values_list('slot__shift__name',flat=True) for i in range(7)]
        
        context= {
            'empls' : empls,
            'wds'   : wds, 
            'seven' : range(7),
        }
        return render (request,'sch/week/week-hours-table.html', context)
             
    def weekFillTemplates (request, year, week):
        days = Workday.objects.filter(date__year=year, iweek=week)
        for day in days:
            WorkdayActions.fillDailySST(day) 
        return HttpResponseRedirect(f'/sch/week/{year}/{week}/')

    def all_weeks_view (request):
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
        while fx == True and n < 50 :
            ScheduleBot.performSolvingFunctionOnce (0,year,week)
            n += 1
            print(n)
        return HttpResponseRedirect(f'/sch/week/{year}/{week}/')
    
    def make_preference_swaps (request, year, week):
        for empl in Employee.objects.all():
            print(empl.info_printWeek(year,week))
        workdays = Workday.objects.filter(date__year=year, iweek=week)
        i = 3
        for workday in workdays:
            while i > 0:
                bestswap = ScheduleBot.best_swap(workday)
                if bestswap != None:
                    ScheduleBot.perform_swap(*bestswap)
                    messages.success(request,[f"{bestswap[0].shift}] {bestswap[0].employee} swapped with [{bestswap[1].shift}] {bestswap[1].employee}"])
                else:
                    i -= 1
        for empl in Employee.objects.all():
            print(empl.info_printWeek(year,week))
        return HttpResponseRedirect (f'/sch/week/{year}/{week}/')

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

def slotAdd_post (request, workday, shift):
    if request.method == 'POST':
        form = SlotForm(request.POST)
        if form.is_valid():
            employee = form.cleaned_data['employee']
            slot = Slot.objects.get(workday=WorkdayManager.slug, shift=shift) 
            slot.employee = employee
            slot.save()
            return HttpResponseRedirect(f'/sch2/day/{workday.slug}/')
    else:
        return HttpResponse('Error: Not a POST request')

def slot (request, date, shift):
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

def slotDelete (request, date, shift):
    slot = Slot.objects.get(workday__slug=date, shift__name=shift)
    slot.delete()
    return HttpResponseRedirect(f'/sch2/day/{date}/')

class HYPER:
    
    def hilight (request):
        
        return render(request, 'sch/hyper/highlight-mouseEnter.html')

class SHIFT :
    class ShiftDetailView (DetailView):
        model                = Shift
        template_name        = 'sch/shift/shift_detail.html'
        context_object_name  = 'shifts'

        def get_context_data(self, **kwargs):
            context                  = super().get_context_data(**kwargs)
            context ['shift']        = self.object 
            
            context ['empls_trained'] = Employee.objects.filter(shifts_trained=self.object).order_by('name')

            sstsA = [(day, ShiftTemplate.objects.filter(shift=self.object, ppd_id=day)) for day in range(7)] 
            context ['sstsA'] = sstsA
            sstsB = [(day, ShiftTemplate.objects.filter(shift=self.object, ppd_id=day)) for day in range(7,14)] 
            context ['sstsB'] = sstsB
            
            ssts  = [(day, ShiftTemplate.objects.filter(shift=self.object, ppd_id=day)) for day in range(42)]
            context ['ssts'] = ssts
            
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
        
    def shiftOverview (request):
        rph_n_evening = 0
        for sft in Shift.objects.filter(start__hour__gte=10, cls='RPh').values_list('occur_days',flat=True):
            rph_n_evening += len(sft)
        rph_ssts = ShiftTemplate.objects.filter(shift__start__hour__gte=10, employee__cls='RPh').count()
        cpht_n_evening = 0
        for sft in Shift.objects.filter(start__hour__gte=10, cls='CPhT').values_list('occur_days',flat=True):
            cpht_n_evening += len(sft)
        cpht_ssts = ShiftTemplate.objects.filter(shift__start__hour__gte=10, employee__cls='CPhT').count()
        
        resp = f""" *** EVENING TOTALS ***
         RPH EVENING SHIFTS : {rph_n_evening*6}/schedule
              RPH TEMPLATED : {rph_ssts}/schedule
              {rph_n_evening*6-rph_ssts} EVENING SHIFT(S) Remain
        CPHT EVENING SHIFTS : {cpht_n_evening*6}/schedule
        CPHT EVENING SHIFTS : {cpht_n_evening*6}/schedule
             CPHT TEMPLATED : {cpht_ssts}/schedule
             {cpht_n_evening*6-cpht_ssts} EVENING SHIFT(S) Remain"""
        print(resp)
        return HttpResponse(resp)

    class ShiftListView (ListView):
        """SHIFT LIST VIEW 
        =====================================================
        template_name: `templates/sch/shift/shift_list.html`
        """
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
        fields          = ['name',
                           'start',
                           'duration',
                           'occur_days',
                           'is_iv',
                           'cls',
                           'group'
                           ]
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
            context['template_slots'] = ShiftTemplate.objects.filter(shift__pk=self.kwargs['sftId'])
            context['shift'] = Shift.objects.get(pk=self.kwargs['sftId'])
            return context

        def get_queryset (self):
            return ShiftTemplate.objects.filter(shift__pk=self.kwargs['sftId'])
    
    def shiftTalliesView (request, shiftpk):
        shift = Shift.objects.get(pk=shiftpk)
        context = {}
        
        employees = Employee.objects.annotate(tally=Count('slots',filter=Q(slots__shift__name=shift)))
        for emp in employees: 
            emp.save()
        context['shift']     = shift
        context['employees'] = employees 
        context['maxTally']  = max(list(employees.values_list('tally',flat=True))) 
        employees = Employee.objects.annotate(
                            tally=Count('slots',filter=Q(slots__shift__name=shift))).annotate(
                            normalized=(F('tally')/context['maxTally'])*100
                        )
        
        return render(request, 'sch/shift/tallies.html', context)
        
    def trainedShiftView(request, cls, sft):
        context = {}
        shift = Shift.objects.get(cls=cls, name=sft)
        shiftClass = shift.cls
        context['shift'] = shift
        TrainedEmployeeShiftFormSet = formset_factory(TrainedEmployeeShiftForm, extra=0 )
        
        if request.method == 'POST':
            formset = TrainedEmployeeShiftFormSet(request.POST)
            if formset.is_valid():
                print('Formset VALID')
                for form in formset:
                    employee = form.cleaned_data.get('employee')
                    print(employee, form['is_trained'].value())
                    if form['is_trained'].value() == True:
                        print('is true!')
                        if shift not in employee.shifts_trained.all():
                            employee.shifts_trained.add(shift)
                            print(f'added to {employee}')
                            employee.save()
                    if form['is_trained'].value() == False:
                        if shift in employee.shifts_trained.all():
                            employee.shifts_trained.all()
                            employee.shifts_trained.remove(shift)
                            employee.save()
                    if form['is_available'].value() == True:
                        if shift not in employee.shifts_available.all():
                            employee.shifts_available.add(shift) 
                            employee.save()
                    if form['is_available'].value() == False:
                        if shift in employee.shifts_available.all():
                            employee.shifts_available.remove(shift)
                            employee.save()
                return HttpResponseRedirect(reverse('sch:shift-detail' , args=[cls, sft]))
            if formset.is_valid() == False:
                print(formset.errors)
        initData = [
            {
                'is_trained' : em.shifts_trained.filter(cls=cls,name=sft).exists(),
                'is_available' : em.shifts_available.filter(cls=cls,name=sft).exists(),
                'employee' : em,
                'shift' : shift,
            } for em in Employee.objects.filter(cls=shiftClass).order_by('name')
        ]
        formset = TrainedEmployeeShiftFormSet(initial=initData)
        context['formset'] = formset
        return render(request, 'sch/shift/trained_available_emps.html', context)
                        
class EMPLOYEE:
    
    
    class ANNO:
        nShiftsTrained = Employee.objects.annotate(n_shifts_trained=Count('shifts_trained')).order_by('n_shifts_trained').values_list('name','n_shifts_trained')
        
    
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
        fields          = ['name', 'fte_14_day', 'shifts_trained', 'shifts_available', 'streak_pref', 'cls']
        success_url     = '/sch/employees/all/'

        def form_valid(self, form):
            form.save() # type: ignore
            return super().form_valid(form)
        
    class TechnicianCreateView (EmployeeCreateView):
        form_class = TechnicianForm
        
    class PharmacistCreateView (EmployeeCreateView):
        form_class = PharmacistForm
        
    class EmployeePtoFormView (View):
        template_name   = 'sch/employee/pto_form.html'
        def get (self, request, empl, year, num):
            employee = Employee.objects.get(pk=empl)
            yeardates = []
            for date in SCH_STARTDATE_SET:
                if date.year == year:
                    yeardates.append(date)
            yeardates.sort()
            
            sch_date = yeardates[num]
            days = [(sch_date + dt.timedelta(days=i)).strftime("%Y-%m-%d") for i in range(42)]
            
            context = {
                'employee' : employee,
                'days'     : days,
            }
            return render(request, self.template_name, context)

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
            context['ptoTable']     = PtoListTable(PtoRequest.objects.filter(employee=self.object)) 
            context['ptoReqsExist'] = PtoRequest.objects.filter(employee=self.object).exists()
            context['multiplesOf7m1'] = [ i*7-1 for i in range(6) ]
            initial = {
                'employee' : self.object,
                'date_from': dt.date.today() - dt.timedelta( days=int(dt.date.today().strftime("%w")) ),
                'date_to'  : dt.date.today() - dt.timedelta( days=int(dt.date.today().strftime("%w")) ) + dt.timedelta(days=42)
            }
            
            

            return context

        def get_object(self):
            return Employee.objects.get(slug=self.kwargs['name'])

        def employeeSstGrid (employee):
            ssts = ShiftTemplate.objects.filter(employee=employee)
            sstsA = [(day, ssts.filter(ppd_id=day)) for day in range(7)]
            sstsB = [(day, ssts.filter(ppd_id=day)) for day in range(7,14)]
            return (sstsA, sstsB)

        def form_valid(self, form):
            date_from = form.cleaned_data['date_from']
            date_to = form.cleaned_data['date_to']
            employee = form.cleaned_data['employee']
            return HttpResponseRedirect('sch/employee/all/')

    ### UPDATE
    class EmployeeUpdateView (UpdateView):
        model           = Employee
        template_name   = 'sch/employee/employee_form_edit.html'
        form_class      = EmployeeEditForm
        success_url     = '/sch/employees/all/'

        def get_object(self):
            return Employee.objects.get(slug=self.kwargs['name'])
        
        def post (self, request, name):
            form = EmployeeEditForm(request.POST)
            print (form.errors)
            print (form.data)
        
            print (request, request.POST)
            if form.is_valid():
                
                e = Employee.objects.get(slug=name)
                e.name          = form.cleaned_data['name']
                e.cls           = form.cleaned_data['cls']
                e.streak_pref   = form.cleaned_data['streak_pref']
                e.fte_14_day    = form.cleaned_data['fte_14_day']
                e.shifts_trained.set(form.cleaned_data['shifts_trained'])
                e.shifts_available.set(form.cleaned_data['shifts_available'])
                e.save()
            return HttpResponseRedirect(e.url())
                
        
        

    ### SCH-FORM
    class EmployeeScheduleFormView (FormView):
        template_name   = 'sch/employee/schedule_form.html'
        form_class      = EmployeeScheduleForm
        fields          = ['employee', 'date_from', 'date_to']
        success_url     = '/sch/employees/all/'

        def form_valid(self, form):
            schedule = form.cleaned_data['schedule']
            employee = form.cleaned_data['employee']
            return HttpResponseRedirect(reverse('sch:v2-employee-schedule', 
                                                args=[employee.slug, schedule.slug]))

        def get_context_data(self, **kwargs):
            context = super().get_context_data(**kwargs)
            employee = Employee.objects.get(name=self.kwargs['name'])
            schedule = Schedule.objects.get(workdays__date=dt.date.today())
            context['form'] = EmployeeScheduleForm(initial={'employee': employee,'schedule': schedule})
            context['employee'] = employee
            return context

    ### SCHEDULE
    class EmployeeScheduleView (ListView):
        model           = Slot 
        template_name   = 'sch/employee/schedule.html'

        def get_context_data(self, **kwargs):
            context = super().get_context_data(**kwargs)
            employee = Employee.objects.get(name=self.kwargs['name'])
            
            context['employee'] = employee
            ptoReqs = PtoRequest.objects.filter(employee=employee)
            schedule = Schedule.objects.get(slug=self.kwargs['sch'])
            slots = schedule.slots.filter(employee=employee)
            days = [{
                'date':i.strftime("%Y-%m-%d"),
                'slot': slots.filter(workday__date=i)
                } for i in (schedule.workdays.all().values_list('date',flat=True))]
            
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
            return HttpResponseRedirect(reverse_lazy('sch:v2-employee-detail', kwargs={'name': name}))
        
        initData = [
            {'employee':employee, 'shift': s} for s in trainedFor
        ]
        for i in initData:
            if ShiftPreference.objects.filter(employee=employee, shift=i['shift']).exists():
                i['priority'] = ShiftPreference.objects.get(employee=employee, shift=i['shift']).priority
        print(initData)
        formset = prefFormset(initial=initData) # type: ignore
        print(formset)
        context['formset'] = formset
        context['emplPrefs'] = ShiftPreference.objects.filter(employee=employee)
        
        return render(request, 'sch/employee/shift_preferences_form.html', context)
    ### TPL-DAY-OFF-BREAKDOWN 
    def tdoBreakdownView (request):
        """TDO BREAKDOWN VIEW
        ===========================
        ``flowrate.herokuapp.com/sch/day-off-breakdown/``
        
        Breakdown Template Days Off
        ----------------------------
        Breakdown Template Days Off 
        
            TDOs (Template Days Off) are days off that are predefined for employees that have scheduled shifts
        """
        
        context = {}
        context['days'] = tally(list(TemplatedDayOff.objects.all().values_list('sd_id',flat=True)))
        context['employees'] = Employee.objects.all()
        context['tdos'] = TemplatedDayOff.objects.all()
        return render(request,'sch/tdo/all.html', context)
    
    def sortShiftPreferences (request, name):
        employee = Employee.objects.get(name=name)
        shifts = employee.shifts_available.all()
        context = {
            'shifts': shifts,
        }
        return render(request,'sch/employee/sortable-shift-pref.html', context)
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
        
        employee= Employee.objects.get(slug=name)
        
        if request.method == 'POST':
                formset = formset_factory(SstEmployeeForm, extra=0)
                formset = formset(request.POST)
                
                if formset.is_valid():
                    for form in formset:
                        shift = form.cleaned_data['shift']
                        sdid = form.cleaned_data['sd_id']
                        employee = form.cleaned_data['employee']
                        if shift == None:
                            if ShiftTemplate.objects.filter(sd_id=sdid, employee=employee).exists():
                                sst = ShiftTemplate.objects.get(sd_id=sdid, employee=employee)
                                sst.delete()
                        if shift != None:
                            if ShiftTemplate.objects.filter(sd_id=sdid,employee=employee).exists():
                                pass
                            else:
                                sft = ShiftTemplate.objects.create(sd_id=sdid,employee=employee, shift=shift)
                                sft.save()
                            
                return HttpResponseRedirect(reverse_lazy('sch:v2-employee-detail', kwargs={'name': name}))
                
        context = {}
        context['employee'] = employee
        context['template_slots'] = ShiftTemplate.objects.filter(employee=employee)
        
        formset = formset_factory(SstEmployeeForm, extra=0)
        sts = [ShiftTemplate.objects.filter(employee=employee, sd_id=i).exists() for i in range(42)]
        sts2 = []
        i = 0
        for s in sts:
            if s == True:
                sts2.append(ShiftTemplate.objects.get(sd_id=i, employee=employee).shift)
                i += 1
            else:
                sts2.append(None)
                i += 1
        
        initial = [{'sd_id': i,'employee':employee, 'shift': sts2[i]} for i in range(42)]
        
        formset    = formset (initial=initial)
        context['formset']  = formset
        return render(request, 'sch/employee/employee_ssts_form.html', context)
        
    def employeeTemplatedDaysOffView(request, name ):
        
            template_name = 'sch/employee/template_days_off.html'
            form_class = EmployeeTemplatedDaysOffForm
            success_url = '/sch/employees/all/' 
            
            employee = Employee.objects.get(slug=name)
            
            if request.method == "POST":
                formset = formset_factory(EmployeeTemplatedDaysOffForm,extra=0)
                formset = formset (request.POST)
                print('POST ')
                if formset.is_valid():
                    print('VALID')
                    for form in formset:
                        if form.cleaned_data.get('is_templated_off') == False:
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
                        
                    return HttpResponseRedirect('/sch/day-off-breakdown/')

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
            context['shifts'] = Shift.objects.annotate(
                            slot_count=Count('slots__employee', filter=Q(slots__employee=context['employee']))
                        )
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
        context ['employees'] = Employee.objects.all().order_by('cls','name')

        return render(request,'sch/employee/coworker-select.html',context)
    ### COWORKER
    def coWorkerView (request, nameA, nameB):
        """ COWORKER VIEW
        =======================================================
        
        Description
        -----------------------------------------------------------------------
            From the Base employees view, looks at Slots that co-occur with slots of another specified employee.
            
        URLs 
        -----------------------------------------------------------------------
            flowrate.herokuapp.com/sch/employees/`<employeeName>`/co-worker/`<otherEmployeeName>`/
        """
        emp1 = Employee.objects.get(name=nameA)
        emp2 = Employee.objects.get(name=nameB)
        
        emp1slots = Slot.objects.filter(employee=emp1).values('workday')
        emp1days  = Workday.objects.filter(pk__in=emp1slots)
        emp2days  = Slot.objects.filter(employee=emp2).values('workday')
        
        days = emp1days.filter(pk__in=emp2days).annotate(
            sft1=Subquery(Slot.objects.filter(employee=emp1,workday=OuterRef('pk')).values('shift__name'))).annotate(
                sft2=Subquery(Slot.objects.filter(employee=emp2,workday=OuterRef('pk')).values('shift__name')))
            
        return render(request, 'sch/employee/coworker.html', {'days':days,'emp1':emp1,'emp2':emp2})
    
    ### EVENING-FRACTION VIEW
    def eveningFractionView (request):
        empls = list(Employee.objects.all().order_by('name').values_list('name', flat=True))
        empls = {i : {'eveningFraction':0, 'evening':0, 'total':0} for i in empls}
        for emp in empls:
            if Slot.objects.filter(employee__name=emp).exists():
                percent = int (Slot.objects.filter(
                    employee__name=emp,shift__start__hour__gte=10).count() / Slot.objects.filter(
                        employee__name=emp).count()*100)
                empls[emp]['eveningFraction'] = percent
                empls[emp]['evening'] = Slot.objects.filter(employee__name=emp,shift__start__hour__gte=10).count()
                empls[emp]['total'] = Slot.objects.filter(employee__name=emp).count()
                
        # sort empls by eveningFraction:
        empls = {k: v for k, v in sorted(empls.items(), key=lambda item: item[1]['eveningFraction'])}
        
        return render(request,'sch/employee/eveningRatio/pmFrac.html', { 'employees':empls })

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
        
        def fillableBy (workday,shift):
            slot = Slot.objects.get(workday=workday,shift=shift)
            return JsonResponse(slot.fillableBy(),safe=False)
        
    def newSlotView (request, slotPk):
        slot = Slot.objects.get(pk=slotPk)
        html_template = 'sch/slot/detail-admin.html'
        context = {
            'slot': slot,
        }
        return render(request, html_template, context)
        
    def slotView (request, sch, date, shift) :
        slot = Slot.objects.get(schedule__pk=sch, workday__slug=date,shift__name=shift)
        
        if request.method == "POST":
            form = SlotForm(request.POST, instance=slot)
            if form.is_valid():
                employee = Employee.objects.get(pk=request.POST['employee'])
                slot.employee = employee
                slot.save()
                form.save()
                return HttpResponseRedirect(f'sch/day/{slot.workday.slug}')
        form = SlotForm(instance=slot)
        otherslots = Slot.objects.filter(workday=slot.workday).exclude(shift=slot.shift)
        context = {
            'slots':otherslots,
            'sch':sch,
            'mslot':slot,
            'form':form,
            'date':slot.workday,
            }
        return render(request,'sch/slot/slot_form.html',context)
                  
           
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

    class SlotDeleteView (DeleteView) : 
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
        
    def deleteTurnaroundsView (request):
        for slot in Slot.objects.turnarounds():
                slot.save()
        turns_am = Slot.objects.turnarounds()
        turns_pm = Slot.objects.preturnarounds()
        turnarounds = []
        for ta in turns_am:
            if ta.employee.evening_pref:
                turnarounds.append(ta.pk)
        for ta in turns_pm:
            if ta.employee.evening_pref == False:
                turnarounds.append(ta.pk)
        slots = Slot.objects.filter(pk__in=turnarounds)
        for slot in slots: 
                slot.delete()
                
        return HttpResponseRedirect('/sch/day/all/')
        
    def resolveTurnaroundSlot (request, date, shift) :
        potential = []
        slot = Slot.objects.get(workday__slug=date,shift__name=shift)
        for s in Slot.objects.filter(workday__slug=date, shift__start__hour__gte=12):
            if slot.shift in s.employee.shifts_available.all():
                if not s.employee in slot.conflicting_slots().values('employee'):
                    if s.shift in slot.employee.shifts_available.all():
                        potential.append(s)
                    potential += [s]
        print(potential)
        if len(potential) == 0:
            return HttpResponseRedirect(f'/sch/day/{date}/')
        emp1 = potential[-1].employee
        potential[-1].employee = None
        potential[-1].save()
        emp2 = slot.employee
        slot.employee = None
        slot.save()
        potential[-1].employee = emp2
        potential[-1].save()
        slot.employee = emp1
        slot.save()
        return HttpResponseRedirect(f'/sch/day/{date}/')
                

    class SlotTurnaroundsListView (ListView):
        
        template_name = 'sch/slot/turnarounds.html'
        context_object_name = 'slots'
        
        def get_queryset(self):
            for slot in Slot.objects.turnarounds():
                slot.save()
            turns_am = Slot.objects.turnarounds()
            turns_pm = Slot.objects.preturnarounds()
            turnarounds = []
            for ta in turns_am:
                if ta.employee.evening_pref:
                    turnarounds.append(ta.pk)
            for ta in turns_pm:
                if ta.employee.evening_pref == False:
                    turnarounds.append(ta.pk)
            return Slot.objects.filter(pk__in=turnarounds)
      
def EmpSSTView (request, name):
    
    context                  = {}
    employee                 = Employee.objects.get(name=name)
    context['employee']      = employee
    context['dayrange']      = range(42)
    context['wd']            = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat']
    on_days = range(14)
    TmpSlotFormSet = formset_factory (SstEmployeeForm, extra=0)

    
    if request.method == 'POST':
        TmpSlotFormSet = formset_factory(SstEmployeeForm)
        formset        = TmpSlotFormSet(request.POST)
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

    initData = [ {'ppd_id': i, 'employee': employee } for i in on_days ]

    formset = TmpSlotFormSet(initial=initData)

    context = {
        'employee': Employee.objects.get(name=employee), # type: ignore
        'formset' : formset,
        'idata'   : initData,

    }
    return render(request, 'sch/employee/employee_ssts_form.html', context)

class SST:
    class sstUpdateView (UpdateView):
        model           = ShiftTemplate
        template_name   = 'sch/sst/sst_form_edit.html'
        fields          = ['shift', 'ppd_id', 'employee']
        success_url     = '/sch/shifts/all/'

        def get_context_data(self, **kwargs):
            context = super().get_context_data(**kwargs) 
            context ['employee'] = self.object.employee
            return context

        def get_queryset(self):
            return ShiftTemplate.objects.filter(shift__name=self.kwargs['shift'])

    def sstDayView (request):
        context = {}
        dayinfo = []
        days = range(42)
        for day in days:
            dayinfo.append(ShiftTemplate.objects.filter(ppd_id=day))
        context['days'] = dayinfo
        context['range'] = range(42)
        
        return render(request, 'sch/sst/day_view.html', context)

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

def shiftTemplate (request, shiftid):
    """SHIFT TEMPLATE VIEW
    ======================================
    viewname
    >>> sch:shift-template
    """
    context               = {}
    shift                 = Shift.objects.get(pk=shiftid)
    context['shift']      = shift
    context['dayrange']   = range(14)
    context['wd']         = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat']
    on_days = shift.sd_ids 
    TmpSlotFormSet = formset_factory(SstForm, extra=0)
    print(on_days)
    
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
        {'sd_id': i, 
         'shift' : shift }  for i in range(42)
        ]
    

    formset = TmpSlotFormSet(initial=initData)

    context.update({
        'shift'    : Shift.objects.get(name=shift),
        'employees': Employee.objects.trained_for(shift), # type: ignore
        'formset'  : formset
        })
    
    return render(request, 'sch/shift/shift_sst_form.html', context)

import random
class SCHEDULE:
    
    class FX:
        
        def getSlots (year,sch):
            wds = Workday.objects.filter(date__year=year, ischedule=sch)
            for wd in wds:
                wd.slots = wd.emptySlots 
                
        def removePtoConflictSlots (request,year,sch):
            ac = Slot.objects.filter(workday__date__year=year,workday__ischedule=sch).annotate(
                ptoConflict=Subquery(PtoRequest.objects.filter(
                    employee=OuterRef('employee'), 
                    workday=OuterRef('workday__date')).values('workday')[:1]))
            allConflicts = ac.exclude(ptoConflict=None)
            for cnf in allConflicts:
                messages.success(request, f'Deleting Slot {cnf}')
                
            allConflicts.update(employee=None)
            return HttpResponseRedirect (f'/sch/schedule/{year}/{sch}')
                
        def removeTurnaround_EmplOptimized (self,year,sch):
            allConflicts = Slot.objects.filter (
                is_turnaround=True,workday__date__year=year,workday__ischedule=sch) | Slot.objects.filter (
                    is_preturnaround=True,workday__date__year=year,workday__ischedule=sch)
            strs = []
            for conflict in allConflicts:
                print('checking {}'.format(conflict))
                if conflict.employee != None:
                    if conflict.employee.evening_pref:
                        if conflict.shift.start.hour < 10:
                            strs.append('Deleted Slot: %s' % conflict)
                            Slot.objects.filter(pk=conflict.pk).update(employee=None)
                            
                    elif conflict.employee.evening_pref == False:
                        if conflict.shift.start.hour > 10:
                            strs.append('Deleted Slot: %s' % conflict)
                            Slot.objects.filter(pk=conflict.pk).update(employee=None)
            for conflict in allConflicts:
                conflict.save()
            for s in strs:
                messages.success( self, s )          
            return HttpResponseRedirect(f'/sch/schedule/{year}/{sch}')
          
        def theNickyCoefficient (self, year, sch):  
            slotsTogether = Slot.objects.filter(workday__date__year=year,workday__ischedule=sch,employee__name__in=['Josh','Nicki'])
            print( f"{len(slotsTogether)}" )
            
            slot_trades = {}
            for slot in slotsTogether:
                slot_trades[slot] = slot.tenable_trades
                
            slot_trades = str(slot_trades.items())
                
            return HttpResponse (slot_trades)
        
        def lazy_popover_load (request, schSlug, wdSlug):
            sch = Schedule.objects.get(slug=schSlug)
            wd = sch.workdays.get(slug=wdSlug)

            return render (request, 'sch2/schedule/sch-day-popover.html', {'workday':wd})
        
    class DO:
        
        @csrf_exempt
        def generateRandomPtoRequest ( request, schpk )  :
            """
            GENERATE RANDOM PTO REQUEST
            -----------------------------------------------------
            **Action View**
            
            """
            
            emp      = Employee.objects.all()[random.randint(0,Employee.objects.all().count())] 
            amount   = random.randint(1,6)
            sch      = Schedule.objects.get(pk=schpk)
            startDay = sch.workdays.all()[random.randint(0,41)]
            
            i = 0
            # while loop will repeat 1-6 times based on Randomizer
            while i < amount:
                if not PtoRequest.objects.filter(employee=emp, workday=startDay.date+dt.timedelta(days=i)).exists():
                    pto = PtoRequest.objects.create(employee=emp, workday=startDay.date+dt.timedelta(days=i))
                    pto.save()
                    i  += 1
                    
            return HttpResponseRedirect(reverse('sch:v1-schedule-detail',args=[sch.pk]))
    
    def scheduleListView (request):
        template_html = 'sch/schedule/sch_list.html'
        
        schedules = Schedule.objects.all()
        
        context = {
            'schedules': schedules,
            'schStartDates': SCH_STARTDATE_SET
        }  
        print(context["schStartDates"])
        return render(request, template_html, context)
    
    def scheduleDetailView (request, year, number):
        template_html   = 'sch/schedule/sch_detail.html'
        schedule        = Schedule.objects.get(year=year,number=number)
        
        context = {
            'schedule': schedule,
        }
        return render(request, template_html, context)
    
    def scheduleSlotModalView (request, year, number, version, workday, shift):
        """
        SCHEDULE SLOT MODAL VIEW
        This function generates the modal view of a schedule slot.
        It includes the employee assigned to the slot, 
        as well as a list of other employees who can fill the slot.
        """
        slot = Slot.objects.get(
            workday__date__year=year,
            schedule__number=number,
            schedule__version=version,
            workday__slug=workday,
            shift__name=shift)
        emp = slot.employee
        fillableBy = slot.fillableBy()
        
        modal_html = 'sch/schedule/sch_slot_modal.html'
        context = {
            'slot'       : slot,
            'emp'        : emp,
            'fillableBy' : fillableBy,
            }
        return render(request, modal_html, context)

    def scheduleSlotModalView (request, year, number, version, workday, shift):
        slot = Slot.objects.get(workday__date__year=year,schedule__number=number,schedule__version=version,
                                workday__slug=workday,shift__name=shift)
        emp = slot.employee
        fillableBy = slot.fillableBy()
        
        modal_html = 'sch/schedule/sch_slot_modal.html'
        context = {
            'slot'       : slot,
            'emp'        : emp,
            'fillableBy' : fillableBy,
            }
        return render(request, modal_html, context)
    
    def scheduleView (request, schId):
        context = {}
        sched = Schedule.objects.get(pk=schId)
        year = sched.year
        sch = sched.number
        context['days'] = sched.workdays.all()
        
        employees = Employee.objects.all().order_by('cls','name')
        
        for empl in employees:
            schedule = sched.workdays.filter(pk__in=context['days'].values('pk')).annotate(
                emplShift=Subquery(Slot.objects.filter(employee=empl.pk, workday=OuterRef('pk')).values('shift__name')[:1])).annotate(
                    ptoReq=Subquery(PtoRequest.objects.filter(employee=empl.pk, workday=OuterRef('date')).values('employee__name')[:1])).annotate(
                    streakPref=Subquery(Employee.objects.filter(pk=empl.pk).values('streak_pref')[:1])).annotate(
                    streak=Subquery(Slot.objects.filter(employee=empl.pk, workday=OuterRef('pk')).values('streak')[:1])).values_list('iweekday','emplShift','streak','ptoReq','streakPref')
            
            empl.schedule = schedule
            
        context['employees'] = employees

        context['weekendlist']  = [0,6]
        context['unfavorables'] = ScheduleBot.get_unfavorables(year,sch)
        
        context['year'] = year
        context['sch']  = sch
        
        context['conflicted'] = SCHEDULE.tdosConflictedSlots(year,sch)

        
        tempty = sched.slots.empty().count()
        ttotal = sched.slots.all().count() + tempty
        context['percComplete'] = f'{int(100-round(tempty / ttotal, 2) * 100)}%'
        context['nEmpty'] = tempty
        context['tot'] = ttotal
        context['unfilled'] = sched.slots.empty()
        
        if sch > 1:
            context['prevSch_url']    = f'/sch/schedule/{year}/{sch-1}/'
            context['nextSch_url']    = f'/sch/schedule/{year}/{sch+1}/'
        if sch >= 8:
            context['prevSch_url']    = f'/sch/schedule/{year}/{sch-1}/'
            context['nextSch_url']    = f'/sch/schedule/{year+1}/1/'
        else :
            context['prevSch_url']    = f'/sch/schedule/{year-1}/8'
            context['nextSch_url']    = f'/sch/schedule/{year}/{sch+1}/'
            
        context['schedule'] = sched
        
        return render(request, 'sch/schedule/grid.html', context)
    
    def currentScheduleView (request):
        today       = Workday.filter(date=dt.date.today()).first()
        
        
        return HttpResponseRedirect(reverse('sch:v2-schedule-detail',args=[today.schedule.slug] ))
    
    def weeklyOTView (request, year, sch):
        weeks = Workday.objects.filter(date__year=year,ischedule=sch).values_list('iweek',flat=True).distinct()
        employees = []
        for emp in Employee.objects.all(): 
            weeklyHrs = []
            for w in weeks:
                weeklyHrs += [Slot.objects.filter(employee=emp, workday__iweek=w).aggregate(Sum('shift__hours'))['shift__hours__sum']]
            employees += [{'name':emp.name, 'weeklyHrs':weeklyHrs}]
            
        return render(request, 'sch/schedule/ot.html', {'employees':employees,'weeks':weeks,'year':year,'sch':sch})
                  
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
    
    def solveScheduleLoader (request,year,sch):
        url_pattern = '/sch/schedule/<int:year>/<int:sch>/solve/'
        return HttpResponseRedirect(f'/sch/schedule/{year}/{sch}/solve-slots/')
    
    def solveScheduleSlots (request,schId):
        ScheduleBot.solveSchedule(0,schId)
        schedule = Schedule.objects.get(slug=schId)
        year = schedule.year 
        sch = schedule.number
        print(f"SOLVEBOT: MAIN PROCESS COMPLETED {dt.datetime.now()}")
        for slot in SCHEDULE.tdosConflictedSlots(year,sch):
            slot.delete()
            print(f"{slot} : TDO-CONFLICT SLOT DELETED DURING SOLUTION")
        for slot in Slot.objects.filter(workday__date__year=year,workday__ischedule=sch):
            if slot.is_turnaround :
                slot.delete()
            if slot.is_preturnaround :
                slot.delete()
            slot.save()
        SCHEDULE.solvePart2(request,year,sch)
        return HttpResponseRedirect(schedule.url())
        
    def solvePart2 (request,year,sch):
        emptySlots = []
        for day in Workday.objects.filter(date__year=year, ischedule=sch):
            for sft in day.emptySlots:
                emptySlots.append((day,sft))
                print(f"EMPTY SLOT DISCOVERED DURING PART-II-SOLUTION:    [{day.slug}: {sft}]")
        for slot in emptySlots:
            ScheduleBot().performSolvingFunctionOnce( slot[0].date.year, slot[0].ischedule )
        SCHEDULE.breakupLongStreaks(request, year,sch)
            
    def breakupLongStreaks (request,year,sch):
        print("RUNNING PROCESS *** BREAKUP-LONG-STREAKS")
        nUnfilled_initial = sum([wd.emptySlots.count() for wd in Workday.objects.filter(date__year=year,ischedule=sch)])
        print(f"N-UNFILLED INITIAL: {nUnfilled_initial}")
        slots = Slot.objects.filter(workday__date__year=year,workday__ischedule=sch)
        oneOverStreak = []
        for slot in slots:
            if slot.employee.streak_pref - slot.streak ==1:
                oneOverStreak += [slot]
        oneOverStreak
        for slot in oneOverStreak:
            if not ShiftTemplate.objects.filter(ppd_id=slot.workday.sd_id, employee=slot.employee).exists():
                print(f"DELETING SLOT : {slot}")
                slot.delete()
        for wd in Workday.objects.filter(date__year=year, ischedule=sch):
            wd.save()
        nUnfilled_final = sum([wd.emptySlots.count() for wd in Workday.objects.filter(date__year=year,ischedule=sch)])
        print(f"N-UNFILLED FINAL: {nUnfilled_final}")

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
    def radProgress (request, progress):
        return render(request,'sch/comp/rad-progress.html', {'progress':progress})
    
    def alertView (request, title, msg):
        return render(request, 'sch/doc/alert.html', context={'title': title, 'msg': msg})
    
    def spinner (request):
        return render(request, 'sch/test/spinner.html')
    
    def rphShiftChoices (request):
        context = {}
        context['shift_choices'] = Shift.objects.filter(cls='RPh')
        return render (request, 'sch/forms/shiftChoices.html', context)
    
    def cphtShiftChoices (request):
        context = {}
        context['shift_choices'] = Shift.objects.filter(cls='CPhT')
        return render (request, 'sch/forms/shiftChoices.html', context=context)
    
    def rank_shift_prefs (request, empl):
        context = { 'empl': empl }
        html_template='sch/alipine--drag-and-drop.html'
        return render (request,html_template, context)
       
    @csrf_exempt 
    def scheduleActiveLoad (request,year,sch):
        SCHEDULE.solveScheduleSlots(request,year,sch)
        SCHEDULE.solveScheduleSlots(request, year,sch)
        return render(request, 'sch/schedule/load_button_active.html')
        
class TEST:
    
    def spinner (request):
        return render(request, 'sch/test/spin_center.html')
    
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
    
    