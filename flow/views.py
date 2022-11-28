from django.shortcuts import render, HttpResponse, HttpResponseRedirect
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Count
from django.urls import reverse_lazy
from django.views.generic.detail import DetailView
from django.views.generic.list import ListView
from django.views.generic.edit import UpdateView, DeleteView, FormView
from django.forms import formset_factory
from django.contrib import messages, admin
from django.contrib.auth.forms import UserCreationForm 
from django.http import JsonResponse

from django.db.models import Q, F, Sum, Subquery, OuterRef, Count
from django_tables2 import RequestConfig
import datetime as dt
from .models import *



def weekView (request, year, week):
    week = Week.objects.filter(year=year, number=week).first()
    week.save()
    context = {
        'week': week,
        'workdays': week.workdays.all(),
    }
    return render(request, 'sch2/week/wk-detail.html', context)

@csrf_exempt
def weekView__set_ssts (request, year, week):
    """
    If SST exists and filling employee is appropriate, Slot is filled.
    Exceptions that will result in no change:
        - empl has ptoreq
        - empl would go overtime 
        - empl in conflicting slot
    """
    if request.method == "POST":
        week = Week.objects.filter(year=year, number=week).first()
        for day in week.workdays.all():
            for slot in day.slots.all():
                slot.set_sst()
        return HttpResponseRedirect(reverse_lazy('wk-details', kwargs={'year': year, 'week': week.number}))
