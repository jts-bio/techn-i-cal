from sch.models import *
from . import forms
from django.shortcuts import render, HttpResponse, HttpResponseRedirect
from django.contrib import messages
from django.db.models import Sum, Case, When, FloatField, IntegerField, F, Value
from django.db.models.functions import Cast


class Actions:
    class SlotActions:
        def clear_employee(request, slotId):
            if request.method == "POST":
                slot = Slot.objects.get(pk=slotId)
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


class WeekViews:
    def all_slots_fillable_by_view(request, weekId):
        html_template = "sch2/week/all-slots-fillable-by-view.html"
        week = Week.objects.get(pk=weekId)
        context = {
            "week": week,
        }
        return render(request, html_template, context)

    def nextWeek(request, weekId):
        week = Week.objects.get(pk=weekId)
        nextWeek = week.nextWeek()
        return HttpResponseRedirect(nextWeek.url())

    def prevWeek(request, weekId):
        week = Week.objects.get(pk=weekId)
        prevWeek = week.prevWeek()
        return HttpResponseRedirect(prevWeek.url())


class SchViews:
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
            "sch1": sch1,
            "sch2": sch2,
            "workdays": days,
        }
        return render(request, html_template, context)

    def schEMUSR(request, schId):
        """Schedule Expected Morning Unpreferred Shift Requirements"""
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


class SlotViews:
    def slotStreakView(request, slotId):
        html_template = "sch2/slot/streak-timeline.html"
        slot = Slot.objects.get(pk=slotId)
        siblings = slot.siblings_streak()
        ids = [s.pk for s in siblings] + [slot.pk]
        streak = Slot.objects.filter(pk__in=ids).order_by("workday__date")
        context = {
            "mainSlot": slot,
            "streak": streak,
        }
        return render(request, html_template, context)


class ShiftViews:
    def sstFormView(request, shiftId):
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
            exclude_tdos = TemplatedDayOff.objects.filter(sd_id=i).values_list(
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
                if sd_id == "csrfmiddlewaretoken":
                    continue
                else:
                    sst = ShiftTemplate.objects.filter(shift=shift, sd_id=sd_id)
                    if sst.exists():
                        sst = sst.first()
                        if employee == "":
                            sst.delete()
                            messages.INFO(
                                request,
                                sst.employee,
                                sst.shift,
                                "SCH DAY #",
                                sst.sd_id,
                                "[ DELETED SUCCESSFULLY ]",
                            )
                        else:
                            if sst.employee == Employee.objects.get(pk=employee):
                                continue
                            else:
                                sst.employee = Employee.objects.get(pk=employee)
                                sst.save()
                                print(
                                    sst.employee,
                                    sst.shift,
                                    "SCH DAY #",
                                    sst.sd_id,
                                    "[ SAVED SUCCESSFULLY ]",
                                )

        context = {"shift": shift, "days": days}
        return render(request, html_template, context)


class EmpViews:
    def empShiftSort(request, empId):
        html_template = "sch2/employee/shift-sort.html"
        emp = Employee.objects.get(pk=empId)
        if request.method == "POST":
            for i in range(1, emp.shifts_available.count() + 1):
                shift = request.POST.get(f"bin-{i}")
                shift = Shift.objects.get(name=shift.replace("shift-", ""))
                pref = emp.shift_sort_prefs.get_or_create(shift=shift)[0]
                pref.score = i
                pref.rank = i - 1
                pref.save()
            messages.success(
                request,
                f"Success: {emp} shift sort preferences updated: {emp.shift_sort_prefs.all()}",
            )

            return HttpResponseRedirect(emp.url())

        context = {
            "employee": emp,
            "nTotal": range(1, emp.shifts_available.all().count() + 1),
        }
        return render(request, html_template, context)


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
        """Checks for Prefered Streak-length not to be exceeded"""
        slot = Slot.objects.get(pk=slot_id)
        possible = IdealFill.levelD(None, slot_id)
        okstreak = []
        for possibleEmpl in possible:
            slot.employee = possibleEmpl
            slot.save()
            maxStreak = slot.siblings_streak().count() + 1
            if slot.employee.streak_pref >= maxStreak:
                okstreak += [possibleEmpl]
        return Employee.objects.filter(pk__in=okstreak)

    def levelF(request, slot_id):
        for empl in IdealFill.levelE(None, slot_id):
            empl.shift
