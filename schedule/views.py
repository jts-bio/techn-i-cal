from django.shortcuts import render
from django.template.loader import render_to_string
from django.http import HttpResponse, JsonResponse, HttpResponseRedirect
from django.views.generic.base import TemplateView, RedirectView, View
from sch.models import generate_schedule 
import datetime as dt
from django.urls import reverse
from sch.forms import GenerateNewScheduleForm
from django.db.models import Count, Q
from flow.views import ApiViews
from django.views.decorators.csrf import csrf_exempt

from sch.models import Schedule, Week, Slot, Employee, Shift
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
        "schedules": schedules,
        "new_schedule_form": GenerateNewScheduleForm(),
    }
    return render(request, "sch-list.html", context)

def schDetailView (request, schId):
    sch = Schedule.objects.get (slug = schId )
    return render(request, 'sch-detail.html', {'schedule': sch})

class Sections: 
    
    def schStats (request, schId):
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
    
    def schMistemplated (request, schId):
        sch = Schedule.objects.get (slug = schId )
        data = ApiViews.schedule__get_mistemplated_list(request, schId).content
        data = json.loads(data)
        return render(request, 'tables/mistemplated.html', {'data': data})
    
    def schUnfavorables (request,schId):
        sch = Schedule.objects.get(slug=schId)
        data = ApiViews.schedule__get_unfavorables_list(request, schId).content
        data = json.loads(data)
        return render(request, 'tables/unfavorables.html', {'data': data})
    
    def schEmusr (request, schId):
        sch = Schedule.objects.get(slug=schId)
        data = ApiViews.schedule__get_emusr_list(request, schId).content
        data = json.loads(data)
        return render(request, 'tables/emusr.html', {'data': data}) 
class Actions:
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
            return HttpResponse("<div class='text-red-300 font-light'> Cleared </div>")
    
    def clearOvertimeSlotsByRefillability (request,schId):
        sch = Schedule.objects.get (slug =schId )
        for empl in sch.employees.all():
            emplSlots = sch.slots.filter(employee=empl)
            emplSlots = emplSlots.annotate(n_fillableBy=Count(F('fills_with')))
            if sum(list(emplSlots.values_list('shift__hours',flat=True))) > 40:
                print(emplSlots.order_by('empl_sentiment','n_fillableBy'))
                

        
        