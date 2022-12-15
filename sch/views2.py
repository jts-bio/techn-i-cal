import datetime as dt
import re

from django.contrib import admin, messages
from django.contrib.auth.forms import UserCreationForm
from django.core.serializers import serialize
from django.db.models import Count, F, OuterRef, Q, Subquery, Sum
from django.forms import formset_factory
from django.http import JsonResponse
from django.shortcuts import HttpResponse, HttpResponseRedirect, render
from django.template.loader import get_template, render_to_string
from django.urls import reverse_lazy
from django.views.decorators.csrf import csrf_exempt
from django.views.generic.detail import DetailView
from django.views.generic.edit import DeleteView, FormView, UpdateView
from django.views.generic.list import ListView
from django_tables2 import RequestConfig
from django.views.generic.base import View

from .actions import *
from .forms import *
from .formsets import *
from .models import *
from .tables import *
from .data import Images


# -------------------------#
#### LIST OF SCHEDULES ####
# -------------------------#
def schListView(request):

    schedules = Schedule.objects.all()

    if request.method == "POST":
        sd = request.POST.get("start_date")
        start_date = dt.date(int(sd[:4]), int(sd[5:7]), int(sd[8:]))
        print(start_date)
        i = 0
        idate = start_date
        while idate.year == start_date.year:
            i += 1
            idate = idate - dt.timedelta(days=42)
        generate_schedule(year=start_date.year, number=i)

        return HttpResponseRedirect(reverse("sch:sch-list"))

    context = {
        "schedules": schedules,
        "new_schedule_form": GenerateNewScheduleForm(),
    }
    return render(request, "sch2/schedule/sch-list.html", context)


def schDayPopover(request, year, num, ver, day):
    schedule = Schedule.objects.get(year=year, number=num, version=ver)
    workday = schedule.workdays.get(day=day)

    context = {
        "workday": workday,
    }
    return render(request, "sch2/schedule/sch-day-popover2.html", context)


def schDetailView(request, schId):
    """
    ---------- SCHEDULE DETAIL VIEW  ----------
    """
    schedule = Schedule.objects.get(slug=schId)

    action1 = {
        "name":    "Solve: Method A",
        "note":    "(AI trained on Shift Scheduling data) ",
        "confirm": "Confirm you want the AI to solve the remaining slots of this schedule.",
        "url":      schedule.url__solve_b(),
    }
    action2 = {
        "name":    "Solve: Method B",
        "note":    "(Quasi-algorithmic approach [in progress])",
        "confirm": "This method is under construction and may take upward of 5 minutes to complete. Verify to continue.",
        "url":      schedule.url__solve(),
    }
    actionDropdown = render_to_string(
        "sch/comp/dropdown_btn.html",
        {
            "menuItems": [action1, action2],
            "deleteLink": schedule.url__clear(),
        },
    )

    if request.method == "POST":
        form = EmployeeSelectForm(request.POST)
        if form.is_valid():
            employee = form.cleaned_data["employee"]
            return HttpResponseRedirect(
                reverse("sch:v2-schedule-empl-pto", args=[schedule.pk, employee.pk])
            )
    context = {
        "schedule": schedule,
        "actionDropdown": actionDropdown,
        "employees": Employee.objects.all(),
        "form": EmployeeSelectForm,
    }
    form = EmployeeSelectForm()
    return render(request, "sch2/schedule/sch-detail.html", context)


def weekView(request, week):
    week = Week.objects.filter(pk=week).first()
    week.save()
    context = {
        "week": week,
        "slots": week.slots.filled().order_by("employee"),
        "workdays": week.workdays.all(),
    }
    return render(request, "sch2/week/wk-detail.html", context)


def weekView__set_ssts(request, week):
    """
    If SST exists and filling employee is appropriate, Slot is filled.
    Exceptions that will result in no change:
        - empl has ptoreq
        - empl would go overtime
        - empl in conflicting slot
    """
    if request.method == "POST":
        week = Week.objects.filter(pk=week).first()
        for day in week.workdays.all():
            for slot in day.slots.all():
                slot.set_sst()
        return HttpResponseRedirect(week.url())


def weekView__clear_slots(request, week):
    if request.method == "POST":
        week = Week.objects.filter(pk=week).first()
        week.slots.filled().update(employee=None)
    return HttpResponseRedirect(week.url())


def workdayDetail(request, slug):

    html_template = "sch2/workday/wd-detail.html"
    workday = Workday.objects.get(slug=slug)

    context = {
        "workday": workday,
    }
    return render(request, html_template, context)


def shiftDetailView(request, cls, name):
    html_template = "sch2/shift/shift-detail.html"

    shift = Shift.objects.get(cls=cls, name=name)
    _ = [int(sft) for sft in shift.occur_days]
    days = ",".join(["SMTWRFS"[d] for d in _])

    context = {
        "shift": shift,
        "days": days,
    }
    return render(request, html_template, context)


def shiftTrainingFormView(request, cls, sft):

    shift = Shift.objects.get(cls=cls, pk=sft)
    if request.method == "POST":
        # if there is a dict key in the form of 'employee-trained' and it to the list trained:
        trained = []
        for i in request.POST:
            tagless = i[:-8]
            if i.replace("-trained", "") == tagless:
                e = Employee.objects.get(slug=tagless)
                trained.append(e)
        available = []
        for i in request.POST:
            tagless = i[:-10]
            if i.replace("-available", "") == tagless:
                e = Employee.objects.get(slug=tagless)
                available.append(e)
        for employee in Employee.objects.all():
            if employee in trained:
                if shift not in employee.shifts_trained.all():
                    employee.shifts_trained.add(shift)
            if employee not in trained:
                if shift in employee.shifts_trained.all():
                    employee.shifts_trained.remove(shift)
            if employee in available:
                if shift not in employee.shifts_available.all():
                    employee.shifts_available.add(shift)
            if employee not in available:
                if shift in employee.shifts_available.all():
                    employee.shifts_available.remove(shift)
        return HttpResponseRedirect(shift.url())

    html_template = "sch2/shift/shift-training.html"
    empls = Employee.objects.filter(cls=shift.cls).order_by("name")
    context = {
        "shift": shift,
        "empls": empls,
    }
    return render(request, html_template, context)


def currentWeek(request):
    workday = Workday.objects.filter(date=dt.date.today()).first()
    week = Week.objects.filter(workdays=workday).first()
    return HttpResponseRedirect(week.url())


def currentSchedule(request):
    workday = Workday.objects.filter(date=dt.date.today()).first()
    schedule = Schedule.objects.filter(workdays=workday).first()
    return HttpResponseRedirect(schedule.url())


def scheduleSolve(request, schId):
    sch = Schedule.objects.get(slug=schId)
    bot = sch.Actions()
    bot.fillSlots(sch)
    return HttpResponseRedirect(sch.url())


def scheduleClearAllView(request, schId):
    try:
        sch = Schedule.objects.get(pk=schId)
    except:
        pass
    try:
        sch = Schedule.objects.get(slug=schId)
    except:
        pass
    sch.slots.filled().update(employee=None)
    return HttpResponseRedirect(sch.url())


class ScheduleMaker:
    def generate_schedule(self, year, number):
        """
        GENERATE SCHEDULE
        ===========================================
        args:
            - ``year``
            - ``number``
        -------------------------------------------
        """
        yeardates = []
        for date in SCH_STARTDATE_SET:
            if date.year == year:
                yeardates.append(date)
        yeardates.sort()
        n = Schedule.objects.filter(year=year, number=number).count()
        version = "ABCDEFGHIJKLMNOPQRST"[n - 1]
        print(yeardates)
        start_date = yeardates[number - 1]
        sch = Schedule.objects.create(
            start_date=start_date, version=version, number=number, year=year
        )
        sch.save()
        for slot in sch.slots.all():
            slot.save()
        return (
            sch,
            f"Successful Creation of schedule {sch.slug}. Completed at [{dt.datetime.now()}] ",
        )


def mytest(request):
    return render(request, "sch/test/layout.html", {})


def generate_schedule_form(request):
    html_template = "sch2/schedule/generate-new-miniform.html"
    TEMPLATESCH_STARTDATE = dt.date(2020, 1, 12)
    SCH_STARTDATE_SET = [
        (TEMPLATESCH_STARTDATE + dt.timedelta(days=42 * i)) for i in range(50)
    ]
    print(SCH_STARTDATE_SET)
    context = {
        "schStartDates": SCH_STARTDATE_SET,
    }
    return render(request, html_template, context)


def generate_schedule_view(request, year, num):
    generate_schedule(year, num)
    return HttpResponseRedirect(reverse("sch:schedule-list"))


def pto_schedule_form(request, schId, empl):
    """
    PTO Schedule Form View
    --------------------------------------------------
    >>> v2/schedule-empl-pto/<str:schId>/<str:empl>/
    """
    html_template = "sch2/schedule/pto-input.html"
    empl = Employee.objects.get(pk=empl)
    sch = Schedule.objects.get(pk=schId)

    if request.method == "POST":
        pto_checked = list(request.POST.keys())[1:]
        wds = sch.workdays.all().values("date")
        PtoRequest.objects.filter(workday__in=wds, employee=empl).delete()
        for pto_date_str in pto_checked:
            YMD = re.findall("(\d+)-(\d+)-(\d+)", pto_date_str)[0]
            pto_date = dt.date(int(YMD[0]), int(YMD[1]), int(YMD[2]))
            pto_new = PtoRequest.objects.create(workday=pto_date, employee=empl)
            pto_new.save()

            messages.success(request, f"{pto_new} created at {dt.datetime.now()}")

        return HttpResponseRedirect(sch.url())

    context = {
        "employee": Employee.objects.get(pk=empl),
        "schedule": Schedule.objects.get(pk=schId),
        "initial_pto_dates": sch.pto_requests.filter(employee=empl).values_list(
            "workday", flat=True
        ),
    }
    print(context)
    return render(request, html_template, context)


def shift_templating_view(request, schId):
    shift = Shift.objects.get(pk=schId)


class PeriodViews:
    def detailView(request, prdId):
        html_template = "sch2/period/detail.html"
        period = Period.objects.get(pk=prdId)
        context = {
            "period": period,
        }
        return render(request, html_template, context)


def schDetailSlotTableView(request, schId):
    html_template = "sch2/schedule/slot-table.html"
    schedule = Schedule.objects.get(pk=schId)
    context = {
        "schedule": schedule,
    }
    return render(request, html_template, context)


def schTdoConflictTableView(request, schId):
    html_template = "sch2/schedule/tdo-conflict-table.html"
    schedule = Schedule.objects.get(pk=schId)
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


class EmployeeSortShiftPreferences(View):

    template_name = "flow/alpine--drag-and-drop.html"

    def get(self, request, slug, **kwargs):
        context = {"employee": Employee.objects.get(slug=slug)}
        return render(request, self.template_name, context)

    def post(self, request, slug, **kwargs):
        print(request.POST)
        employee = Employee.objects.get(slug=slug)
        employee.shiftSortPrefs.all().delete()
        i = 0
        output_string = ""
        for pref in list(request.POST.values())[1:]:
            shift = Shift.objects.get(pk=pref)
            ssp = ShiftSortPreference.objects.create(
                employee=employee, shift=shift, score=i
            )
            i += 1
            ssp.save()
            output_string += f"{shift.name}. "

        msg = f"New Sorted Shift Preferences saved for {employee}. {output_string}"
        messages.success(request, msg)

        return HttpResponseRedirect(employee.url())
