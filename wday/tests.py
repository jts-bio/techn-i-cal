from django.test import TestCase

# Create your tests here.
from .views import empl_check_hours, empl_can_fill, workday_context
from sch.models import Workday, Employee

class CheckHoursVerificationTests (TestCase):

    def test_no_workday_slots(self):
    # Create a workday with no slots for any employee
        wd = Workday.objects.create(slug='test-wd')
        # Create an employee
        empl = Employee.objects.create(slug='test-empl')
        # Call the function with the workday and employee slugs
        response = empl_check_hours(None, 'test-wd', 'test-empl')
        # Check that the response contains 0 hours for both week and period
        assert response.content == b"(0/ 0 hrs)"