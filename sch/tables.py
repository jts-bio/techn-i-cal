from django_tables2 import tables
from django_tables2.utils import A

from .models import PtoRequest, Shift, Employee, Workday, Slot, ShiftTemplate, PtoRequest
from django.db.models import Q, F, Count, Sum, Max, Min, Avg, FloatField, IntegerField, Case, When, Value, CharField, OuterRef




class EmployeeTable (tables.Table):
    """
    Base Table for All Employees
    Displays basic details about each employee
    """

    name = tables.columns.LinkColumn('employee_detail', args=[A('name')])

    class Meta:
        model           = Employee
        fields          = ['name','shifts_trained', 'shifts_available']
        template_name   = 'django_tables2/bootstrap.html'

class ShiftListTable (tables.Table) :

    name = tables.columns.LinkColumn("shift", args=[A("name")])
    class Meta:
        model           = Shift
        fields          = ['name','start', 'end','duration', 'on_days_display']
        template_name   = 'django_tables2/bootstrap.html'
        
class ShiftsWorkdayTable (tables.Table):
    """
    Single Workday Table
    Displays all shifts for a single workday
    """

    class Meta:
        model           = Shift
        fields          = ['name','start','employee']
        template_name   = 'django_tables2/bootstrap.html'
    


class WorkdayListTable (tables.Table):

    date = tables.columns.LinkColumn("workday", args=[A("date")])
    n_unfilled = tables.columns.Column(verbose_name="Unfilled Shifts")
    days_away = tables.columns.Column(verbose_name="Days Away") 

    page_field = 'iperiod'

    class Meta:
        model           = Workday
        fields          = ['date', 'iweek', 'iperiod', 'iweekday', 'n_unfilled', 'days_away']
        template_name   = 'django_tables2/bootstrap.html'

    def render_n_unfilled(self, record):
        return record.n_unfilled

    def render_days_away(self, record):
        return record.daysAway
    
class PtoListTable (tables.Table):

    class Meta:
        model           = PtoRequest
        fields          = ['workday', 'status', 'stands_respected' ]
        template_name   = 'django_tables2/bootstrap.html'