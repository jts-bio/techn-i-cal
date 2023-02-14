from django.shortcuts import render
from django.template.loader import render_to_string
from django.http import HttpRequest, HttpResponse, JsonResponse, HttpResponseRedirect
from django.views.generic.base import TemplateView, RedirectView, View
from sch.models import generate_schedule 
import datetime as dt
from django.urls import reverse
from sch.forms import GenerateNewScheduleForm
from django.db.models import Count, Q, F
from flow.views import ApiViews
from django.views.decorators.csrf import csrf_exempt

from sch.models import Schedule, Week, Slot, Employee, Shift, PtoRequest
import json


def schListView(request):
    VERSION_COLORS = {
        'A': 'amber',
        'B': 'emerald',
        'C': 'blue',
        'D': 'pink',
    }
    schedules = Schedule.objects.annotate(nEmpty=Count('slots', filter=Q(slots__employee=None)))
    for schedule in schedules:
        schedule.n_empty = schedule.nEmpty

    for sch in schedules:
        sch.versionColor = VERSION_COLORS[sch.version]

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
        return HttpResponseRedirect(reverse("schd:list"))

    context = {
        "schedules": schedules.order_by('-start_date'),
        "new_schedule_form": GenerateNewScheduleForm(),
    }
    return render(request, "sch-list.html", context)

def schDetailView (request, schId):
    sch = Schedule.objects.get (slug = schId )
    sch.save()
    return render(request, 'sch-detail.html', {'schedule': sch})

class Sections: 
    
    def modal (request):
        return render(request, 'modal.html')
    
    def schStats (request, schId ):
        sch = Schedule.objects.get (slug = schId )
        statPartials = [ 
            dict(title="EMUSR (SDfµ)", name="emusr-sd",
                 goal=[1,1.01,1.01], url="{% url 'sch:sch-calc-uf-distr' schedule.slug %}",
                 icon='fa-chart-bar'),
            dict(title="EMUSR",name="emusr",
                 goal=[4,8,10], url="{% url 'sch:sch-calc-uf-distr' schedule.slug %}",
                 icon='fa-moon'),
            dict(title="Mistemplated", name="mistemplated", 
                 goal=[0,0,0], url="{% url 'sch:sch-mistemplated' schedule.slug %}",
                 icon="fa-exclamation-triangle")
        ]
        statsHtml = ""
        for stat in statPartials:
            statsHtml += render_to_string('stats__figure.html', stat)
        return render(request, 'stats.html', {'schedule': sch, 'statPartials': statsHtml})
    
    def schMistemplated (request, schId ):
        sch = Schedule.objects.get (slug = schId )
        data = ApiViews.schedule__get_mistemplated_list(request, schId).content
        data = json.loads(data)
        return render(request, 'tables/mistemplated.html', {'data': data})
    
    def schUnfavorables (request,schId):
        sch = Schedule.objects.get(slug=schId )
        data = ApiViews.schedule__get_unfavorables_list(request, schId).content
        data = json.loads(data)
        return render(request, 'tables/unfavorables.html', {'data': data})
    
    def schPtoConflicts (request,schId):
        sch = Schedule.objects.get(slug=schId )
        data = sch.slots.conflictsWithPto().all()
        return render(request, 'tables/pto-conflicts.html', {'data': data, 'schedule': sch})
    
    def schPtoGrid (request, schId, emp):
        sch = Schedule.objects.get(slug=schId )
        emp = Employee.objects.get(slug=emp)
        ptoreqs = PtoRequest.objects.filter(employee=emp, workday__gte=sch.start_date, workday__lte=sch.start_date + dt.timedelta(days=42))
        return render(request, 'pto-chart.html', {'ptoreqs': ptoreqs, 'sch': sch, 'empl': emp })
    
    def schEmusr (request, schId):
        sch = Schedule.objects.get(slug=schId )
        data = ApiViews.schedule__get_emusr_list(request, schId).content
        data = json.loads(data)
        return render(request, 'tables/emusr.html', {'data': data }) 
    def schEmptyList (request,schId ):
        if request.headers.get('page'):
            page = int(request.headers.get('page'))
        else:
            page = 1
        version = schId[-1]
        data = ApiViews.schedule__get_empty_list(request,schId)
        data = json.loads(data.content)
        for d in data:
            d['n_options'] = len(d['fills_with'])
            d['workday_slug'] = d['workday'] + version
        return render(request, 'tables/empty-actionable.html', {'data': data })
    def schUntrained (request, schId):
        sch = Schedule.objects.get(slug=schId )
        data = sch.slots.untrained().all()
        return render(request, 'tables/untrained.html', {'data': data})
    
class Actions:
    
    def wdRedirect (request, schId, wd):
        sch = Schedule.objects.get (slug = schId )
        wday = sch.workdays.get(slug__contains=wd)
        return HttpResponseRedirect(wday.url())
    
    def retemplateAll (request, schId):
        sch = Schedule.objects.get (slug = schId )
        n = 0
        for slot in sch.slots.filter(template_employee__isnull=False):
            emp = slot.template_employee
            if slot.employee != emp:
                n += 1
                slot.workday.slots.filter(employee=emp).update(employee=None)
                slot.employee = emp
                slot.save()
        return HttpResponse(f"<div class='text-lg text-emerald-400'><i class='fas fa-check'></i> {n} slots retemplated</div>")
    
    @csrf_exempt
    def solveTca (request, schId):
        sch = Schedule.objects.get (slug = schId )
        if request.method == "POST":
            sch.actions.sch_solve_with_lookbehind(sch)
            return render(request, 'data-responses/clearAll.html', {'result': 'success','message': 'TCA solved'})
        return render(request, 'data-responses/clearAll.html', {'result': 'error','message': 'Invalid request method'})
    
    @csrf_exempt
    def clearAll (request, schId):
        sch = Schedule.objects.get (slug = schId )
        if request.method == "POST":
            sch.actions.deleteSlots(sch)
            return render(request, 'data-responses/clearAll.html', {'result': 'success','message': 'All slots cleared'})
        return render(request, 'data-responses/clearAll.html', {'result': 'error','message': 'Invalid request method'})
    
    @csrf_exempt
    def clearSlot (request, schId, wd, sft):
        sch = Schedule.objects.get (slug = schId )
        slot = Slot.objects.get (schedule=sch,workday__slug__contains=wd, shift__name=sft)
        if request.method == "POST":
            slot.actions.clear_employee(slot)
            CHECKMARK = "<i class='fas fa-check'></i>"
            return HttpResponse(f"<div class='text-amber-300 text-2xs font-thin py-1'> {CHECKMARK} CLEARED </div>")
        return HttpResponse("<div class='text-red-300 text-2xs font-thin py-1'> ERROR (REQUEST METHOD) </div>")
    
    @csrf_exempt
    def overrideSlot (request, schId, wd, sft, empId):
        sch = Schedule.objects.get (slug = schId)
        empl = Employee.objects.get (slug = empId)
        if request.method == "POST":
            sch.slots.filter(workday__slug__contains=wd, employee=empl).update(employee=None)
            slot = sch.slots.get (workday__slug__contains=wd, shift__name=sft)
            slot.employee = empl
            slot.save()
            CHECKMARK = "<i class='fas fa-check'></i>"
            return HttpResponse(f"<div class='text-green-300 font-light'> {CHECKMARK} Updated </div>")
        return HttpResponse("<div class='text-red-300 text-2xs font-thin py-1'> ERROR (REQUEST METHOD) </div>")
    
    
    @csrf_exempt
    def updateSlot(request,schId,wd,sft,empl):
        employee = Employee.objects.get(slug=empl)
        slot = Slot.objects.get (schedule=schId,workday__slug__contains=wd, shift__name=sft)
        if slot.workday.slots.all().filter(employee=employee).exclude(shift=slot.shift).exists():
            otherSlot = slot.workday.slots.all().filter(employee=employee).exclude(shift=slot.shift).first()
            otherSlot.employee= None
            otherSlot.save()
        slot.employee = employee
        slot.save()
        CHECKMARK = "<i class='fas fa-check'></i>"
        return HttpResponse(f"<div class='text-green-300 font-light'>{CHECKMARK} Updated </div>")
        
    
    
    def clearOvertimeSlotsByRefillability (request,schId):
        sch = Schedule.objects.get (slug =schId )
        for empl in sch.employees.all():
            emplSlots = sch.slots.filter(employee=empl)
            emplSlots = emplSlots.annotate(n_fillableBy=Count(F('fills_with')))
            if sum(list(emplSlots.values_list('shift__hours',flat=True))) > 40:
                print(emplSlots.order_by('empl_sentiment','n_fillableBy'))
                

        
        