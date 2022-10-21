from django.shortcuts import render
from .models import *
from django.db.models import Q, F, Sum, Subquery,OuterRef

# Create your views here.
# import Left



class PREPMODE:

    def letterView (request):
        letters = Drug.objects.all().annotate(
            firstLetter = Subquery(Drug.objects.filter(name__startswith = OuterRef('name')).order_by('name')[:1].values('name'))
        )
        return render (request, 'pds/prep/letters.html', {'letters':letters})
    
    
class PARTIALS:
    
    def icon_A (request, iconName, text):
        icon = file = open('pds/templates/pds/icons/' + iconName + '.svg').read()
        
        return render (request, 'pds/icons.html', {'icon': icon, 'text':text})
        