from django.test import TestCase
from .models import Workday, Shift, Employee, PtoRequest
import datetime as dt
from django.urls import reverse
from sch.forms import EmployeeSelectForm
from sch.models import Employee, Schedule
from sch.views2 import schDetailView
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

"""
Code Analysis

Objective:
The objective of the schDetailView function is to display the details of a schedule and provide a form to select an employee for that schedule. Once an employee is selected, the function redirects to another view to display the employee's PTO schedule for the selected schedule.

Inputs:
- request: the HTTP request object
- schId: the slug of the schedule to display

Flow:
1. Get the Schedule object with the given slug (schId).
2. If the request method is POST, validate the EmployeeSelectForm and redirect to the PTO schedule view for the selected employee.
3. If the form is invalid, display a warning message.
4. Create a context dictionary with the schedule object, all employees, the EmployeeSelectForm, and other schedules (excluding the current one).
5. Render the sch-detail.html template with the context.

Outputs:
- Rendered HTML template with the schedule details and employee selection form.

Additional aspects:
- The function uses the reverse function to generate the URL for the PTO schedule view.
- The function uses the messages framework to display warning messages.
- The function excludes the current schedule from the list of other schedules to display.
"""



class TestSchdetailview(TestCase):

    # Tests that a valid get request with an existing schedule id returns the correct schedule details. tags: [happy path]
    def test_valid_GET_request(self, mocker):
        # Setup
        schedule = Schedule.objects.create(slug="test-schedule")
        url = reverse("sch:v2-schedule-detail", args=[schedule.slug])
        request = mocker.Mock()
        request.method = "GET"
        request.user = mocker.Mock()
        request.user.is_authenticated = True

        # Exercise
        response = schDetailView(request, schedule.slug)

        # Assert
        assert response.status_code == 200
        assert response.context["schedule"] == schedule

    # Tests that the current schedule is excluded from the list of other schedules. tags: [happy path]
    def test_exclude_current_schedule(self, mocker):
        # Setup
        schedule1 = Schedule.objects.create(slug="test-schedule-1")
        schedule2 = Schedule.objects.create(slug="test-schedule-2")
        url = reverse("sch:v2-schedule-detail", args=[schedule1.slug])
        request = mocker.Mock()
        request.method = "GET"
        request.user = mocker.Mock()
        request.user.is_authenticated = True

        # Exercise
        response = schDetailView(request, schedule1.slug)

        # Assert
        assert response.status_code == 200
        assert schedule1 not in response.context["otherSchedules"]
        assert schedule2 in response.context["otherSchedules"]

    # Tests that an invalid post request with invalid form data displays a warning message. tags: [edge case]
    def test_invalid_POST_request(self, mocker):
        # Setup
        schedule = Schedule.objects.create(slug="test-schedule")
        url = reverse("sch:v2-schedule-detail", args=[schedule.slug])
        request = mocker.Mock()
        request.method = "POST"
        request.user = mocker.Mock()
        request.user.is_authenticated = True
        form_data = {"employee": None}
        form = EmployeeSelectForm(data=form_data)
        form.is_valid = mocker.Mock(return_value=False)

        # Exercise
        response = schDetailView(request, schedule.slug)

        # Assert
        assert response.status_code == 200

    # Tests that an invalid get request with a non-existing schedule id returns an error message. tags: [edge case]
    def test_invalid_GET_request(self, mocker):
        # Mocking Schedule.objects.get() to return DoesNotExist error
        mocker.patch('sch2.views.Schedule.objects.get', side_effect=Schedule.DoesNotExist)
        
        # Making a GET request with a non-existing schedule id
        response = self.client.get(reverse('sch:v2-schedule-detail', args=['non-existing-id']))
        
        # Asserting that the response status code is 404 and the error message is displayed
        assert response.status_code == 404
        assert 'Schedule matching query does not exist' in str(response.content)

    # Tests that the form validation works correctly. tags: [other possible issue]
    def test_form_validation(self):
        # Creating a valid form data
        form_data = {'employee': Employee.objects.first().pk}
        
        # Making a POST request with the valid form data
        response = self.client.post(reverse('sch:v2-schedule-detail', args=[Schedule.objects.first().slug]), data=form_data)
        
        # Asserting that the response redirects to the correct URL
        assert response.status_code == 302
        assert response.url == reverse('sch:v2-schedule-empl-pto', args=[Schedule.objects.first().pk, Employee.objects.first().pk])

    # Tests that the reverse url generation works correctly. tags: [other possible issue]
    def test_reverse_URL_generation(self):
        # Generating a reverse URL for the schDetailView function
        url = reverse('sch:v2-schedule-detail', args=[Schedule.objects.first().slug])
        
        # Asserting that the generated URL is correct
        assert url == f'/schedule/{Schedule.objects.first().slug}/'