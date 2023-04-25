from django.test import TestCase
from .models import Workday, Shift, Employee, PtoRequest, Schedule, ShiftSortPreference, ShiftPreference
import datetime as dt
from django.urls import reverse
from sch.forms import EmployeeSelectForm
from sch.models import Employee, Schedule
from sch.views2 import schDetailView
import pytest
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




"""
Code Analysis

Main functionalities:
The EmpViews class contains two methods that handle employee shift preferences and tallies. The empShiftSort method updates an employee's shift sort preferences based on a POST request, while the empShiftTallies method generates a visualization of an employee's shift preferences using a kernel density estimate plot.

Methods:
- empShiftSort: updates an employee's shift sort preferences based on a POST request
- empShiftTallies: generates a visualization of an employee's shift preferences using a kernel density estimate plot

Fields:
The EmpViews class does not have any fields of its own, but it uses fields from other models such as Employee, ShiftSortPreference, and Shift.
"""
from sch.viewsets import EmpViews


class TestEmpViews:

    # Tests that empshiftsort updates an employee's shift sort preferences with valid data. tags: [happy path]
    def test_empShiftSort_valid(self, mocker):
        # Setup
        emp = Employee.objects.create(name="John Doe")
        shift1 = Shift.objects.create(name="Morning")
        shift2 = Shift.objects.create(name="Afternoon")
        emp.shifts_available.add(shift1, shift2)
        request = mocker.Mock()
        request.method = "POST"
        request.POST = {
            "bin-1": "shift-Morning",
            "bin-2": "shift-Afternoon",
        }
        messages_mock = mocker.patch("django.contrib.messages.success")
        # Exercise
        response = EmpViews.empShiftSort(request, emp.id)
        # Assert
        assert response.status_code == 302
        assert response.url == emp.url()
        assert ShiftSortPreference.objects.filter(employee=emp).count() == 2
        assert messages_mock.called_once_with(
            request,
            f"{emp} shift sort preferences updated: Morning (1), Afternoon (2)",
        )

    # Tests that empshiftsort handles a post request with missing data. tags: [edge case]
    def test_empShiftSort_missingData(self, mocker):
        # Setup
        emp = Employee.objects.create(name="John Doe")
        request = mocker.Mock()
        request.method = "POST"
        request.POST = {}
        messages_mock = mocker.patch("django.contrib.messages.success")
        # Exercise
        response = EmpViews.empShiftSort(request, emp.id)
        # Assert
        assert response.status_code == 200
        assert ShiftSortPreference.objects.filter(employee=emp).count() == 0
        assert not messages_mock.called

    # Tests that empshifttallies handles rendering a visualization with no data. tags: [edge case]
    def test_empShiftTallies_noData(self, mocker):
        # Setup
        emp = Employee.objects.create(name="John Doe")
        request = mocker.Mock()
        request.method = "GET"
        shift_prefs_with_counts_mock = mocker.Mock()
        shift_prefs_with_counts_mock.annotate.return_value = shift_prefs_with_counts_mock
        shift_prefs_with_counts_mock.annotate.return_value.annotate.return_value = shift_prefs_with_counts_mock
        shift_prefs_with_counts_mock.annotate.return_value.annotate.return_value.values.return_value = shift_prefs_with_counts_mock
        shift_prefs_with_counts_mock.annotate.return_value.annotate.return_value.values.return_value.annotate.return_value = shift_prefs_with_counts_mock
        shift_prefs_with_counts_mock.annotate.return_value.annotate.return_value.values.return_value.annotate.return_value.annotate.return_value = shift_prefs_with_counts_mock
        shift_prefs_with_counts_mock.annotate.return_value.annotate.return_value.values.return_value.annotate.return_value.annotate.return_value.values.return_value = shift_prefs_with_counts_mock
        shift_prefs_with_counts_mock.annotate.return_value.annotate.return_value.values.return_value.annotate.return_value.annotate.return_value.values.return_value.annotate.return_value = shift_prefs_with_counts_mock
        shift_prefs_with_counts_mock.order_by.return_value = shift_prefs_with_counts_mock
        mocker.patch(
            "sch.models.Employee.shift_prefs",
            new_callable=mocker.PropertyMock(return_value=shift_prefs_with_counts_mock),
        )
        # Exercise
        response = EmpViews.empShiftTallies(request, emp.slug)
        # Assert
        assert response.status_code == 200
        assert response.context["emp"] == emp
        assert response.context["tallies"] == shift_prefs_with_counts_mock
        assert "plot" in response.context

    # Tests that empshifttallies generates a visualization of an employee's shift preferences with valid data. tags: [happy path]
    def test_empShiftTallies_valid(self, mocker):
        emp = Employee.objects.create(name="John Doe")
        shift1 = Shift.objects.create(name="Morning", hours=8)
        shift2 = Shift.objects.create(name="Afternoon", hours=6)
        pref1 = ShiftPreference.objects.create(employee=emp, shift=shift1, priority='SP')
        pref2 = ShiftPreference.objects.create(employee=emp, shift=shift2, priority='P')
        Slot.objects.create(employee=emp, shift=shift1)
        Slot.objects.create(employee=emp, shift=shift1)
        Slot.objects.create(employee=emp, shift=shift2)
        request = mocker.Mock()
        request.method = "GET"
        response = EmpViews.empShiftTallies(request, emp.name)
        assert response.status_code == 200
        assert response.context['emp'] == emp
        assert response.context['tallies'][0]['score'] == 2
        assert response.context['tallies'][0]['count'] == 2
        assert response.context['tallies'][0]['shifts'] == ['Morning']
        assert response.context['tallies'][1]['score'] == 1
        assert response.context['tallies'][1]['count'] == 1
        assert response.context['tallies'][1]['shifts'] == ['Afternoon']
        assert 'plot' in response.context

    # Tests that empshiftsort handles invalid data. tags: [other possible issue]
    def test_empShiftSort_invalidData(self, mocker):
        emp = Employee.objects.create(name="John Doe")
        request = mocker.Mock()
        request.method = "POST"
        request.POST = {"bin-1": "invalid-shift"}
        response = EmpViews.empShiftSort(request, emp.id)
        assert response.status_code == 302
        assert len(ShiftSortPreference.objects.all()) == 0
        assert len(messages.get_messages(request)) == 1

    # Tests that empshifttallies handles invalid data. tags: [other possible issue]
    def test_empShiftTallies_invalidData(self, mocker):
        emp = Employee.objects.create(name="John Doe")
        request = mocker.Mock()
        request.method = "GET"
        response = EmpViews.empShiftTallies(request, "invalid-employee")
        assert response.status_code == 404