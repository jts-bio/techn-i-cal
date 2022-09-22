from django.test import TestCase
from .models import Workday, Shift, Employee, PtoRequest
import datetime as dt
# Create your tests here.

class DateCalcTests(TestCase):

    def test_iweekday (self):
        """
        Test the iweekday property of the Workday model
        """
        init = dt.date(2023,12,25)
        print("Testing iweekday")
        days = [init + dt.timedelta(days=i) for i in range(14)]
        for day in days:
            wd = Workday.objects.create(date=day)
            print("WD-",wd.iweekday, "// ",wd.date.strftime("%w %a %d %m"))
            self.assertEqual(wd.iweekday, int(day.strftime("%w")))

    def test_iperiod(self):
        """
        Test the iperiod property of the Workday model
        """
        init = dt.date(2023,12,1)
        print("Testing iperiod")
        days = [init + dt.timedelta(days=i) for i in range(62)]
        for day in days:
            wd = Workday.objects.create(date=day)
            print("PP-",wd.iperiod, "// ", wd.date.strftime("%w %a %d-%b"))
            