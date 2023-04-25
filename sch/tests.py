from django.test import TestCase
from sch.models import Workday, Shift, Employee, PtoRequest, Schedule, ShiftSortPreference, ShiftPreference
from datetime import datetime, timedelta
from django.urls import reverse
from sch.forms import EmployeeSelectForm
from sch.models import Employee, Schedule
from sch.views2 import schDetailView
import pytest
# Create your tests here.



class EmployeeTestCase(TestCase):

    def setUp(self):
        # create some test employees
        self.emp1 = Employee.objects.create(name='John Smith', fte_14_day=80, streak_pref=3)
        self.emp2 = Employee.objects.create(name='Jane Doe', fte_14_day=60, streak_pref=2)

    def test_yrs_experience(self):
        # test that the years of experience property returns the expected value
        emp = Employee.objects.create(name='Bob Smith', hire_date=datetime.now() - timedelta(days=365*3))
        self.assertEqual(emp.yrs_experience, 3)

    def test_fte_calculation(self):
        # test that the FTE calculation is correct
        self.assertEqual(self.emp1.fte, 1.0)
        self.assertEqual(self.emp2.fte, 0.75)

    def test_details_on_day(self):
        # test the details_on_day method returns the expected values
        emp = Employee.objects.create(name='Alice Smith')
        # assume the employee has worked 5 hours on Monday
        emp.dayHours = lambda wd: 5 if wd.weekday() == 0 else None
        # assume the employee has worked 20 hours this week so far
        emp.weekHours = lambda wd: 20 if wd < datetime.now() else None
        # assume the employee has worked 60 hours this period so far
        emp.periodHours = lambda wd: 60 if wd < datetime.now() else None
        # test that the details on Monday are as expected
        details = emp.details_on_day(datetime.now() - timedelta(days=1))
        self.assertEqual(details['day_hours'], 5)
        self.assertEqual(details['wk_hours'], 15)
        self.assertEqual(details['pd_hours'], 55)


