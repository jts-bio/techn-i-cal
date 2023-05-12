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

@register.simple_tag
def isSlotted (empl, wd):
    """ 
    CHECK EMPLOYEE IS SLOTTED ON WORKDAY
    """
    if empl in wd.slots.filled().filter(employee=empl).values('employee'):
        return True
    return False

@register.simple_tag
def getAllowedFills (empl, wd):
    if sum(list(wd.period.slots.filter(employee=empl).values_list('shift__hours', flat=True))) > (empl.fte * 80) :
        return None 
    fills = empl.shifts_available.all()
    if wd.sd_id != 0:
        if wd.prevWD().slots.filter(employee=empl).exists():
            pg = wd.prevWD().slots.get(employee=empl).shift.group 
            if pg in ["PM","XN"]:
                fills = fills.exclude(name__in=["AM","XN"])
    if wd.sd_id != 41:
        if wd.nextWD().slots.filter(employee=empl).exists():
            ng = wd.nextWD().slots.get(employee=empl).shift.group
            if ng in ["AM"]:
                fills = fills.exclude(name__in=["PM","XN"])
    return " ".join([f"allowed-to-fill-{f.name}" for f in fills])