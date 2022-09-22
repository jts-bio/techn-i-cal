python3 manage.py shell

from sch.models import *
from django.db.models import Subquery, Sum, F, Q, Count, Avg
import datetime as dt

today = Workday.objects.get(date=dt.date.today())

wd = Workday.objects.get(date=dt.date(2022,10,27))

Shift.objects.to_fill(today)

date = Workday.objects.get(date=dt.date(2022, 9, 25))
date

shifts = Shift.objects.filter(occur_days__contains=date.iweekday)
slots = Slot.objects.filter(workday=date)
slots.first().employee

