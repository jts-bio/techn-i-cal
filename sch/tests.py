from django.test import TestCase
from .models import Workday, Shift, Employee, PtoRequest
import datetime as dt
# Create your tests here.

class TestSlots (TestCase):
    
    def setUp(self):
        self.workdays = [Workday.objects.create(2022,10,i) for i in range(1,4)]
        self.shift    = Shift.objects.create(name='XAM', start=dt.time(8), duration=dt.timedelta(hours=8), occur_days='MTWRF')
        self.employee = Employee.objects.create(name='MARTHA', fte_14_day=80)
        
    def testTurnaroundDetection (self):
        self.assertEqual(self.shift.is_turnaround, False)
        self.shift.is_turnaround = True
        self.assertEqual(self.shift.is_turnaround, True)
        self.shift.is_turnaround = False
        self.assertEqual(self.shift.is_turnaround, False)
        
        
        
            