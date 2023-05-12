from django.shortcuts import render

# Create your views here.
from sch.models import *
from sch.serializers import SlotSerializer, EmployeeSerializer

from django.http import HttpResponse, JsonResponse, HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse, reverse_lazy
from django import forms
from django.views.generic.base import TemplateView, RedirectView, View
from django.db.models import (
    SlugField,
    SlugField,
    Sum,
    Case,
    When,
    FloatField,
    IntegerField,
    F,
    Value,
)
from django.db.models.functions import Cast
from django.views.decorators.csrf import csrf_exempt
import json
from django.views.decorators.vary import vary_on_headers
from sch.models import Schedule, Department


class ApiViews:
    def schedule__list(request):
        schs = Schedule.objects.all()
        page = request.GET.get("page", 1)
        page_size = 5
        return JsonResponse(schs[(page * page_size) - 1 : (page + 1) * page_size])

    def schedule__get_n_empty(request, schId):
        sch = Schedule.objects.get(slug=schId)
        return JsonResponse(sch.slots.empty().count(), safe=False)

    def schedule__get_weekly_hours(request, schId):
        sch = Schedule.objects.get(slug=schId)
        employee_week_breakdowns = {}
        for employee in sch.employees.all():
            employee_week_breakdowns[employee.name] = [
                sum(
                    list(
                        week.slots.filter(employee=employee).values_list(
                            "shift__hours", flat=True
                        )
                    )
                )
                for week in sch.weeks.all()
            ]
        return JsonResponse(employee_week_breakdowns, safe=False)

    def schedule__get_weekly_hours__employee(request, schId, empName):
        employee = Employee.objects.filter(name__contains=empName).first()
        sch = Schedule.objects.get(slug=schId)
        employee.weekBreakdown = [
            sum(
                list(
                    week.slots.filter(employee=employee).values_list(
                        "shift__hours", flat=True
                    )
                )
            )
            for week in sch.weeks.all()
        ]
        return JsonResponse(employee.weekBreakdown, safe=False)

    def schedule__get_emusr_list(request, schId):
        sch = Schedule.objects.get(slug=schId)
        emusrEmployees = sch.employees.emusr_employees()
        for e in emusrEmployees:
            n = sch.slots.unfavorables().filter(employee=e).count()
            e.n_unfavorables = n
        return JsonResponse(
            {f"{e.name}": e.n_unfavorables for e in emusrEmployees}, safe=False
        )

    def schedule__get_emusr_range(request, schId):
        sch = Schedule.objects.get(slug=schId)
        emusrEmployees = sch.employees.emusr_employees()
        for e in emusrEmployees:
            n = sch.slots.unfavorables().filter(employee=e).count()
            e.n_unfavorables = n
        data = {f"{e.name}": e.n_unfavorables for e in emusrEmployees}
        return JsonResponse(max(data.values()) - min(data.values()), safe=False)

    def schedule__get_percent(request, schId):
        sch = Schedule.objects.get(slug=schId)
        calculatedPercent = int(sch.slots.filled().count() / sch.slots.count() * 100)
        if sch.percent != calculatedPercent:
            sch.percent = calculatedPercent
        return JsonResponse(
            int(sch.slots.filled().count() / sch.slots.count() * 100), safe=False
        )

    def schedule__get_n_pto_conflicts(request, schId):
        sch = Schedule.objects.get(slug=schId)
        return JsonResponse(sch.slots.pto_violations().count(), safe=False)
    
    def schedule__get_n_tdo_conflicts(request, schId):
        sch = Schedule.objects.get(slug=schId)
        return JsonResponse(sch.slots.tdo_violations().count(), safe=False)

    def schedule__get_n_untrained(request, schId):
        sch = Schedule.objects.get(slug=schId)
        return JsonResponse(sch.slots.untrained().count(), safe=False)

    def schedule__get_untrained_list(request, schId):
        sch = Schedule.objects.get(slug=schId)
        return JsonResponse(
            SlotSerializer(sch.slots.untrained(), many=True).data, safe=False
        )

    def schedule__get_n_mistemplated(request, schId):
        sch = Schedule.objects.get(slug=schId)
        return JsonResponse(sch.slots.mistemplated().count(), safe=False)

    def schedule__get_mistemplated_list(request, schId):
        sch = Schedule.objects.get(slug=schId)
        return JsonResponse(
            SlotSerializer(sch.slots.mistemplated(), many=True).data, safe=False
        )

    def schedule__get_n_unfavorables(request, schId):
        sch = Schedule.objects.get(slug=schId)
        return JsonResponse(sch.slots.unfavorables().count(), safe=False)

    def schedule__get_unfavorables_list(request, schId):
        sch = Schedule.objects.get(slug=schId)
        return JsonResponse(
            SlotSerializer(sch.slots.unfavorables(), many=True).data, safe=False
        )

    @vary_on_headers("X-Requested-With")
    def schedule__get_empty_list(request, schId):
        sch = Schedule.objects.get(slug=schId)
        return JsonResponse(SlotSerializer(sch.slots.empty(), many=True).data, safe=False)

    def schedule__employee_excess_week_hours(request, schId, empId, wk):
        sch = Schedule.objects.get(slug=schId)
        emp = Employee.objects.get(slug=empId)
        slots = sch.slots.filter(workday__week__number=wk, employee=emp)
        data = {"slots": SlotSerializer(slots, many=True).data}
        return JsonResponse(data, safe=False)

    def schedule__get_n_turnarounds(request, schId):
        sch = Schedule.objects.get(slug=schId)
        return JsonResponse(sch.slots.turnarounds().count(), safe=False)

    def schedule__get_overtime_hours(request, schId):
        sch = Schedule.objects.get(slug=schId)
        for wk in sch.weeks.all():
            wk.save()
        ot_sum = 0
        for wk in sch.weeks.values("hours"):
            for emp, val in wk["hours"].items():
                if val > 40:
                    ot_sum += val - 40
        return JsonResponse(ot_sum, safe=False)

    def schedule__get_undertime_hours(request, schId):
        """
        output example:
        >>> {'Cheryl':
                   {'weeks':   [40.0, 10.0, 20.0, 40.0, 40.0, 30.0],
                    'periods': [50.0,       60.0,       70.0],
                    'fte': 1.0,
                    'needed-week-1': 30.0,
                        'week-1-empty': ['2023-06-22B-EP'],
                        'week-1-steal': ['2023-06-20B-7C'],
                    'needed-week-2': 20.0,
                        'week-2-empty': ['2023-06-26B-EP'],
                        'week-2-steal': ['2023-06-26B-MI'],
                    'needed-week-5': 10.0,
                        'week-5-empty': ['2023-07-18B-EI'],
                        'week-5-steal': ['2023-07-16B-EI',
                                         '2023-07-17B-MI',
                                         '2023-07-17B-7C'
            }
        """
        sch          = Schedule.objects.get(slug='2023-S4B')
        
        empl_dict    = {empl.slug:{
                            'weeks':[],
                            'periods':[],
                            'fte':empl.fte,
                            'img_url':empl.image_url
                        } for empl in sch.employees.filter(fte__gt=0)}
        
        wk_empl_dict = {empl.slug:[] for empl in sch.employees.all()}

        for pd in sch.periods.all():
            for week in pd.weeks.all():
                for empl in sch.employees.all():
                    if week.slots.filter(employee=empl).count() > 0:
                        slot_sum = sum(list(week.slots.filter(employee=empl).values_list('shift__hours',flat=True)))
                        pto_sum  = week.pto_requests().filter(employee=empl).count() * 10
                        wk_empl_dict[empl.slug] += [slot_sum + pto_sum]
                    else:
                        wk_empl_dict[empl.slug] += [0]

        pd_empl_dict = {empl.slug:[] for empl in sch.employees.all()}
        for empl in wk_empl_dict:
            pd_empl_dict[empl] += [wk_empl_dict[empl][0] + wk_empl_dict[empl][1]]
            pd_empl_dict[empl] += [wk_empl_dict[empl][2] + wk_empl_dict[empl][3]]
            pd_empl_dict[empl] += [wk_empl_dict[empl][4] + wk_empl_dict[empl][5]]

        for emp in empl_dict:
            empl_dict[emp]['weeks'] = wk_empl_dict[emp]
            empl_dict[emp]['periods'] = pd_empl_dict[emp]
            
            i = 0 # week counter
            for wk in empl_dict[emp]['weeks']:

                if wk < empl_dict[emp]['fte'] * 40:

                    # i // 2 = period number
                    if empl_dict[emp]['periods'][i//2] < empl_dict[emp]['fte'] * 80:
                    
                        empl_dict[emp][f"needed-week-{i}"] = empl_dict[emp]['fte'] * 40 - empl_dict[emp]['weeks'][i]

                        empl_dict[emp][f"week-{i}-empty"]  = list(sch.weeks.all()[i].slots.filter(
                                                                employee__isnull= True, 
                                                                fills_with__slug= emp)
                                                                .values_list('slug',flat=True))
                        
                        empl_dict[emp][f"week-{i}-empty"]  = [j for j in empl_dict[emp][f"week-{i}-empty"] if j is not None]

                        empl_dict[emp][f"week-{i}-steal"]  = list(sch.weeks.all()[i].slots.filter(
                                                                employee__fte= 0,
                                                                fills_with__slug= emp)
                                                                .values_list('slug',flat= True))
                        
                        empl_dict[emp][f"week-{i}-steal"]  = [j for j in empl_dict[emp][f"week-{i}-steal"] if j is not None]

                    else:
                        empl_dict[emp][f"needed-week-{i}"] = 0
                        empl_dict[emp][f"week-{i}-empty"]  = []
                        empl_dict[emp][f"week-{i}-steal"]  = []
                else:
                    empl_dict[emp][f"needed-week-{i}"] = 0
                    empl_dict[emp][f"week-{i}-empty"]  = []
                    empl_dict[emp][f"week-{i}-steal"]  = []
                i += 1
        return JsonResponse(empl_dict, safe=False) # type: Dict[str, Dict[str, Any]]

    @staticmethod
    def schedule__get_undertime_hours_sum(request, schId):
        from schedule.utils import get_sum_sch_undertime
        
        return JsonResponse(get_sum_sch_undertime(schId), safe=False)
        
        sch = Schedule.objects.get(slug=schId)
        ut = {}
        for pd in sch.periods.all():
            pd.save()
            for empl in sch.employees.filter(fte__gt=0):
                pd_hours  = pd.slots.filter(employee=empl).aggregate(Sum("shift__hours"))['shift__hours__sum'] or 0
                pto_hours = PtoRequest.objects.filter(employee=empl,workday__in=pd.workdays.values('date')).count() * 10

                print(f"{empl} : {(pd_hours + pto_hours) - (empl.fte * 80)}")

                if pd_hours + pto_hours < empl.fte * 80:
                    total = empl.fte * 80 - pd_hours 
                    ut[empl.slug] = total - pto_hours if total - pto_hours > 0 else 0

        return JsonResponse(sum(ut.values()), safe=False)


    def schedule__is_best_version(request, schId):
        sch = Schedule.objects.get(slug=schId)
        schedules = Schedule.objects.filter(start_date=sch.start_date)
        max_percent = max(list(schedules.values_list("percent", flat=True)))
        return HttpResponse(str(max_percent == sch.percent))

    def employee__week_hours(request, empId, sch, wd):
        emp = Employee.objects.get(slug=empId)
        day = Workday.objects.get(schedule=sch, slug__contains=wd)
        return HttpResponse(emp.weekHours(day))

    def employee__period_hours(request, empId, sch, wd):
        emp = Employee.objects.get(slug=empId)
        day = Workday.objects.get(schedule=sch, slug__contains=wd)
        return HttpResponse(emp.periodHours(day))


class ApiActionViews:
    """
    API DRIVEN ACTION VIEWS
    ---
    ```
    build_schedule
    build_alternate_draft
    deleteSch
    set__shift_img
    pto_req__delete
    pto_req__create
    clear_fte_overages
    ignoreMistemplateFlag
    ```
    """
    @staticmethod
    def build_schedule(request, year, num, version, dept_id, start_date, testing=False):
        """Build Schedule
        ---
        ```
        params:
            1  year
            2  num_of_sch
            3  version_char
        """
        # basic time data
        pd_nums = [num * 2 + i for i in range(3)]
        wk_nums = [num * 6 + i for i in range(6)]
        dates   = [start_date + dt.timedelta(days=i) for i in range(42)]

        # object creation
        schedule = Schedule.objects.create(
            year=year,
            number=num,
            version=version,
            department=Department.objects.get(slug=dept_id),
            start_date=start_date,
            slug=f"{year}-S{num}{version}",
        )
        schedule.save()

        pd_start_dates = [dates[i] for i in [0, 14, 28]]
        pd_nums        = [num * 2 + i for i in range(3)]
        pds            = []

        for i in range(3):
            pd = Period.objects.create(
                year=year,
                start_date=pd_start_dates[i],
                schedule=schedule,
                number=pd_nums[i],
            )
            pd.save()
            pds.append(pd)

        wk_start_dates  = [dates[i] for i in [0, 7, 14, 21, 28, 35]]
        wk_nums         = [num * 6 + i for i in range(6)]
        wks             = []

        for i in range(6):
            wk = Week.objects.create(
                year=year,
                start_date=wk_start_dates[i],
                schedule=schedule,
                number=wk_nums[i],
                period=pds[0] if i < 2 else pds[1] if i < 4 else pds[2],
            )
            wk.save()
            wks.append(wk)

        wdlist = []

        for i in range(42):
            slug = f"{dates[i].strftime('%Y-%m-%d')}{version}"
            date = dates[i]
            period = Period.objects.get(
                schedule=schedule,
                number=pd_nums[0] if i < 14 else pd_nums[1] if i < 28 else pd_nums[2],
            )
            week = Week.objects.get(
                schedule=schedule,
                number=wk_nums[0]
                if i < 7
                else wk_nums[1]
                if i < 14
                else wk_nums[2]
                if i < 21
                else wk_nums[3]
                if i < 28
                else wk_nums[4]
                if i < 35
                else wk_nums[5],
            )
            iweekday = i % 7
            sd_id = i
            wdlist += [
                Workday(
                    schedule=schedule,
                    slug=slug,
                    date=date,
                    period=period,
                    week=week,
                    iweekday=iweekday,
                    sd_id=sd_id,
                )
            ]

        for wd in wdlist:
            wd.save()
            slotlist = []
            for sft in Shift.objects.filter(occur_days__contains=wd.iweekday, department=schedule.department):
                period = wd.period
                week = wd.week
                shift = sft
                workday = wd
                employee = None
                slotlist += [
                    Slot(
                        schedule=schedule,
                        period=period,
                        week=week,
                        shift=shift,
                        workday=workday,
                        employee=employee,
                    )
                ]

            Slot.objects.bulk_create(slotlist)

            schedule.employees.set(Employee.objects.filter(department=schedule.department))

            print (f"slots made for wd {wd}")

        slots = Slot.objects.filter(schedule=schedule)

        for slot in slots:
            slot.fills_with.set(
                Employee.objects.filter(shifts_available=slot.shift)
                .exclude(pk__in=slot.workday.on_pto())
                .exclude(pk__in=slot.workday.on_tdo())
            )
            template = ShiftTemplate.objects.filter(
                shift=slot.shift, sd_id=slot.workday.sd_id
            )
            if template.exists():
                slot.template_employee = template.first().employee
        slots.bulk_update(slots, ["slug", "template_employee"])

        if testing:
            return schedule

        return HttpResponseRedirect(schedule.url())


    def build_alternate_draft(request, schId):
        
        sch = Schedule.objects.get(slug=schId)
        c = Schedule.objects.filter(year=sch.year, number=sch.number).count()
        version = "ABCDEFGHIJ"[c]
        return ApiActionViews.build_schedule(
            request, sch.year, sch.number, version, sch.start_date
        )

    @csrf_exempt
    def delete_schedule(request, schId):

        if request.method == "DELETE":
            sch = Schedule.objects.get(slug=schId)
            sch.delete()
            return HttpResponseRedirect(reverse("schd:list"))
        return HttpResponse(f"REQUEST ERROR")

    @csrf_exempt
    def set__shift_img(request, shiftName):
        # get HX-PROMPT from headerp
        print(request.headers)
        url = request.session["Hx-Prompt"] = request.headers["Hx-Prompt"]
        sft = Shift.objects.get(name=shiftName)
        sft.image_url = url
        sft.save()
        return HttpResponseRedirect(sft.url())

    @csrf_exempt
    def ptoreq__delete(request, day, emp):

        day = dt.date(*[int(i) for i in day.split("-")])
        ptos = PtoRequest.objects.filter(workday=day, employee__slug=emp)
        if ptos:
            ptos.delete()
            return HttpResponse(f"Request for {emp} deleted")
        return HttpResponse(f"No request for {emp} found")

    @csrf_exempt
    def ptoreq__create(request, day, emp):

        emp = Employee.objects.get(slug=emp)
        day = dt.date(*[int(i) for i in day.split("-")])
        workdays = Workday.objects.filter(date=day, schedule__employees=emp)

        pto = PtoRequest.objects.create(workday=day, employee=emp)
        pto.workdays.set(workdays)
        pto.save()
        return HttpResponse(f"Request for {pto.employee.name} created")

    def clear_fte_overages(request, schId):

        sch = Schedule.objects.get(slug=schId)
        sch.clear_fte_overages()
        return HttpResponseRedirect(sch.url())

    def payPeriodFiller(request, schId):
        
        sch = Schedule.objects.get(slug=schId)
        for pd in sch.periods.all():
            empties = pd.slots.empty().all()
            empty_n_i = empties.count()
            empty_n_f = empty_n_i
            print(f"Checking {empties.count()} slots")
            empties.update()
            for e in empties:
                count = e.fills_with.count()
                if count > 0:
                    print(e, "  checking...")
                    empls = list(pd.needed_hours())
                    for empl in empls:
                        print(empl)
                        if e.fills_with.filter(name=empl).exists():
                            if e.workday.slots.filter(employee=empl).exists() == False:
                                e.employee = empl
                                print("    FILLING SLOT:", e, "with", empl)
                                empty_n_f -= 1
                                empties.bulk_update(empties, ["employee"])
                            else:
                                print(
                                    "    skipping employee because they already have a shift"
                                )
                        else:
                            print(
                                "  skipping employee because they are not trained for this shift"
                            )
                else:
                    print("  skipping slot because it is already filled")

        return HttpResponse(f"Filled {empty_n_i - empty_n_f} slots")

    def ignore_mistemplated_flag(request, slotId):
        slot = Slot.objects.get(slug=slotId)  # type :Slot
        slot.tags.add(slot.Flags.IGNORE_MISTEMPLATE_FLAG)
        slot.save()
        return HttpResponse(f"Muted")

    def flag_mistemplated(request, slotId):
        slot = Slot.objects.get(slug=slotId)
        slot.tags.remove(slot.Flags.IGNORE_MISTEMPLATE_FLAG)
        slot.save()
        return HttpResponse(f"Watching {slot} for mistemplating")


class VizViews:
    def tally_plot_data_generator(request, empId):
        from django.db.models import Count, OuterRef, Subquery
        import pandas as pd
        import seaborn as sns
        import matplotlib.pyplot as plt
        import urllib
        import base64
        from io import BytesIO
        import seaborn as sns
        import matplotlib.pyplot as plt
        from django.db.models import Sum

        # define a subquery that counts the occurrences of each employee/shift combination in the Slot model
        subquery = Subquery(
            Slot.objects.filter(employee=OuterRef("employee"), shift=OuterRef("shift"))
            .values("employee", "shift")
            .annotate(count=Count("*"))
            .values("count")[:1],
            output_field=models.IntegerField(),
        )
        # Count n of Slots, then if A ShiftPreference exists for that employee/shift combination
        emp = Employee.objects.get(name=empId)
        shift_prefs = emp.shift_prefs.annotate(count=subquery)

        score_subquery = Subquery(
            Slot.objects.filter(
                employee=OuterRef("employee"),
                shift=OuterRef("shift"),
            )
            .values("employee", "shift", "employee__shift_prefs__priority")
            .annotate(count=Count("*"))
            .values("count")[:1],
            output_field=models.IntegerField(),
        )
        sps = (
            shift_prefs.annotate(
                pref_score=Subquery(
                    ShiftPreference.objects.filter(
                        employee=OuterRef("employee"), shift=OuterRef("shift")
                    ).values("score")[:1]
                )
            )
            .annotate(score_count=Coalesce(score_subquery, 0))
            .values("score")
            .annotate(count=Sum("score_count"))
            .order_by("score")
        )

        data = []
        for j in sps:
            for n in range(j["count"]):
                data.append(j["score"])

        sns.kdeplot(data=data, fill=True, bw_adjust=1.5, cut=4, label=f"{emp.name}")
        sns.set_theme("paper", "dark")
        plt.style.use("dark_background")
        # change x label to "Dislike" at -3 and "Prefer" at 3
        plt.xticks([-3, 0, 3], ["Dislike", "Neutral", "Prefer"])

        emp = Employee.objects.get(name=empId)
        # change x labels to be from Dislike to Prefer
        plt.xticks([-2.5, 2.5], ["Dislike", "Prefer"])
        plt.title(f"{emp.name}'s Shift Preference Distribution")
        # save the figure to a buffer as SVG
        plt.legend(loc="upper left")
        buf = BytesIO()

        plt.savefig(buf, format="svg")
        plt.savefig(buf, format="svg")
        # get the SVG contents as bytes and encode to base64
        svg_bytes = buf.getvalue()
        svg_base64 = base64.b64encode(svg_bytes).decode("utf-8")
        return svg_base64
        # format the SVG string in an HTML <img> tag

        buf.close()

        return svg_html
