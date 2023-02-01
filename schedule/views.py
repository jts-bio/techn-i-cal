from django.shortcuts import render
from django.template.loader import render_to_string
from django.http import HttpResponse, JsonResponse, HttpResponseRedirect
from django.views.generic.base import TemplateView, RedirectView, View
from sch.models import generate_schedule 
import datetime as dt
from django.urls import reverse
from sch.forms import GenerateNewScheduleForm
from django.db.models import Count, Q

from sch.models import Schedule, Week, Slot, Employee, Shift

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
            {'title': 'EMUSR (SDfµ)',
             'goal': '< 1',
             'url': '{% url "sch:sch-calc-uf-distr" schedule.slug %}',
             'color': ['bg-red-500',
                       'bg-emerald-500'],
             'icon': 'fa fa-chart-bar'
             }, 
            {'title': None,
             'goal': None,
             'url': None,
             'color': None,
             'icon': None
             }
        ]
        return render(request, 'stats.html', {'schedule': sch, 'statPartials': statPartials})
    
    
    
class Actions:
    def clearOvertimeSlotsByRefillability (request,schId):
        sch = Schedule.objects.get (slug =schId )
        for empl in sch.employees.all():
            emplSlots = sch.slots.filter(employee=empl)
            emplSlots = emplSlots.annotate(n_fillableBy=Count(F('fills_with')))
            if sum(list(emplSlots.values_list('shift__hours',flat=True))) > 40:
                print(emplSlots.order_by('empl_sentiment','n_fillableBy'))

        
        