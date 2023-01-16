from django import template
import datetime as dt

register = template.Library()

@register.simple_tag
def weekHours (empl, week):
    """ 
    EMPLOYEE WEEKLY HOURS 
    """
    if empl == "":
        return 0
    hrs = empl.weekHours(week)
    if hrs == None:
        return 0
    return int(hrs)

@register.simple_tag
def periodHours (empl, period):
    """ 
    EMPLOYEE PERIOD HOURS 
    """
    if empl == "":
        return 0
    hrs = empl.periodHours(period)
    if hrs == None:
        return 0
    return int(hrs)