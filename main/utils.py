from .models import *


def build_new_schedule_version (schId):
    sch = Schedule.objects.get(slug=schId)
    
    n = sch.versions.count()
    version_letter = "ABCDEFGHIJ"[n]
    version = Version.objects.create(schedule=sch, name=version_letter, percent=0)
    
    n_weeks = sch.organization.schedule_week_count
    n_prds  = sch.organization.schedule_period_count
    

    
def annotate_week_hours (ver):
    version = Version.objects.get(slug=ver)
    employees = version.schedule.employees.all()
    wkvals = version.workdays.values('wkid')
    pdvals = version.workdays.values('pdid')
    for empl in employees :
        for wk in wkvals:
            empl.week_hours = Slot.objects.filter(employee=empl, workday__version=version, workday__wkid=wk['wkid']).aggregate(Sum('shift__hours'))['shift__hours__sum']
        for pd in pdvals:
            empl.pd_hours = Slot.objects.filter(employee=empl, workday__version=version, workday__pdid=pd['pdid']).aggregate(Sum('shift__hours'))['shift__hours__sum']

    return employees.values('name','week_hours','pd_hours').order_by('-week_hours')