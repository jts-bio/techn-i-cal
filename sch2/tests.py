from django.test import TestCase
from .models import *

# Create your tests here.

def setUp ():
    mi = Shift.objects.create(
        name='MI',cls="CPhT",start=dt.time(6,30),group='AM',hours=10,is_iv=True,duration=dt.timedelta(hours=10,minutes=30))
    mi.save()
    c7 = Shift.objects.create(
        name='7C',cls="CPhT",start=dt.time(7),group='AM',hours=10,is_iv=True,duration=dt.timedelta(hours=10,minutes=30))
    c7.save()
    p7 = Shift.objects.create(
        name='7P',cls="CPhT",start=dt.time(7),group='AM',hours=10,is_iv=False,duration=dt.timedelta(hours=10,minutes=30))
    p7.save()
    s = Shift.objects.create(
        name='S',cls="CPhT",start=dt.time(8),group='AM',hours=10,is_iv=True,duration=dt.timedelta(hours=10,minutes=30),occur_days=[])
    
    