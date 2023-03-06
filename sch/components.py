from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render_to_response, render 





class BasicSpeedDial:
    
    def __init__(self):
        self.options = []
        
    def addOption(self, name, url, method, icon, color):
        self.options.append({'name': name, 'url': url, 'method': method, 'icon': icon, 'color': color})
    
    def render(self, request):
        return render(request, 'sch3/basicSpeedDial.html', {'options': self.options})
        
    
 