from django.shortcuts import render
from django.template.loader import render_to_string
from django.http import HttpResponse, JsonResponse, HttpResponseRedirect
from django.views.generic.base import TemplateView, RedirectView, View

from sch.models import Schedule, Week, Slot, Employee, Shift



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
    
    
    
        
        