from sch.models import *
from . import forms 
from django.shortcuts import render, HttpResponse, HttpResponseRedirect
from django.http import JsonResponse
from django.contrib import messages
from django.db.models import SlugField, SlugField, Sum, Case, When, FloatField, IntegerField, F, Value, CharField, Q
from django.db.models.functions import Cast
from django.template.loader import render_to_string
from django.views.decorators.csrf import csrf_exempt

from django_require_login.decorators import public
from flow.views import ApiViews

from rest_framework import viewsets
from .models import Employee, Week, Period, Schedule, Slot, ShiftTemplate, TemplatedDayOff, PtoRequest, Workday, Shift
from .serializers import (WorkdaySerializer, WeekSerializer, PeriodSerializer, 
                          ScheduleSerializer, SlotSerializer, ShiftTemplateSerializer, 
                          TemplatedDayOffSerializer, PtoRequestSerializer, EmployeeSerializer, 
                          ShiftSerializer)



class EmployeeViewSet(viewsets.ModelViewSet):
    queryset = Employee.objects.all()
    serializer_class = EmployeeSerializer
    
    filter_mappings = {
        'id'                : 'id',
        'name'              : 'name__icontains',
        'time_pref'         : 'time_pref__icontains',
        'streak_pref__gte'  : 'streak_pref__gte',
        'streak_pref__lte'  : 'streak_pref__lte',
        'available'         : 'shifts_available',
    }
    
    
class ShiftViewSet(viewsets.ModelViewSet):
    queryset = Shift.objects.all()
    serializer_class = ShiftSerializer
    
class WorkdayViewSet(viewsets.ModelViewSet):
    queryset = Workday.objects.all()
    serializer_class = WorkdaySerializer
    
class SlotViewSet (viewsets.ModelViewSet):
    queryset = Slot.objects.all()
    serializer_class = SlotSerializer
    
class WeekViewSet (viewsets.ModelViewSet):
    queryset = Week.objects.all()
    serializer_class = WeekSerializer
    
class PeriodViewSet (viewsets.ModelViewSet):
    queryset = Period.objects.all()
    serializer_class = PeriodSerializer 
    
class ScheduleViewSet (viewsets.ModelViewSet):
    queryset = Schedule.objects.all()
    serializer_class = ScheduleSerializer
    
class ShiftTemplateViewSet (viewsets.ModelViewSet):
    queryset = ShiftTemplate.objects.all()
    serializer_class = ShiftTemplateSerializer
    
class TemplatedDayOffViewSet (viewsets.ModelViewSet):
    queryset = TemplatedDayOff.objects.all()
    serializer_class = TemplatedDayOffSerializer
    
class PtoRequestViewSet (viewsets.ModelViewSet):
    queryset = PtoRequest.objects.all()
    serializer_class = PtoRequestSerializer
    
    



class Actions:
    class SlotActions:
        def clear_employee(request, slotId):
            slot = Slot.objects.get(pk=slotId)
            if request.method == "POST":
                
                slot.employee = None
                slot.save()
                messages.success(
                    request, f"Success! {slot.workday}-{slot.shift} Assignment Cleared"
                )
                return HttpResponseRedirect(slot.workday.url())

            messages.error(
                request,
                "Error: Clearing the employee assignment on this slot was unsuccessful...",
            )
            return HttpResponseRedirect(slot.url())

        def fill_with_best(request, slotId):
            if request.method == "POST":
                slot = Slot.objects.get(pk=slotId)
                empl_original = slot.employee
                slot.fillWithBestChoice()
                if slot.employee != empl_original:
                    msg = f"""Success! 
                    {slot.workday}-{slot.shift} Assigned to {slot.employee} 
                    via [FILL-VIA-BEST_CHOICE]"""
                    messages.success(request, msg)
                    return HttpResponseRedirect(slot.workday.url())
                else:
                    msg = f"""No Change: 
                    {slot.workday}-{slot.shift} Assigned to {slot.employee} 
                    via [FILL-VIA-BEST_CHOICE]"""
                    messages.success(request, msg)
                    return HttpResponseRedirect(slot.workday.url())

    class ShiftActions: 
        @csrf_exempt          
        def set__shift_img(request, empId):
            # get HX-PROMPT from header
            url = request.session['HX-PROMPT'] = request.headers['HX-PROMPT']
            empl = Employee.objects.get(pk=empId)
            empl.image_url = url
            empl.save()
            return HttpResponseRedirect(empl.url())
        
    class PeriodActions:
        def fill_slot_with_lowest_hour_employee(request, prdId):
            period = Period.objects.get(pk=prdId)
            empl = list(period.needed_hours())[0]
            fillableSlots = []
            for emptySlot in period.slots.empty():
                if empl in emptySlot.fillable_by():
                    fillableSlots += [emptySlot]
            selectedSlot = fillableSlots[random.randint(0, len(fillableSlots))]
            selectedSlot.employee = empl
            selectedSlot.save()
            if selectedSlot.employee != None:
                messages.success(
                    request,
                    f"Success: {selectedSlot} filled via PeriodActions.fill_slot_with_lowest_hour_employee",
                )
            return HttpResponseRedirect(period.url())
#######--- END OF ACTIONS SECTION ---########

class WeekViews:
    def all_slots_fillable_by_view(request, weekId):
        html_template = "sch2/week/all-slots-fillable-by-view.html"
        week = Week.objects.get(pk=weekId)
        context = {
            "week": week,
        }
        return render(request, html_template, context)

    def nextWeek (request, weekId):
        week = Week.objects.get(pk=weekId)
        nextWeek = week.nextWeek()
        return HttpResponseRedirect(nextWeek.url())

    def prevWeek (request, weekId):
        week = Week.objects.get(pk=weekId)
        prevWeek = week.prevWeek()
        return HttpResponseRedirect(prevWeek.url())

class SchViews:
    """
    _____GROUPED SCHEDULE VIEWS_____
    =================================
    """
    def newSchView (request):
        dates = Schedule.START_DATES
        return render(request, 'sch2/schedule/new.pug', {'dates':dates})
    
    class Calc:
        
        def uf_distr (
                request, 
                schId 
                ) -> JsonResponse:
            schedule = Schedule.objects.get(slug=schId)
            
            emusr = SchViews.schEMUSR(None, schedule.slug, asTable=False)

            emusr_differences = list(emusr.values_list('difference', flat=True))
            emusr_differences = [x for x in emusr_differences if x is not None]
    
            ufs = list(Schedule.objects.values_list('unfavorable_ratio',flat=True))
            
            mean = statistics.mean(ufs)
            ufs_stdev = statistics.stdev(ufs)
            uf_stdev_diff = schedule.unfavorable_ratio - mean 
            
            distr = uf_stdev_diff / ufs_stdev
            return JsonResponse(round(distr,2), safe=False)
        def n_empty (request, schId):
            sch = Schedule.objects.get(slug=schId)
            return sch.slots.empty().count()
        def percent (request, schId):
            sch = Schedule.objects.get(slug=schId)
            n_slots = sch.slots.count()
            n_filled = sch.slots.filled().count()
            return int(round(n_filled/n_slots,2)*100)
        def emusr_distr (request, schId):
            sch = Schedule.objects.get(slug=schId)
            n_pm = sch.slots.evenings().count()
            pm_empls = Employee.objects.filter(
                time_pref__in=["PM", "XN"]
            )
            pm_empls_shifts = sum(list(pm_empls.values_list("fte", flat=True))) * 40 * 6
            remaining_pm = n_pm - pm_empls_shifts
            full_template_empls = Employee.objects.full_template_employees().values("pk")
            am_empls_fte_sum = sum(
                list(
                    Employee.objects.filter(time_pref__in=["AM"])
                    .exclude(pk__in=full_template_empls)
                    .values_list("fte", flat=True)
                )
            )
            unfavorables = sch.slots.unfavorables().values("employee")
            unfavorables = unfavorables.annotate(
                count=Value(1, output_field=IntegerField())
            )
            unfavorables = unfavorables.values("employee").annotate(count=Sum("count"))
            emusr_differences = list(unfavorables.values_list("count", flat=True))
            while None in emusr_differences:
                emusr_differences.remove(None)
                emusr_differences.append(0)
            if len(emusr_differences) == 0:
                emusr_differences.append(0)
            return JsonResponse(max(emusr_differences) - min(emusr_differences), safe=False)
        def n_mistemplated (request, schId):
            sch = Schedule.objects.get(slug=schId)
            n = sch.slots.mistemplated().count()
            return n
        def ot_hours (request, schId):
            sch = Schedule.objects.get(slug=schId)
            employee_week_breakdowns = {}
            for employee in sch.employees.all():
                employee_week_breakdowns[employee.name] = [
                    sum(list(week.slots.filter(employee=employee).values_list(
                        'shift__hours', flat=True))) for week in sch.weeks.all()
                ]
            ot = 0 
            for wkHrs in employee_week_breakdowns.values():
                for hrs in wkHrs :
                    if hrs > 40 :
                        ot += hrs - 40
            return ot
        def all_calcs (request, schId):
            output =  {
                'percent': SchViews.Calc.percent(request, schId),
                'n_empty': SchViews.Calc.n_empty(request, schId),
                'emusr': SchViews.Calc.emusr_distr(request, schId),
                'emusr__sdfm': float(SchViews.Calc.uf_distr(request, schId).content),
                'n_mistemplated': SchViews.Calc.n_mistemplated(request, schId),
                'ot_hours': SchViews.Calc.ot_hours(request, schId),
                }
            return JsonResponse(output, safe=False)
            
        
    def schDetail(request, schId):
        schedule = Schedule.objects.get(slug=schId)
        return HttpResponseRedirect(f'/schedule/detail/{schedule.slug}/')      

    def schFtePercents(request, schId):

        html_template = "sch2/schedule/fte-percents.html"

        sch = Schedule.objects.get(slug=schId)
        # annotate a list of all employees with the sum of their scheduled hours of slots in sch.slots.all
        empls = (
            Employee.objects.annotate(
                total_hours=Sum(
                    Case(
                        When(slots__in=sch.slots.all(), then="slots__shift__hours"),
                        default=0,
                        output_field=FloatField(),
                    )
                )
            )
            .annotate(fte_percent=(F("total_hours") / (F("fte") * 240)) * 100)
            .order_by("-fte_percent")
        )
        context = {
            "sch": sch,
            "employees": empls,
        }
        return render(request, html_template, context)

    def compareSchedules(request, schId1, schId2):

        html_template = "sch2/schedule/sch-compare.html"

        sch1 = Schedule.objects.get(slug=schId1)
        sch2 = Schedule.objects.get(slug=schId2)
        
        days = []
        for day in sch1.workdays.all():
            slots = []
            for slot in day.slots.all():
                thisSlot = {}
                thisSlot["sch1"] = slot
                thisSlot["sch2"] = sch2.slots.get(
                    workday__sd_id=slot.workday.sd_id, shift__pk=slot.shift.pk
                )
                thisSlot["equal"] = (
                    thisSlot["sch2"].employee == thisSlot["sch1"].employee
                )
                slots += [thisSlot]
            days += [slots]
            
        context = {
            "sch1"      : sch1,
            "sch2"      : sch2,
            "workdays"  : days,
            "percentSimilarity": sch1.actions.calculatePercentDivergence(sch1,sch2),
        }
        return render(request, html_template, context)

    def schEMUSR(request, schId, asTable=False):
        """Schedule Expected Morning Unpreferred Shift Requirements
        -----------------------------------------------------------
        inputs: (1) request (2) schId 
        """
        import json
        import pandas as pd
        sch = Schedule.objects.get(slug=schId)
        n_pm = sch.slots.evenings().count()
        pm_empls = Employee.objects.filter(
            time_pref__in=["Midday", "Evening", "Overnight"]
        )
        pm_empls_shifts = sum(list(pm_empls.values_list("fte", flat=True))) * 24
        remaining_pm = n_pm - pm_empls_shifts
        full_template_empls = Employee.objects.full_template_employees().values("pk")
        am_empls_fte_sum = sum(
            list(
                Employee.objects.filter(time_pref__in=["Morning"])
                .exclude(pk__in=full_template_empls)
                .values_list("fte", flat=True)
            )
        )

        unfavorables = sch.slots.unfavorables().values("employee")
        unfavorables = unfavorables.annotate(
            count=Value(1, output_field=IntegerField())
        )
        unfavorables = unfavorables.values("employee").annotate(count=Sum("count"))

        query = (
            Employee.objects.filter(time_pref="Morning")
            .exclude(pk__in=full_template_empls)
            .annotate(
                emusr=Cast(
                    F("fte") * remaining_pm / am_empls_fte_sum,
                    output_field=IntegerField(),
                )
            )
            .order_by("-emusr")
            .annotate(
                count=Subquery(
                    unfavorables.filter(employee=OuterRef("pk")).values("count")
                )
            )
            .annotate(difference=F("emusr") - F("count"))
        )
        if asTable:
            df = pd.DataFrame(list(query.values()))
            return df
        return query

    def schEMUSRView(request, schId):
        
        html_template = "sch2/schedule/emusr.html"
        
        sch = Schedule.objects.get(slug=schId)
        emusr = SchViews.schEMUSR(None, sch.slug)
        emusr_differences = list(emusr.values_list("difference", flat=True))
        emusr_differences = [x for x in emusr_differences if x is not None]
        context = {
            "sch": sch,
            "emusr": emusr.exclude(emusr=0),
            "emusr_dist": max(emusr_differences) - min(emusr_differences),
        }
        return render(request, html_template, context)

    def schEMUSREmployeeView (request, schId, empl):
        html_template = "sch2/schedule/emusr-employee.html"
        sch = Schedule.objects.get(slug=schId)
        unfavorables = sch.slots.unfavorables().filter(employee=empl)
        emusr = SchViews.schEMUSR(None, sch.slug).get(pk=empl)

        context = {
            "sch": sch,
            "emusr": emusr,
            "unfavorables": unfavorables,
        }
        return render(request, html_template, context)

    def getSchEmptyCount (request, schId):
        sch = Schedule.objects.get(slug=schId)
        empty_count = sch.slots.filter(employee__isnull=True).count()
        return HttpResponse(empty_count)

    def schTdoConflictsView (request, schId):
        
        html_template = "sch2/schedule/tdo-conflict-table.html"
        
        schedule     = Schedule.objects.get(slug=schId)
        tdoConflicts = []
        for slot in schedule.slots.all():
            if slot.shouldBeTdo:
                tdoConflicts.append(slot)
        tdoConflicts = Slot.objects.filter(pk__in=[s.pk for s in tdoConflicts])

        if request.method == "POST":
            for slot in tdoConflicts:
                print(slot)
                if slot.shouldBeTdo:
                    slot.employee = None
                    slot.save()
            return HttpResponseRedirect(schedule.url())

        context = {
            "tdoConflicts": tdoConflicts,
            "schedule": schedule,
        }
        return render(request, html_template, context)

    def clearOverFteSchView (request,schId):
        schedule = Schedule.objects.get(slug=schId)
        empty_initial = schedule.slots.empty().count()
        slots  = []
        for prd in schedule.periods.all():
            for employee in prd.slots.values("employee").distinct():
                employee = Employee.objects.filter(pk=employee)
                if employee.exists():
                    slots += prd.slots.filter(employee=employee.first()).first()
        for slot in schedule.slots.all():
            slot.actions.clear_over_fte_slots(slot)
        empty_final = schedule.slots.empty().count()
        messages.success (
                request, 
                f"Schedule {schedule.number}{schedule.version}.{schedule.year} All Employees Brought down to FTE Levels."
                f"Resulted in {empty_initial - empty_final} slot assignments being cleared."
            )
        return HttpResponseRedirect(schedule.url())

    def syncDbSchView (request, schId):
        sch = Schedule.objects.get(slug=schId)
        for slot in sch.slots.all():
            slot.save()
        messages.success (request, f"Successfully synched database with schedule {sch.slug}" )
        return HttpResponseRedirect (sch.url())        
    
    def mistemplatedView (request, schId):
        sch = Schedule.objects.get(slug=schId)
        n = sch.slots.mistemplated().count()
        return render(request, 'sch3/schedule/partials/mistemplated.html', {'schedule':sch,'n':n })
        
        
        
class SchPartials:
    def schStatBarPartial (request, schId):
        html_template = "sch2/schedule/partials/stat-bar.html"
        sch = Schedule.objects.get(slug=schId)
        context = {
            "schedule": sch,
        }
        return render (request, html_template, context)
    
    def schComplexTablePartial (request, schId):
        html_template = "sch2/schedule/partials/complex-table-wrapper.html"
        sch = Schedule.objects.get(slug=schId)
        for wd in sch.workdays.all():
            wd.save()
        context = {
            "schedule": sch,
        }
        return render (request, html_template, context)
    
    def schCompareSelectPartial (request, schId):
        html_template = "sch2/schedule/partials/compare-select.html"
        sch = Schedule.objects.get(slug=schId)
        context = {
            "schedule": sch,
            "other_schedules": Schedule.objects.exclude(slug=schId),
        }
        return render (request, html_template, context)
    
    def schViewSelectPartial (request, schId):
        html_template = "sch2/schedule/partials/view-select.html"
        sch = Schedule.objects.get(slug=schId)
        context = {
            "schedule": sch,
        }
        return render(request, html_template, context)
    
    def schEmployeeGridPartial (request, schId):
        html_template = "sch2/schedule/partials/sch-as-empl-grid.html"
        sch = Schedule.objects.get(slug=schId)
        context = {
            "schedule": sch,
        }
        return render(request, html_template, context)
    
    def schShiftGridPartial (request, schId):
        html_template = "sch2/schedule/partials/sch-as-shift-grid.html"
        sch = Schedule.objects.get(slug=schId)
        context = {
            "schedule": sch,
        }
        return render(request, html_template, context)
    
    def schFteRatioPartial (request, schId):
        html_template = "sch2/schedule/partials/fte-percents.html"
        sch = Schedule.objects.get(slug=schId)
        empls = (
            Employee.objects.annotate(
                total_hours=Sum(
                    Case(
                        When(slots__in=sch.slots.all(), then="slots__shift__hours"),
                        default=0,
                        output_field=FloatField(),
                    )
                )
            )
            .annotate(fte_percent=(F("total_hours") / (F("fte") * 240)) * 100)
            .order_by("-fte_percent")
        )
        context = {
            "sch": sch,
            "employees": empls,
        }
        return render(request, html_template, context)
    
    def schWeeklyBreakdownPartial (request,schId):
        html_template = "sch2/schedule/partials/sch-employee-week-breakdown.html"
        sch = Schedule.objects.get(slug=schId)
        context = {
            'schedule' : sch,
            'employees' : Employee.objects.all(),
        }
        return render(request, html_template, context)

    def schMistemplatedPartial (request, schId):
        sch = Schedule.objects.get(slug=schId)
        mistemplated = sch.slots.mistemplated().all()
        return render(request,'sch2/schedule/partials/mistemplated.html',{'sch' : sch , 'mistemplated' : mistemplated })


class EmpPartials:
    def tdoPreview (request, empPk):
        empl = Employee.objects.get(pk=empPk)
        tdos = [empl.tdos.filter(sd_id=x).count() for x in range(42)]
        html_template = 'sch2/employee/partials/tdo-preview.html'
        return render(request, html_template, {'tdos':tdos } )
    def workPrevDay (request, empPk, wdId):
        wd = Workday.objects.get(slug=wdId)
        empl = Employee.objects.get(pk=empPk)
        if wd.prevWD().slots.filter(employee=empl).exists():
            return HttpResponse (wd.prevWD().slots.filter(employee=empl).first().shift.group)
        else :
            return HttpResponse ("")
    def workNextDay (request, empPk, wdId):
        wd = Workday.objects.get(slug=wdId)
        empl = Employee.objects.get(pk=empPk)
        if wd.nextWD().slots.filter(employee=empl).exists():
            return HttpResponse (wd.nextWD().slots.filter(employee=empl).first().shift.group)
        else :
            return HttpResponse ("")
    def comingUp (request, empPk):
        empl = Employee.objects.get(pk=empPk)
        comingUp = empl.slots.filter(workday__date__gte=date.today()).order_by('workday__date')[:7]
        html_template = 'sch2/employee/partials/coming-up.html'
        return render(request, html_template, {'empl':empl})
        
        
class WdViews:
    def wdayDetailBeta (request, slug):
        wd = Workday.objects.get(slug=slug)
        html_template = "sch2/workday/wd-2.html"
        context = {
            "wd": wd,
        }
        return render(request, html_template, context)

class SlotViews:
    
    def slotStreakView(request, slug, sft):
        """
        Slot Streak View: 
            - Shows the streak of slots for a given Slot
            - Streak generated from the selected slot
        """
        html_template = "sch2/slot/streak-timeline.html"
        
        slot = Slot.objects.get(workday__slug=slug, shift__name=sft)
        siblings = slot.siblings_streak()
        ids = [s.pk for s in siblings] + [slot.pk]
        streak = Slot.objects.filter(pk__in=ids).order_by("workday__date")
        for s in streak:
            s.save()
        context = {
            "mainSlot": slot,
            "streak"  : streak,
        }
        return render(request, html_template, context)
    def clearSlotViaShift (request, wdId, shiftId):
        """
        Clear Slot Via Shift: 
            - Clears all slots for a given shift on a given workday
        """
        wd = Workday.objects.get(slug=wdId)
        shift = Shift.objects.get(pk=shiftId)
        slot = wd.slots.filter(shift=shift).first()
        slot.employee = None
        slot.save()
        return HttpResponseRedirect(wd.url())
        
    def slotClearActionView (request, slotId):
        """
        Slot Clear Action View
        ============================================
        input:   slotId
        --------------------------------------------
        """
        slot = Slot.objects.get(pk=slotId)
        if request.method == 'POST':
            old_assignment = slot.employee
            slot.actions.clear_employee(slot)
            messages.success(
                    request, 
                    f"success:{old_assignment} cleared from {slot} successfully."
                )
            return HttpResponseRedirect(slot.workday.url())
        else:
            messages.error(
                    request, 
                    f"error:Invalid request method."
                )
            return HttpResponseRedirect(slot.url())

class ShiftViews:
    
    def sstFormView(request, shiftId):
        """
        SST Form View: 
            - Edits the 42 Schedule-Days for a given Shift"""
        import json

        html_template = "sch2/shift/sst-form.html"
        
        shift = Shift.objects.get(name=shiftId)
        days = {}
        weekdays = [
            "Sunday",
            "Monday",
            "Tuesday",
            "Wednesday",
            "Thursday",
            "Friday",
            "Saturday",
        ]
        for i in range(42):
            day = {}
            day["sd_id"] = (i,)
            day["shift_on_sd_id"] = str(i % 7) in shift.occur_days
            excludeEmployees = (
                ShiftTemplate.objects.filter(sd_id=i)
                .exclude(shift=shift)
                .values_list("employee", flat=True)
            )
            exclude_tdos = TemplatedDayOff.objects.filter(
                sd_id=i).values_list(
                "employee", flat=True
            )
            excludeEmployees = Employee.objects.filter(
                pk__in=list(excludeEmployees) + list(exclude_tdos)
            )
            day["available"] = Employee.objects.filter(
                shifts_available__pk=shift.pk
            ).exclude(pk__in=excludeEmployees)
            day["initial"] = ShiftTemplate.objects.filter(sd_id=i, shift=shift).first()
            days[i] = day

        initial_data = {
            "shift": shift,
            "sd_id": i,
            "employee": ShiftTemplate.objects.filter(sd_id=i, shift=shift)
            .first()
            .employee
            if ShiftTemplate.objects.filter(sd_id=i, shift=shift).first()
            else None,
        }
        print(initial_data)

        if request.method == "POST":
            for sd_id, employee in request.POST.items():
                if sd_id != "csrfmiddlewaretoken":
                    sst = ShiftTemplate.objects.filter(sd_id=sd_id, shift=shift)
                    if sst.exists():
                        sst = sst.first()
                        employee = Employee.objects.get(pk=employee)
                        if sst.employee != employee:
                            sst.employee = employee
                            sst.save()
                            print(f"Updated {sst}")
                    else:
                        pass
            return HttpRequestRedirect(shift.url())
                                

        context = {"shift": shift, "days": days}
        return render(request, html_template, context)

class EmpViews:
    def empShiftSort(request, empId):
        html_template = "sch2/employee/shift-sort.html"
        emp = Employee.objects.get(pk=empId)
        if request.method == "POST":
            print(request.POST)
            for i in range(1, emp.shifts_available.count() + 1):
                shift = request.POST.get(f"bin-{i}")
                if shift:
                    shift = Shift.objects.get(name=shift.replace("shift-", ""))
                    pref = emp.shift_sort_prefs.get_or_create(shift=shift)[0]
                    pref.score = i
                    pref.rank = i - 1
                    pref.save()
            sort_repr = ", ".join([f"{pref.shift} ({pref.score})" for pref in emp.shift_sort_prefs.all()])
            messages.success(
                request,
                f"{emp} shift sort preferences updated: {sort_repr}",
            )
            print(messages.get_messages(request))
            print("here is a log statement")
            return HttpResponseRedirect(emp.url())

        context = {
            "employee": emp,
            "nTotal": range(1, emp.shifts_available.all().count() + 1),
        }
        return render(request, html_template, context)
    def empShiftTallies (request, empId, doRender=True):
        from django.db.models import Count, OuterRef, Subquery
        # define a subquery that counts the occurrences of each employee/shift combination in the Slot model
        subquery = Subquery(
            Slot.objects.filter(
                employee=OuterRef('employee'),
                shift=OuterRef('shift')
            ).values('employee', 'shift').annotate(
                count=Count('*')
            ).values('count')[:1],
            output_field=models.IntegerField()
            )
        # Count n of Slots, then if A ShiftPreference exists for that employee/shift combination
        j = Employee.objects.get(name=empId)
        j_shift_prefs = j.shift_prefs.annotate(count=subquery)

        score_subquery = Subquery(
            Slot.objects.filter(
                employee=OuterRef('employee'),
                shift=OuterRef('shift'),
            ).values('employee', 'shift', 'employee__shift_prefs__priority').annotate(
                count=Count('*')
            ).values('count')[:1],
            output_field=models.IntegerField()
        )
        from django.db.models import Sum

        j_shift_prefs_with_counts = j_shift_prefs.annotate(
            pref_score=Subquery(
                ShiftPreference.objects.filter(
                    employee=OuterRef('employee'),
                    shift=OuterRef('shift')
                ).values('score')[:1]
            )
        ).annotate(
            score_count=Coalesce(score_subquery, 0)
        ).values(
            'score'
        ).annotate(
            count=Sum('score_count')
        ).order_by('score')
        # annotate the queryset with the list of shifts that the employee has that score for 
        # then annotate with 'Strongly Dislike' to 'Strongly Like' based on the -2 to 2 score 
        j_shift_prefs_with_counts = j_shift_prefs_with_counts.annotate(
            shifts=Subquery(
                ShiftPreference.objects.filter(
                    employee=OuterRef('employee'),
                    score=OuterRef('score')
                ).values('shift__name')
            )
        )
        if doRender == False:
            return j_shift_prefs_with_counts
        return render(request, 'sch2/employee/shift-tally.pug', {'emp':j, 'tallies': j_shift_prefs_with_counts})

    def tallyPlotDataGenerator (request, empId):    
        from django.db.models import Count, OuterRef, Subquery
        import pandas as pd
        import seaborn as sns
        import matplotlib.pyplot as plt
        import urllib
        import base64
        from io import BytesIO
        import seaborn as sns
        import matplotlib.pyplot as plt
        # define a subquery that counts the occurrences of each employee/shift combination in the Slot model
        subquery = Subquery(
            Slot.objects.filter(
                    employee=OuterRef('employee'),
                    shift=OuterRef('shift')
                ).values('employee', 'shift').annotate(
                    count=Count('*')
                ).values('count')[:1],
                output_field=models.IntegerField()
                )
        # Count n of Slots, then if A ShiftPreference exists for that employee/shift combination
        emp = Employee.objects.get(name=empId)
        shift_prefs = emp.shift_prefs.annotate(count=subquery)

        score_subquery = Subquery(
                        Slot.objects.filter(
                            employee=OuterRef('employee'),
                            shift=OuterRef('shift'),
                        ).values('employee', 'shift', 'employee__shift_prefs__priority').annotate(
                            count=Count('*')
                        ).values('count')[:1],
                        output_field=models.IntegerField()
                    )
        from django.db.models import Sum

        sps = shift_prefs.annotate(
            pref_score=Subquery(
                ShiftPreference.objects.filter(
                    employee=OuterRef('employee'),
                    shift=OuterRef('shift')
                ).values('score')[:1]
            )
        ).annotate(
            score_count=Coalesce(score_subquery, 0)
                ).values('score').annotate(
            count=Sum('score_count')
                ).order_by('score')
                
        data = []
        for j in sps:
            for n in range(j['count']):
                data.append(j['score'])

        return JsonResponse(data, safe=False)
        
class IdealFill:
    def levelA(request, slot_id):
        """Checks Training and No Turnarounds"""
        slot = Slot.objects.get(pk=slot_id)
        base_avaliable = slot.shift.available.all()
        inConflictingSlots = slot._get_conflicting_slots().values("employee")
        available__noConflict = base_avaliable.exclude(pk__in=inConflictingSlots)
        return available__noConflict

    def levelB(request, slot_id):
        """Checks for No Weekly Overtime"""
        slot = Slot.objects.get(pk=slot_id)
        underFte = []
        nh = slot.period.needed_hours()
        for n in nh:
            if nh[n] > slot.shift.hours:
                underFte += [n.pk]
        possible = IdealFill.levelA(None, slot_id)
        return possible.filter(pk__in=nh)

    def levelC(request, slot_id):
        """Checks for No PayPeriod FTE overages"""
        slot = Slot.objects.get(pk=slot_id)
        underFte = []
        nh = slot.week.needed_hours()
        for n in nh:
            if nh[n] > slot.shift.hours:
                underFte += [n.pk]
        possible = IdealFill.levelA(None, slot_id)
        return possible.filter(pk__in=nh)

    def levelD(request, slot_id):
        """Checks for Matching Time-of-day Preference"""
        slot = Slot.objects.get(pk=slot_id)
        timeGroup = slot.shift.group
        possible = IdealFill.levelC(None, slot_id)
        return possible.filter(time_pref=timeGroup)

    def levelE(request, slot_id):
        """Checks for Preferred Streak-length not to be exceeded"""
        slot = Slot.objects.get(pk=slot_id)
        possible = IdealFill.levelD(None, slot_id)
        ok_streak = []
        for possibility in possible:
            slot.employee = possibility
            slot.save()
            maxStreak = slot.siblings_streak().count() + 1
            if slot.employee.streak_pref >= maxStreak:
                ok_streak += [possibility]
        return Employee.objects.filter (pk__in=ok_streak)

    def levelF(request, slot_id):
        for empl in IdealFill.levelE(None, slot_id):
            empl.shift


class UserViews:

    def userDetailView (request, uname):
        html_template = "sch2/user/user-detail.html"
        user = User.objects.get(username=uname)
        context = {"user": user}
        if request.method == 'POST':
            view_pref = request.POST.get('wd-view-pref')
            WorkdayViewPreference.objects.filter(user=user).update(view=view_pref)
            messages.success (request, f"View preference updated to {view_pref} for {user}.")
            
        return render(request, html_template, context)