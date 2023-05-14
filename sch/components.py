from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render 
from django.template.loader import render_to_string
import re


class BasicSpeedDial:
    
    def __init__(self):
        self.options = []
        
    def add_option(
            self, 
            name, 
            url, 
            method="POST", 
            icon="fa-plus", 
            color="text-slate-500"):
        
        if not icon.startswith('fa-'): 
            icon = 'fa-' + icon
        if not color.startswith('bg-'):
            color = 'bg-' + color
        if not re.findall(r'-\d\d\d', color):
            color = color + '-500'
        self.options.append( {
            'name': name, 
            'url': url, 
            'method': method, 
            'icon': icon, 
            'color': color
            } )
    
    def render( self ) -> str :
        return render_to_string('sch3/speedDial.html', {'options': self.options} )


workday_speed_dial_menu = BasicSpeedDial()
workday_speed_dial_menu.add_option(
            name= "Solve",
            url=  "solve/",
            icon= "robot-user",
            color="zinc-300"
            )
