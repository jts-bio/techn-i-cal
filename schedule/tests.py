from django.test import TestCase
from sch.models import Schedule, Slot 
from flow.views import ApiActionViews
import datetime as dt
import requests

# Create your tests here.


class ScheduleSlotSlugTests (TestCase):
    """ Tests the functionality of setting of the slug field for a schedule slot """

    def test_slug_creation(self):
        build = ApiActionViews.build_schedule(
            year=2023, 
            num=1,
            version='A',
            start_date=Schedule.START_DATES[2023][0],
            testing=True
            )
        print (build.slots.values('slug'))