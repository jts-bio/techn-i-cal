from .models import *


def build_new_schedule_version (schId):
    sch = Schedule.objects.get(slug=schId)
    
    n = sch.versions.count()
    version_letter = "ABCDEFGHIJ"[n]
    version = Version.objects.create(schedule=sch, name=version_letter, percent=0)
    
    n_weeks = sch.organization.schedule_week_count
    n_prds  = sch.organization.schedule_period_count
    

    
    