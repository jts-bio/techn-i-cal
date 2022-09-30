from sch.models import *
from django.db.models import Subquery, Sum, F, Q, Count, Avg
import datetime as dt

today = Workday.objects.get(date=dt.date.today())


