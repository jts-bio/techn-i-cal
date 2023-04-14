from django.shortcuts import render
from django.template.loader import render_to_string
from django.http import HttpRequest, HttpResponse, JsonResponse, HttpResponseRedirect
from django.views.generic.base import TemplateView, RedirectView, View
from sch.models import generate_schedule
import datetime as dt
from django.urls import reverse
from sch.forms import GenerateNewScheduleForm
from django.db.models import ( OuterRef, Subquery, Count,
                              Q, F, CharField, Avg, Sum, Case,
                              When, BooleanField, Value )
from django.db.models.functions import Coalesce, Concat
from flow.views import ApiViews
from django.views.decorators.csrf import csrf_exempt
from flow import views as flow_views

from django.db import models
from django.contrib import messages
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

from sch.models import Schedule, Week, Slot, Employee, Shift, PtoRequest, RoutineLog
from .tables import MistemplatedFlagIgnoreTable
import json
from django.db.models import Case, When, Sum, IntegerField
from django.contrib.postgres.aggregates import ArrayAgg
from django.contrib.postgres.fields import ArrayField
import random
from sch.data import Images

def schListView(request):
    """ 
    SCHEDULE LIST VIEW
    ==================
    This view is the main view for the schedule app. It displays a list of all
    schedules, and allows the user to generate new schedules.
    """
    VERSION_COLORS = {
            "A":  "amber",
            "B":  "emerald",
            "C":  "blue",
            "D":  "pink",
            "E":  "rose",
            "F":  "purple",
            "G":  "orange",
            "H":  "sky",
        }
    schedules = Schedule.objects.annotate(
        nEmpty=Count("slots", filter=Q(slots__employee=None))
    )
    
    for schedule in schedules:
        schedule.n_empty = schedule.nEmpty

    for sch in schedules:
        sch.versionColor = VERSION_COLORS[sch.version]

    if request.method == "POST":
        
        sd = request.POST.get("start_date")
        start_date = dt.date(int(sd[:4]), int(sd[5:7]), int(sd[8:]))
        idate = start_date
        year  = start_date.year
        i = Schedule.START_DATES[year].index(start_date) + 1
        s = Schedule.objects.filter(year=year,number=i).count()
        version = "ABCDEFGH"[s]
        
        flow_views.ApiActionViews.build_schedule (request, year, i, version, start_date)
        sch = Schedule.objects.get(year=year, number=i, version=version)
        
        return HttpResponseRedirect(sch.url())

    context = {
        "schedules": schedules.order_by("-start_date").exclude(status=2), # status 2 = discarded
        "new_schedule_form": GenerateNewScheduleForm(),
    }
    return render(request, "sch-list.html", context)


def groupedScheduleListView(request):
    yn_pairs = []
    for sch in Schedule.objects.all():
        yn_pairs.append((sch.year, sch.number))
        
    yn_dict = {}
    for pair in yn_pairs:
        yn_dict[f"{pair[0]}-{pair[1]}"] = []
    for sch in Schedule.objects.all():
        yn_dict[f"{sch.year}-{sch.number}"].append(sch)
        
    return render (request, "sch-list-grouped.html", {"schedules": yn_dict} )


def schDetailView(request, schId):
    sch = Schedule.objects.get(slug=schId)
    BACKGROUND_PATH = random.choice (Images.SEAMLESS_OPTIONS)
    
    if sch.status == 2:
        redirect_sch = Schedule.objects.get(year=sch.year, number=sch.number, status=1)
        messages.info (request, f"{sch.slug} is discarded; you were redirected to the published version {redirect_sch.version}")
        return HttpResponseRedirect (redirect_sch.url())
    prct = sch.percent 
    alternates = Schedule.objects.filter(
            year=sch.year, number=sch.number).exclude(pk=sch.pk).order_by('version').annotate(
            # ANNOTATE DIFFERENCE OF PERCENTS-FILLED
            difference= F('percent') - prct 
        )
    sch.save()
    return render (request, "sch-detail.pug", {
        "schedule":          sch, 
        "alternates":        alternates,
        "nextUrl":           sch.next().url() if sch.next() else None,
        "previousUrl":       sch.previous().url() if sch.previous() else None,
        "isBestVersionLink": reverse("flow:get_is_best_version", args=[schId]),
        "BACKGROUND_PATH":   BACKGROUND_PATH,
        }
    )


class Components: 
    
    def action_button(request):
        pass



class Sections:
    """
        contains fx:
        ```
        MODAL
        SCH STATS
        SCH MISTEMPLATED
        SCH UNFAVORABLES
        SCH PTOCONFLICTS
        SCH PTOGRID
        SCH EMUSR
        SCH EMPTYLIST 
        SCH EMUSRPAGE
        SCH OVER_FTE_FORM
        ```
    """
    
    def modal(request):
        return render(request, "modal.html")

    def schStats(request, schId):
        sch = Schedule.objects.get(slug=schId)
        statPartials = [
            dict(
                title="EMUSR (SDfµ)",
                name="emusr-sd",
                goal=[1, 1.01, 1.01],
                url="{% url 'sch:sch-calc-uf-distr' schedule.slug %}",
                icon="fa-chart-bar",
            ),
            dict(
                title="EMUSR",
                name="emusr",
                goal=[4, 8, 10],
                url="{% url 'sch:sch-calc-uf-distr' schedule.slug %}",
                icon="fa-moon",
            ),
            dict(
                title="Mistemplated",
                name="mistemplated",
                goal=[0, 0, 0],
                url="{% url 'sch:sch-mistemplated' schedule.slug %}",
                icon="fa-exclamation-triangle",
            ),
        ]
        
        statsHtml = ""
        for stat in statPartials:
            statsHtml += render_to_string("stats__figure.html", stat)
            
        return render(
            request, "stats.html", {"schedule": sch, "statPartials": statsHtml}
        )

    def sch_mistemplated(request, schId):
        sch = Schedule.objects.get(slug=schId)
        mistemplated_slots = ApiViews.schedule__get_mistemplated_list(request, schId).content
        mistemplated_slots = json.loads(mistemplated_slots)
        
        ignoring_mistemplate = sch.slots.filter(tags__name=Slot.Flags.IGNORE_MISTEMPLATE_FLAG)
        
        return render(request, "tables/mistemplated.html", {
            "data": mistemplated_slots, 
            "ignoring_mistemplate": ignoring_mistemplate
            })

    def schUnfavorables(request, schId):
        sch = Schedule.objects.get(slug=schId)
        unfavorable_slots = ApiViews.schedule__get_unfavorables_list(request, schId).content
        unfavorable_slots = json.loads(unfavorable_slots)
        return render(request, "tables/unfavorables.html", {"data": unfavorable_slots})

    def schPtoConflicts(request, schId):
        sch = Schedule.objects.get(slug=schId)
        pto_conflicts = sch.slots.conflictsWithPto().all()
        pto_requests = sch.pto_requests.all()
        return render(
            request,
            "tables/pto-conflicts.html",
            {"pto_requests": pto_requests, "schedule": sch, "pto_conflicts": pto_conflicts},
        )

    def schPtoGrid (request, schId, emp):
        sch = Schedule.objects.get(slug=schId)
        emp = Employee.objects.get(slug=emp)
        ptos = list(sch.pto_requests.filter(employee=emp).values_list('workday',flat=True))
        shifts = list(sch.slots.filter(employee=emp).values_list('workday',flat=True))
        
        days = sch.workdays.all()
        for day in days:
            day.is_pto = day.date in ptos
            day.is_shift = day in shifts
            
            if day.is_pto or day.is_shift:
                print(day.date, day.is_pto, day.is_shift)
        
        return render(request, "tables/empl-pto-grid.html", {
                "ptos": ptos,
                "sch": sch,
                "employee": emp,
                "days": days,
            })
        
    def schEmusr (request, schId):
        sch = Schedule.objects.get(slug=schId)
        data = ApiViews.schedule__get_emusr_list(request, schId).content
        data = json.loads(data)
        return render(request, "tables/emusr.html", {"data": data})

    def schEmptyList (request, schId):
        
        version = schId[-1]

        data = ApiViews.schedule__get_empty_list(request, schId)
        data = json.loads(data.content)
        for d in data:
            d["n_options"] = len(d["fills_with"])
            d["workday"] = d["workday"][0:10]
            d["workday_url"] = reverse("wday:detail", args=[f"{d['workday']}{version}"])

        # Add pagination
        page = request.GET.get('page', 1)
        paginator = Paginator(data, 20)  # Show 20 data per page
        try:
            for slot in paginator.page(page):
                Slot.objects.get(id=slot['id']).update_fills_with()
            data_paginated = paginator.page(page)
        except PageNotAnInteger:
            data_paginated = paginator.page(1)
        except EmptyPage:
            data_paginated = paginator.page(paginator.num_pages)   
            
        
            
        return render (request, "tables/emptys.pug", 
                            {"empty_slots": data_paginated, 
                            'paginator': paginator, 
                            'page': int(page), 
                            'pageNext':int(page)+1,
                            'totalPages':paginator.num_pages, 
                            'workday_version': version,
                            'schId': schId, 
                        })
    
    def schEmusrPage (request, schId):
        from django.db.models.functions import Coalesce

        sch = Schedule.objects.get(slug=schId)

        emusr_employees = sch.employees.emusr_employees()
        for empl in emusr_employees:
            empl.uf_count = sch.slots.filter(employee=empl, shift__start__hour__gte=10).count()
            
        return render(request, "tables/emusr.pug", {"emusr_employees": emusr_employees})
    
    def schEmployeeEmusrSlots(request, schId, emp):
        sch          = Schedule.objects.get( slug=schId)
        emp          = Employee.objects.get( slug=emp)
        slots        = sch.slots.filter( employee=emp, shift__start__hour__gte=10)
            
        return render (request, "tables/emusr-empl.pug",
            {
                "slots": slots,
                "n"    : slots.count() if slots.exists() else 0,
                "emp"  : emp, 
                "sch"  : sch, 
            },
        )
        
    def schUntrained(request, schId):
        sch = Schedule.objects.get(slug=schId)
        data = sch.slots.untrained().all()
        return render(request, "tables/untrained.html", {"data": data})
    
    def schLogView(request, schId):
        sch = Schedule.objects.get(slug=schId)
        return render(request, "components/timeline.pug", {"schedule": sch})
    
    def schTurnarounds(request, schId):
        sch = Schedule.objects.get(slug=schId)
        for turnaround in sch.slots.turnarounds().all():
            turnaround.save()
        turnarounds = sch.slots.turnarounds().preturnarounds().all()
        return render(request, "tables/turnarounds.pug", {"turnarounds": turnarounds, "sch": sch})

    def schOvertimeList(request, schId):
        sch = Schedule.objects.get(slug=schId)
        wk = sch.weeks.all()[0] #type: Week
        wk.overtime_hours()

    def sch_prn_empl_maxes(request,schId):
        template="tables/fte-maxes.pug"
        schedule = Schedule.objects.get(slug=schId)
        
        if request.method == "POST":
            print(request.POST)
            for emp in request.POST:
                if schedule.employees.filter(slug=emp).exists():
                    schedule.data['maxes'][emp] = request.POST[emp]
                    print(f">>> UPDATED {emp}: {request.POST[emp]}")
            schedule.save()
            messages.info(request, "Maxes Updated")
            return HttpResponseRedirect(schedule.url())
        
        return render(request, template, {
            "schedule": schedule,
            "maxes": schedule.data['maxes'].items()
            })
    


class Actions:
    """
    SCHEDULE :: ACTION PERFORMING VIEWS
    ====================================
    ```
    Updaters
        @ update_fills_with 
    @ clearUntrained
    @ clearUnfavorables
    @ setTemplates 
    @ retemplateAll
    """

    def publish_view (request, schId):
        sch = Schedule.objects.get(slug=schId)
        sch.actions.publish(sch)
        return HttpResponseRedirect(sch.url())
        
    def unpublish_view (request, schId):
        sch = Schedule.objects.get(slug=schId)
        sch.actions.unpublish(sch)        
        sch.routine_log.events.create(
            event_type='UNPUBLISH',
            data={
                'user': request.user.username
            }
        )
        return HttpResponse()

    class Updaters:

        def update_fills_with (request, schId):
            for slot in Schedule.objects.get(slug=schId).slots.empty():
                slot.update_fills_with()
            return HttpResponse(
                "<div class='text-lg text-emerald-400'><i class='fas fa-check'></i> Slot Availability Data Updated</div>"
            )
            

    def clear_untrained(request, schId):
        sch = Schedule.objects.get(slug=schId)
        
        n = sch.slots.untrained().count()
        sch.slots.untrained().update(employee=None)
        sch.routine_log.events.create(
            event_type='RESOLVE-TRAINING',
            data={
                'n': n,
                'user': request.user.username
            }
        )
        return HttpResponse(
            f"<div class='text-lg text-emerald-400'><i class='fas fa-check'></i> Untrained slots cleared</div>"
        )

    def clear_unfavorables(request, schId):
        sch = Schedule.objects.get(slug=schId)
        n_init = sch.slots.unfavorables().count()
        sch.slots.unfavorables().update(employee=None)
        n_final = sch.slots.unfavorables().count()
        n = n_init - n_final
        sch.routine_log.events.create(
            event_type='RESOLVE-UNFAVORABLES',
            data={
                'n': n,
                'user': request.user.username
            }
        )
        return HttpResponse(
            f'<div class="text-lg text-emerald-400"><i class="fas fa-check"></i>{n} Unfavorable slots cleared</div>'
        )

    def set_templates(request, schId):
        """
        BASE SET TEMPLATES FOR SCHEDULE
        -------------------------------
        Will set the templates for the schedule based on the employee's templates. 
        This function *will* consider context of PTO Requests.
        """

        sch = Schedule.objects.get(slug=schId)
        to_clear  = []
        to_update = []
        for employee in sch.employees.all():
            ptoreqs = employee.pto_requests.filter(workday__gte=sch.start_date, workday__lte=sch.end_date).values('sd_id')
            for tmpl in employee.shift_templates.exclude(sd_id__in=ptoreqs):
                slot = sch.slots.get(
                    workday__sd_id=tmpl.sd_id, shift=tmpl.shift)
                to_update.append(slot)
                slot.employee = employee
                if slot.siblings_day.filter(employee=employee).exists():
                        cslot = slot.siblings_day.filter(employee=employee).first()
                        to_clear.append(cslot)
                        cslot.employee = None
        sch.slots.bulk_update(to_clear, fields=('employee',))
        sch.slots.bulk_update(to_update, fields=('employee',))
        sch.routine_log.events.create(
            event_type='SET-TEMPLATES',
            data={
                'n_cleared': len(to_clear),
                'n'        : len(to_update),
                'user'     : request.user.username,
            }
        )
        return HttpResponse(
            f'<div class="text-lg text-emerald-400"><i class="fas fa-check"></i>{len(to_update)} Templates set</div>'
        )

    def fill_with_favorables(request, schId):
        from django.db.models import FloatField, Case, When, IntegerField

        tmpl_response     = Actions.set_templates(request, schId)
        ptoclear_response = Actions.clear_all_pto_conflicts(request, schId)

        n = 0
        schedule = Schedule.objects.get(slug=schId)
        time_i   = dt.datetime.now()
        results  = []
        slots    = schedule.slots.empty()
        weeks    = schedule.weeks.all()
        
        slots_subquery = slots.filter(
            employee=OuterRef('employee'), week=OuterRef('week')
            )
        
        employees = schedule.employees.annotate(
            weekHours_0=Subquery(weeks[0].slots.filter(employee=OuterRef('pk')).annotate(
                hours=Sum('shift__hours')).values('hours')),
            weekHours_1=Subquery(weeks[1].slots.filter(employee=OuterRef('pk')).annotate(
                hours=Sum('shift__hours')).values('hours')),
            weekHours_2=Subquery(weeks[2].slots.filter(employee=OuterRef('pk')).annotate(
                hours=Sum('shift__hours')).values('hours')),
            weekHours_3=Subquery(weeks[3].slots.filter(employee=OuterRef('pk')).annotate(
                hours=Sum('shift__hours')).values('hours')),
            weekHours_4=Subquery(weeks[4].slots.filter(employee=OuterRef('pk')).annotate(
                hours=Sum('shift__hours')).values('hours')),
            weekHours_5=Subquery(weeks[5].slots.filter(employee=OuterRef('pk')).annotate(
                hours=Sum('shift__hours')).values('hours'))
        )

        for slot in slots:
            empls = slot.fills_with.all().annotate(
                hours=Sum(slot.week.slots.filter(employee=F("pk")).aggregate(
                    week_hours=Sum(F('shift__hours'))
                        )['week_hours'], output_field=FloatField())
                        ).annotate(
                    hoursUnder=F('fte') * 40 - F('hours'),
                        ).annotate(
                    matchingTimePref=Case( When(time_pref=slot.shift.group, then=1),
                        default=0,
                    )
                        ).annotate(
                    hasPtoReq=Case( When(pto_requests__workday=slot.workday.date, then=1),
                        default=0,
                    )
                )
            ptoEmployees = slot.workday.on_pto()
            es = empls.filter(matchingTimePref=1).exclude(pk__in=slot.day_coworkers().all()).exclude(pk__in=ptoEmployees.all())
            print(es.values_list('name','hasPtoReq','hours','matchingTimePref'))
            
            if es.exists():
                emp = es.order_by('?').first()
                results.append(slot)
                slot.employee = emp
                week = slot.week
                week.hours[emp.slug] = sum(list(slot.week.slots.filter(
                    employee=emp).values_list('shift__hours', flat=True)))
                for sibslot in slot.siblings_day: 
                    sibslot.fills_with.remove(emp)
                if week.hours[emp.slug] > emp.fte * 40 - 5:
                    for s in slot.week.slots.filter(fills_with=emp):
                        s.fills_with.remove(emp)
                n+=1

        schedule.slots.bulk_update(results,fields=['employee']) 
        
        clear_maxes = Actions.sch_clear_over_empl_maxes(request, schId)
        
        time_f = dt.datetime.now()
        schedule.routine_log.events.create(
            event_type='SOLVE-ALGORITHM-A',
            data={
                'n': n,
                'time': f'{(time_f - time_i).seconds} seconds',
                'user': request.user.username
            }
        )
        return HttpResponse(
            f'<div class="text-lg text-emerald-400"><i class="fas fa-check"></i>{n} slots filled by favorability-maximizing strategy.</div>'
        )

    def wd_redirect(request, schId, wd):
        sch = Schedule.objects.get(slug=schId)
        wday = sch.workdays.get(slug__contains=wd)
        return HttpResponseRedirect(wday.url())

    @csrf_exempt
    def retemplate_all (request, schId):
        sch = Schedule.objects.get(slug=schId)
        slots = sch.slots.mistemplated()
        n = slots.count()
        for slot in slots:
            template_empl = slot.template_employee
            slot.siblings_day.filter(employee=template_empl).update(employee = None)
            slot.employee = template_empl
            slot.save()
        
        sch.routine_log.events.create(
            event_type='RETEMPLATE-ALL',
            data={
                'n': n,
                'user': request.user.username
            }
        )
        return HttpResponse(
            f"<div class='text-lg text-emerald-400'><i class='fas fa-check'></i> {slots.count()} slots retemplated</div>"
        )

    @csrf_exempt
    def solve_with_tca(request, schId):
        sch = Schedule.objects.get(slug=schId)
        if request.method == "POST":
            sch.actions.sch_solve_with_lookbehind(sch)
            return render(
                request,
                "data-responses/clearAll.html",
                {
                    "result": "success", 
                    "message": "Solved with TCA method"},
            )
        return render(
            request,
            "data-responses/clearAll.html",
            {
                "result": "error", 
                "message": "Invalid request method"},
        )

    @csrf_exempt
    def clear_all_pto_conflicts(request, schId):
        sch = Schedule.objects.get(slug=schId)
        n = 0
        
        time_i = dt.datetime.now()
        for s in sch.slots.conflictsWithPto().all():
            s.employee = None
            s.save()
            n += 1
        time_f = dt.datetime.now()
            
        sch.routine_log.events.create(
            event_type='CLEAR-PTO-CONFLICTS',
            data={
                'n': n,
                'duration': f'{(time_f - time_i).seconds} s',
                'user' : request.user.username
            }
        )
        return HttpResponse(f"<div class='text-lg text-emerald-400'><i class='fas fa-check'></i>{n} slots cleared</div>")

    @csrf_exempt
    def clear_all(request, schId):
        sch = Schedule.objects.get(slug=schId)
        
        if request.method == "POST":
            n = sch.slots.filled().count()
            sch.actions.clearSlots(sch)
    
            messages.success(request, "All slots cleared.")
            sch.routine_log.events.create(event_type='CLEAR-ALL',data={'n':n, 'user': request.user.username})
            
            context = {"result": "success", "message": "All slots cleared"}
            return render(request, "data-responses/clearAll.html",context)
            
        context = {"result": "error", "message": "Invalid request method"}
        return render(request, "data-responses/clearAll.html", context)

    @csrf_exempt
    def clear_slot(request, schId, wd, sft):
        sch = Schedule.objects.get(slug=schId)
        slot = Slot.objects.get(
            schedule=sch, workday__slug__contains=wd, shift__name=sft
        )  # type: Slot
        if request.method == "POST":
            res = slot.actions.clear_employee(slot)
            CHECKMARK = "<i class='fas fa-check'></i>"
            return HttpResponse(
                f"<div class='text-amber-300 text-2xs font-thin py-1'> {CHECKMARK} {res} </div>"
            )
        return HttpResponse(
            "<div class='text-red-300 text-2xs font-thin py-1'> ERROR (REQUEST METHOD) </div>"
        )

    @csrf_exempt
    def sch_clear_over_empl_maxes(request, schId): 
        sch = Schedule.objects.get(slug=schId)
        hours_cleared = 0
        for empl in sch.employees.all():
            if empl.slug in sch.data['maxes']:
                empl_max_hours = sch.data['maxes'][empl.slug]
            else:
                empl_max_hours = empl.fte * 40
                for week in sch.weeks.all():
                    while sum(list(week.slots.filter(employee=empl).values_list('shift__hours',flat=True))) > empl_max_hours:
                        slot = week.slots.filter(employee=empl).order_by('-fills_with__count').first()
                        slot.employee = None
                        hours_cleared += slot.shift.hours
                        slot.save()
                        
        messages.success(request, f'{hours_cleared}hrs cleared')
        return HttpResponseRedirect(sch.url())


    @csrf_exempt
    def override_slot(request, schId, wd, sft, empId):
        sch = Schedule.objects.get(slug=schId)
        empl = Employee.objects.get(slug=empId)
        print(request.method)
        if request.method == "POST":
            sch.slots.filter(workday__slug__contains=wd, employee=empl).update(
                employee=None
            )
            slot = sch.slots.get(workday__slug__contains=wd, shift__name=sft)
            slot.employee = empl
            slot.save()
            CHECKMARK = "<i class='fas fa-check'></i>"
            return HttpResponse(
                f"<div class='text-green-300 font-light'> {CHECKMARK} Updated </div>"
            )
        return HttpResponse(
            "<div class='text-red-300 text-2xs font-thin py-1'> ERROR (REQUEST METHOD) </div>"
        )

    @csrf_exempt
    def update_slot(request, schId, wd, sft, empl):
        employee = Employee.objects.get(slug=empl)
        sch = Schedule.objects.get(slug=schId)
        if isinstance(schId, int):
            slot = Slot.objects.get(
                schedule__pk=sch, workday__slug__contains=wd, shift__name=sft
            )
        else:
            slot = Slot.objects.get(
                schedule__slug=sch, workday__slug__contains=wd, shift__name=sft
            )
        if (
            slot.workday.slots.all()
            .filter(employee=employee)
            .exclude(shift=slot.shift)
            .exists()
        ):
            otherSlot = (
                slot.workday.slots.all()
                .filter(employee=employee)
                .exclude(shift=slot.shift)
                .first()
            )
            otherSlot.employee = None
            otherSlot.save()
        slot.employee = employee
        slot.save()
        CHECKMARK = "<i class='fas fa-check'></i>"
        return HttpResponse(
            f"<div class='text-green-300 font-light'>{CHECKMARK} Updated to {employee}</div>"
        )

    class EmusrBalancer:
        def select_max_min_employees(request, schId):
            
            emusr_data = flow_views.ApiViews.schedule__get_emusr_list(request, schId)
            
            data = json.loads(emusr_data.content)
            max_val = max(data.values())
            max_empl = [k for k, v in data.items() if v == max_val][0]
            min_val = min(data.values())
            min_empl = [k for k, v in data.items() if v == min_val][0]
            return JsonResponse({"max": max_empl, "min": min_empl})

        def get_tradable_slots(request, schId):
            tradables = []
            empls = json.loads(
                Actions.EmusrBalancer.select_max_min_employees(
                    request, schId).content
            )
            for slot in Slot.objects.filter(
                schedule__slug=schId, employee=empls["max"], is_unfavorable=True
            ):
                if empls["min"] in slot.fills_with.all():
                    tradables += [slot]
            return Slot.objects.filter(pk__in=[s.pk for s in tradables]).order_by(
                "empl_sentiment"
            )

    @csrf_exempt
    def clearOvertimeSlotsByRefillability(request, schId):
        n = 0
        sch = Schedule.objects.get(slug=schId)
        for week in sch.weeks.all():
            week.actions.update_hours(week)
            for empl in sch.employees.all():
                if week.hours[empl.slug] > 40:
                    print(f"{empl} has overtime")
                    emplSlots = week.slots.filter(employee=empl).annotate(
                        n_fillableBy=Count(F("fills_with")))  
                    print([(s.n_fillableBy, s.shift.name) for s in emplSlots])
                    while week.hours[empl.slug] > 40:
                        slots = emplSlots.order_by('-n_fillableBy')
                        if slots.count() > 0:
                            slot = slots.first()
                            slot.employee = None
                            slot.save()
                            n += 1
                            week.hours[empl.slug] -= slot.shift.hours
                            print(f"{empl} -{slot.shift.hours}hrs")
                        else:
                            print(f"Could not clear {empl} slots")
                            break
            else:
                print(f"{empl} has no overtime")
        return HttpResponse(f"{n} Overtime slots cleared")

    @csrf_exempt
    def clearPrnEmployeeSlots(request, schId):
        sch = Schedule.objects.get(slug=schId)  # type:Schedule
        prn_employees = sch.employees.prn_employees()
        prn_slots = sch.slots.filter(employee__in=prn_employees)
        n = prn_slots.count()
        prn_slots.update(employee=None)
        sch.save()
        if sch.routine_log:
            rl = sch.routine_log  # type:RoutineLog
            rl.add("Clear PRN Employee Slots", f"{n} slots cleared", {
                'prn_employees': f'{prn_employees.count()}',
                'slots_cleared': f'{n}',
                'schedule %': sch.percent,
                })
        return HttpResponse(f"PRN employees cleared from {n} slots")

    @csrf_exempt
    def publish_schedule(request, pk):
        schedule = Schedule.objects.get(pk=pk)
        schedule.actions.publish(schedule)
        other_versions = Schedule.objects.filter(year=schedule.year, number=schedule.number).exclude(pk=schedule.pk)
        other_versions.update(published=False)
        schedule.status
        schedule.routine_log.events.create(
            event_type='PUBLISH',
            data={
                'user': request.user.username
            }
        )
        return HttpResponse(f"Schedule published")