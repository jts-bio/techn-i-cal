python3 manage.py shell

from sch.models import *
from django.db.models import Subquery, Sum, F, Q, Count, Avg
import datetime as dt



date = Workday.objects.get(date=dt.date(2022, 9, 25))
date

shifts = Shift.objects.filter(occur_days__contains=date.iweekday)
slots = Slot.objects.filter(workday=date)
slots.first().employee

for shift in shifts:
    if slots.filter(shift=shift).exists():
        shift.employee = slots.filter(shift=shift).first().employee or None

shifts.values('employee')