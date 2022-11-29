from django.shortcuts import render
from .models import *
from django.db.models import Q, F, Sum, Subquery,OuterRef

# Create your views here.
# import Left



def testSortable (request):
    template = 'pds/sort.html'
    
    context = {
        'shifts': 'MI 7C 7P OP S EI EP 3 N'.split(" "),
    }
    return render(request, template, context)