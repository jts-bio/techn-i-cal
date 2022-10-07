from django.db.models import (Avg, Case, CharField, Count, F, FloatField,
                              IntegerField, Max, Min, OuterRef, Q, Sum, Value,
                              When)
from django_tables2 import tables
from django_tables2.utils import A

from .models import Employee, PtoRequest, Shift, ShiftTemplate, Slot, Workday, PtoRequest


class EmployeeTable (tables.Table):
    """
    Base Table for All Employees
    Displays basic details about each employee
    """
    name = tables.columns.LinkColumn('employee-detail', args=[A('name')])

    class Meta:
        model           = Employee
        fields          = ['name', 'fte', 'streak_pref']
        template_name   = 'django_tables2/bootstrap.html'

class ShiftListTable (tables.Table) :
    """
    Summary for ALL SHIFTS
    """
    name = tables.columns.LinkColumn("shift", args=[A("name")])
    hours = tables.columns.Column(verbose_name="Hours", attrs={"td": {"class": "small"}})
    
    class Meta:
        model           = Shift
        fields          = ['name','start','hours', 'on_days_display']
        template_name   = 'django_tables2/bootstrap.html'
        
class ShiftsWorkdayTable (tables.Table):
    """
    View from a WORKDAY
    display ALL SHIFTS for a given day
    """
    
    del_slot = tables.columns.LinkColumn("slot-delete", args=[A("date"),A("pk")], verbose_name="Delete", attrs={"td": {"class": "small"}})
    class Meta:
        model           = Shift
        fields          = ['name','start','employee','del_slot']
        template_name   = 'django_tables2/bootstrap.html'

    def render_del_slot(self, record):
        return record.pk

    # TODO --- add a column for "delete" slot

class ShiftsWorkdaySmallTable (tables.Table):

    class Meta:
        model           = Shift
        fields          = ['name','employee']
        template_name   = 'django_tables2/bootstrap.html'

class WorkdayListTable (tables.Table):
    """
    Summary for ALL WORKDAYS
    """

    date = tables.columns.LinkColumn("workday", args=[A("date")])
    n_unfilled = tables.columns.Column(verbose_name="Unfilled Shifts")
    days_away = tables.columns.Column(verbose_name="Days Away")  


    class Meta:
        model           = Workday
        fields          = [
                            'date', 'iweek', 'iperiod', 
                            'iweekday', 'n_unfilled', 'days_away',
                            'percFilled'
                           ]
        template_name   = 'django_tables2/bootstrap.html'

    def render_n_unfilled(self, record):
        return record.n_unfilled

    def render_days_away(self, record):
        return f"in {record.days_away} days"
    
    def render_iweek(self, record):
        return f"W-{record.iweek}"
    
    def render_iperiod(self, record):
        return f"P-{record.iperiod}"
    
    def render_iweekday(self, record):
        WEEKDAY_CHOICES = ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"]
        return WEEKDAY_CHOICES[record.iweekday]
    
    def render_date(self, record):
        return record.date.strftime("%d %b %Y")
    
    def render_percFilled(self, record):
        return f"{round(record.percFilled*100, 2)}%"
    
class PtoListTable (tables.Table):

    workday = tables.columns.LinkColumn("workday", args=[A("workday")])

    class Meta:
        model           = PtoRequest
        fields          = ['workday', 'status', 'stands_respected' ]
        template_name   = 'django_tables2/bootstrap.html'

class WeeklyHoursTable (tables.Table):

    name = tables.columns.LinkColumn("employee-detail", args=[A("name")])
    hours = tables.columns.Column(verbose_name="Weekly Hours")

    class Meta:
        model           = Employee
        fields          = ['name', 'hours']
        template_name   = 'django_tables2/bootstrap.html'

class PtoRequestTable (tables.Table):

    workday = tables.columns.LinkColumn("workday", args=[A("workday")])

    class Meta:
        model           = PtoRequest
        fields          = ['workday', 'status', 'stands_respected', 'employee', 'dateCreated', 'manager_approval' ]
        template_name   = 'django_tables2/bootstrap.html'
